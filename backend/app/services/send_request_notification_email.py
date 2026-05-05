from __future__ import annotations

import smtplib
from dataclasses import dataclass
from urllib.parse import quote

from app.core.config import settings
from app.core.registration_invite_tokens import RegistrationInviteTokenCodec
from app.domain.exceptions import NotFound
from app.infrastructure.email.email_attachment import EmailAttachment
from app.infrastructure.email.email_templates.request_notification_email import (
    build_request_notification_email_payload,
    build_request_registration_email_payload,
)
from app.infrastructure.email.reply_token_codec import ReplyTokenCodec
from app.infrastructure.email_service import SMTPEmailService
from app.repositories.profiles import ActiveContractorEmailRecipient, ProfileRepository
from app.repositories.requests import RequestRepository
from app.services.files import FileService

MAX_EMAIL_ATTACHMENT_SIZE_MB = 20


@dataclass(frozen=True, slots=True)
class NotificationRecipient:
    email: str
    user_login: str | None
    tg_id: int | None
    is_verified_user: bool


class SendRequestNotificationEmailUseCase:
    def __init__(
        self,
        *,
        request_repository: RequestRepository,
        profile_repository: ProfileRepository,
        email_service: SMTPEmailService,
        app_url: str,
        file_service: FileService | None = None,
    ) -> None:
        self._request_repository = request_repository
        self._profile_repository = profile_repository
        self._email_service = email_service
        self._app_url = app_url.rstrip("/")
        self._file_service = file_service or FileService()

    async def execute(
        self,
        *,
        request_id: int,
        contractor_role_id: int,
        additional_emails: list[str] | None = None,
        hidden_contractor_ids: list[str] | None = None,
        include_verified_contractors: bool = True,
    ) -> None:
        request = await self._request_repository.get_by_id(request_id=request_id)
        if request is None:
            return

        active_contractors = await self._profile_repository.list_active_contractor_email_recipients(
            contractor_role_id=contractor_role_id,
        )
        recipients = self._build_recipients(
            active_contractors=active_contractors,
            additional_emails=additional_emails or [],
            hidden_contractor_ids=hidden_contractor_ids or [],
            include_verified_contractors=include_verified_contractors,
        )
        if not recipients:
            return

        reply_secret = settings.reply_email_token_secret
        if not reply_secret and any(recipient.is_verified_user for recipient in recipients):
            return

        token_codec = ReplyTokenCodec(secret=reply_secret) if reply_secret else None
        invite_token_codec = RegistrationInviteTokenCodec(
            secret=settings.email_verification_secret,
            ttl_seconds=settings.tg_register_ttl_seconds,
        )
        attachments, attachment_warning = await self._build_attachments(request_id=request_id)
        request_url = f"{self._app_url}/login?next={quote(f'/requests/{request_id}/contractor', safe='/')}"
        tg_bot_url = settings.tg_bot_public_url if settings.telegram_legacy_enabled else None
        registration_base_url = (settings.public_backend_base_url or self._app_url).rstrip("/")

        for recipient in recipients:
            reply_token: str | None = None
            if token_codec is not None and recipient.user_login is not None:
                reply_token = await token_codec.create_token(
                    request_id=request_id,
                    user_id=recipient.user_login,
                    ttl_seconds=settings.reply_email_ttl_seconds,
                )

            if recipient.is_verified_user:
                payload = build_request_notification_email_payload(
                    to_email=recipient.email,
                    request_id=request_id,
                    description=request.description,
                    deadline_at=request.deadline_at,
                    request_url=request_url,
                    reply_token=reply_token,
                    attachment_warning=attachment_warning,
                )
            else:
                invite_token = invite_token_codec.create_token(email=recipient.email)
                registration_url = (
                    f"{registration_base_url}/api/v1/auth/oidc/register"
                    f"?invite_token={quote(invite_token, safe='')}&next_path={quote('/account', safe='/')}"
                )
                payload = build_request_registration_email_payload(
                    to_email=recipient.email,
                    request_id=request_id,
                    description=request.description,
                    deadline_at=request.deadline_at,
                    tg_bot_url=tg_bot_url,
                    registration_url=registration_url,
                    registration_ttl_seconds=settings.tg_register_ttl_seconds,
                    attachment_warning=attachment_warning,
                )

            try:
                await self._email_service.send_email(
                    to_email=payload.to_email,
                    subject=payload.subject,
                    text_content=payload.text_content,
                    html_content=payload.html_content,
                    attachments=attachments,
                    reply_token=payload.reply_token,
                    recipient_context={
                        "user_login": recipient.user_login,
                        "tg_id": recipient.tg_id,
                    }
                    if recipient.user_login is not None
                    else None,
                )
            except smtplib.SMTPException:
                continue

    def _build_recipients(
        self,
        *,
        active_contractors: list[ActiveContractorEmailRecipient],
        additional_emails: list[str],
        hidden_contractor_ids: list[str],
        include_verified_contractors: bool,
    ) -> list[NotificationRecipient]:
        recipients: list[NotificationRecipient] = []
        recipients_by_email: dict[str, NotificationRecipient] = {}
        recipient_emails: set[str] = set()
        hidden_contractor_id_set = set(hidden_contractor_ids)
        hidden_emails: set[str] = set()

        for contractor in active_contractors:
            normalized_email = contractor.email.strip().lower()
            if contractor.user_id in hidden_contractor_id_set:
                hidden_emails.add(normalized_email)
                continue
            recipient = NotificationRecipient(
                email=normalized_email,
                user_login=contractor.user_id,
                tg_id=contractor.tg_id,
                is_verified_user=True,
            )
            recipients_by_email[normalized_email] = recipient

        if include_verified_contractors:
            for email, recipient in recipients_by_email.items():
                recipients.append(recipient)
                recipient_emails.add(email)

        for email in additional_emails:
            normalized_email = email.strip().lower()
            if not normalized_email or normalized_email in hidden_emails:
                continue
            matched_verified_recipient = recipients_by_email.get(normalized_email)
            if matched_verified_recipient is not None:
                if matched_verified_recipient.email not in recipient_emails:
                    recipients.append(matched_verified_recipient)
                    recipient_emails.add(matched_verified_recipient.email)
                continue
            recipients.append(
                NotificationRecipient(
                    email=normalized_email,
                    user_login=None,
                    tg_id=None,
                    is_verified_user=False,
                )
            )
            recipient_emails.add(normalized_email)

        return recipients

    async def _build_attachments(self, *, request_id: int) -> tuple[list[EmailAttachment], str | None]:
        files = await self._request_repository.list_files_by_request_id(request_id=request_id)
        if not files:
            return [], None

        attachment_items: list[EmailAttachment] = []
        total_size_bytes = 0
        max_total_size_bytes = MAX_EMAIL_ATTACHMENT_SIZE_MB * 1024 * 1024

        for file in files:
            try:
                content_bytes = await self._file_service.read_bytes(db_file=file)
            except NotFound:
                continue
            except Exception:
                continue
            total_size_bytes += len(content_bytes)
            attachment_items.append(
                EmailAttachment(
                    filename=file.name,
                    content_bytes=content_bytes,
                    mime_type=file.mime_type,
                )
            )

        if total_size_bytes > max_total_size_bytes:
            return [], (
                f"Вложения не добавлены: суммарный размер превышает {MAX_EMAIL_ATTACHMENT_SIZE_MB} МБ."
            )

        return attachment_items, None
