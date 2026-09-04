from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from app.core.config import settings
from app.core.uow import UnitOfWork
from app.domain.auth_context import CurrentUser
from app.domain.authorization import require_permission
from app.domain.exceptions import Conflict, Forbidden
from app.domain.permissions import PermissionCodes
from app.infrastructure.email.email_templates.contractor_invitation_email import (
    build_contractor_invitation_email_payload,
)
from app.infrastructure.email.smtp_email_service import SMTPEmailService
from app.infrastructure.iam_client import IamClient
from app.services.registration_invitations import RegistrationInvitationService
from app.services.email_delivery_events import (
    BATCH_OPERATION_KIND_CONTRACTOR_INVITE,
    record_email_batch_operation_state,
)
from app.services.normative_email_attachment import NormativeEmailAttachmentService
from shared.email_delivery import generate_correlation_id

logger = logging.getLogger(__name__)

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_TOKEN_SPLIT_PATTERN = re.compile(r"[\s,]+")
_MAX_EMAIL_LENGTH = 254
_MAX_RAW_INPUT_LENGTH = 10000


@dataclass(frozen=True, slots=True)
class InviteFailure:
    email: str
    reason: str


@dataclass(frozen=True, slots=True)
class ContractorInviteResult:
    sent: list[str]
    failed: list[InviteFailure]
    invalid: list[str]


class ContractorInvitationService:
    def __init__(
        self,
        *,
        email_service: SMTPEmailService | None = None,
        attachment_service: NormativeEmailAttachmentService,
        invitation_service: RegistrationInvitationService | None = None,
        uow: UnitOfWork | None = None,
        iam_client: IamClient | None = None,
        after_commit_hook_registrar=None,
    ) -> None:
        self._email_service = email_service or SMTPEmailService(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            username=settings.email_address,
            password=settings.email_app_password,
            from_address=settings.email_address,
            from_name=settings.email_from_name,
        )
        self._attachment_service = attachment_service
        self._invitation_service = invitation_service
        self._uow = uow
        self._iam_client = iam_client or IamClient()
        self._after_commit_hook_registrar = after_commit_hook_registrar

    async def invite_contractors(
        self,
        *,
        current_user: CurrentUser,
        emails: list[str],
        normative_file_id: int,
    ) -> ContractorInviteResult:
        require_permission(
            current_user,
            PermissionCodes.USERS_REGISTRATION_INVITE,
            message="Недостаточно прав для отправки приглашений контрагентам",
        )
        if current_user.role_id == settings.contractor_role_id:
            raise Forbidden("Контрагент не может отправлять приглашения")

        normalized_valid, invalid = self._normalize_emails(emails)
        if len(normalized_valid) > settings.contractor_invite_max_emails_per_request:
            raise Conflict(
                "Превышено максимальное количество email для одного запроса: "
                f"{settings.contractor_invite_max_emails_per_request}"
            )

        if not normalized_valid:
            return ContractorInviteResult(sent=[], failed=[], invalid=invalid)

        presentation_attachment = await self._attachment_service.load_required_attachment(
            normative_file_id=normative_file_id,
        )
        failed: list[InviteFailure] = []
        sent: list[str] = []
        operation_id = generate_correlation_id()
        first_error_message: str | None = None

        for email in normalized_valid:
            registration_url = await self._registration_url(current_user=current_user, email=email)
            payload = build_contractor_invitation_email_payload(
                to_email=email,
                portal_url=registration_url,
                contact_name=settings.invitation_contact_name,
                contact_email=settings.invitation_contact_email,
                contact_phone=settings.invitation_contact_phone,
                contact_text=settings.invitation_contact_text,
            )
            try:
                await self._email_service.send_email(
                    to_email=payload.to_email,
                    subject=payload.subject,
                    text_content=payload.text_content,
                    html_content=payload.html_content,
                    attachments=[presentation_attachment],
                    recipient_user_id=current_user.user_id,
                    initiator_user_id=current_user.user_id,
                    operation_id=operation_id,
                    operation_kind=BATCH_OPERATION_KIND_CONTRACTOR_INVITE,
                    operation_expected_total=len(normalized_valid),
                )
                sent.append(email)
            except Exception as exc:
                logger.warning(
                    "Failed to queue contractor invitation email: email=%s error_type=%s",
                    _mask_email(email),
                    exc.__class__.__name__,
                )
                failed.append(
                    InviteFailure(
                        email=email,
                        reason="Не удалось поставить письмо в очередь на отправку",
                    )
                )
                if first_error_message is None:
                    first_error_message = "Не удалось поставить письмо в очередь на отправку"

        if self._after_commit_hook_registrar is not None and normalized_valid:
            self._after_commit_hook_registrar(
                lambda: record_email_batch_operation_state(
                    recipient_user_id=current_user.user_id,
                    operation_id=operation_id,
                    operation_kind=BATCH_OPERATION_KIND_CONTRACTOR_INVITE,
                    expected_total=len(normalized_valid),
                    immediate_failure_count=len(failed),
                    first_error_message=first_error_message,
                )
            )

        return ContractorInviteResult(
            sent=sent,
            failed=failed,
            invalid=invalid,
        )

    def _normalize_emails(self, emails: list[str]) -> tuple[list[str], list[str]]:
        if not emails:
            raise Conflict("Необходимо указать хотя бы один email")

        raw_buffer = "\n".join(emails)
        if len(raw_buffer) > _MAX_RAW_INPUT_LENGTH:
            raise Conflict("Список email слишком длинный")

        tokens: list[str] = []
        for chunk in emails:
            parts = _TOKEN_SPLIT_PATTERN.split(chunk or "")
            tokens.extend(parts)

        normalized_valid: list[str] = []
        invalid: list[str] = []
        seen_valid: set[str] = set()
        seen_invalid: set[str] = set()

        for token in tokens:
            candidate = (token or "").strip().lower()
            if not candidate:
                continue
            if len(candidate) > _MAX_EMAIL_LENGTH or not _EMAIL_PATTERN.fullmatch(candidate):
                if candidate not in seen_invalid:
                    seen_invalid.add(candidate)
                    invalid.append(candidate)
                continue
            if candidate in seen_valid:
                continue
            seen_valid.add(candidate)
            normalized_valid.append(candidate)

        if not normalized_valid and not invalid:
            raise Conflict("Необходимо указать хотя бы один email")

        return normalized_valid, invalid

    async def _registration_url(self, *, current_user: CurrentUser, email: str) -> str | None:
        if self._invitation_service is None:
            return self._resolve_portal_url()
        if self._uow is not None:
            existing_user_id = await self._invitation_service.resolve_existing_user_id(email)
            if existing_user_id is not None:
                binding = await self._uow.user_auth_accounts.get_by_user_provider(
                    user_id=existing_user_id,
                    provider="iam",
                )
                if binding is not None:
                    credential_state = await self._iam_client.get_credential_state(
                        account_id=binding.external_subject_id,
                    )
                    action = await self._iam_client.create_action_token(
                        account_id=binding.external_subject_id,
                        purpose="password_setup" if not credential_state.password_set else "password_reset",
                    )
                    from urllib.parse import quote

                    path = "setup" if not credential_state.password_set else "reset"
                    return f"{settings.iam_bff_auth_base_url}/password/{path}?token={quote(action.token, safe='')}"
        raw_token = self._invitation_service.create_contractor_invitation(
            current_user=current_user,
            email=email,
        )
        if settings.web_base_url:
            return f"{settings.web_base_url.rstrip('/')}/register?token={raw_token}"
        return f"/register?token={raw_token}"

    def _resolve_portal_url(self) -> str | None:
        if settings.invitation_portal_url:
            return settings.invitation_portal_url.rstrip("/")
        if settings.web_base_url:
            return f"{settings.web_base_url.rstrip('/')}/login"
        return None


def _mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    if not domain:
        return "***"
    if len(local) <= 1:
        return f"*@{domain}"
    return f"{local[0]}***@{domain}"
