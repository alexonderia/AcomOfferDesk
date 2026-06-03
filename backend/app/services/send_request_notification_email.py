from __future__ import annotations

import smtplib
from dataclasses import dataclass
from urllib.parse import quote

from app.core.config import settings
from app.core.registration_invite_tokens import RegistrationInviteTokenCodec
from app.domain.exceptions import NotFound
from app.infrastructure.email.email_attachment import EmailAttachment
from app.infrastructure.email.email_templates.email_contact_blocks import contact_info_from_invitation_settings
from app.infrastructure.email.email_templates.request_invited_contractor_email import (
    build_request_invited_contractor_email_payload,
)
from app.infrastructure.email.email_templates.request_notification_email import (
    build_request_notification_email_payload,
    build_request_registration_email_payload,
)
from app.infrastructure.email.reply_token_codec import ReplyTokenCodec
from app.infrastructure.email_service import SMTPEmailService
from app.repositories.profiles import ActiveContractorEmailRecipient, ProfileRepository
from app.repositories.requests import RequestRepository
from app.services.files import FileService
from app.services.normative_email_attachment import NormativeEmailAttachmentService

MAX_EMAIL_ATTACHMENT_SIZE_MB = 20


@dataclass(frozen=True, slots=True)
class NotificationRecipient:
    email: str
    user_login: str | None
    tg_id: int | None
    is_verified_user: bool
    has_economist_created_account: bool = False


class SendRequestNotificationEmailUseCase:
    def __init__(
        self,
        *,
        request_repository: RequestRepository,
        profile_repository: ProfileRepository,
        email_service: SMTPEmailService,
        app_url: str,
        file_service: FileService | None = None,
        presentation_attachment_service: NormativeEmailAttachmentService | None = None,
    ) -> None:
        self._request_repository = request_repository
        self._profile_repository = profile_repository
        self._email_service = email_service
        self._app_url = app_url.rstrip("/")
        self._file_service = file_service or FileService()
        self._presentation_attachment_service = presentation_attachment_service

    async def execute(
        self,
        *,
        request_id: str,
        contractor_role_id: int,
        initiator_user_id: str | None = None,
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
        recipients = await self._build_recipients(
            active_contractors=active_contractors,
            additional_emails=additional_emails or [],
            hidden_contractor_ids=hidden_contractor_ids or [],
            include_verified_contractors=include_verified_contractors,
            contractor_role_id=contractor_role_id,
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
        request_attachments, attachment_warning = await self._build_request_attachments(request_id=request_id)
        request_url = f"{self._app_url}/login?next={quote(f'/requests/{request_id}/contractor', safe='/')}"
        tg_bot_url = settings.tg_bot_public_url if settings.telegram_legacy_enabled else None
        registration_base_url = (settings.public_backend_base_url or self._app_url).rstrip("/")
        invitation_contact = contact_info_from_invitation_settings(
            contact_name=settings.invitation_contact_name,
            contact_email=settings.invitation_contact_email,
            contact_phone=settings.invitation_contact_phone,
        )
        portal_url = self._resolve_portal_url()

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
                attachments = request_attachments
            elif recipient.has_economist_created_account and portal_url:
                payload = build_request_invited_contractor_email_payload(
                    to_email=recipient.email,
                    request_id=request_id,
                    description=request.description,
                    deadline_at=request.deadline_at,
                    portal_url=portal_url,
                    contact=invitation_contact,
                    attachment_warning=attachment_warning,
                )
                attachments = await self._build_attachments_with_presentation(
                    request_attachments=request_attachments,
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
                    contact=invitation_contact,
                    attachment_warning=attachment_warning,
                )
                attachments = request_attachments

            try:
                # TODO(notification-center): worker-level SMTP delivery status is async.
                # To emit precise `email.sent` / `email.failed` center notifications,
                # add a feedback event from notifications_worker to backend service layer.
                await self._email_service.send_email(
                    to_email=payload.to_email,
                    subject=payload.subject,
                    text_content=payload.text_content,
                    html_content=payload.html_content,
                    attachments=attachments,
                    reply_token=payload.reply_token,
                    correlation_id=None,
                    recipient_user_id=initiator_user_id,
                    request_id=request_id,
                    offer_id=None,
                    initiator_user_id=initiator_user_id,
                    recipient_context={
                        "user_login": recipient.user_login,
                        "tg_id": recipient.tg_id,
                    }
                    if recipient.user_login is not None
                    else None,
                )
            except smtplib.SMTPException:
                continue

    async def _build_recipients(
        self,
        *,
        active_contractors: list[ActiveContractorEmailRecipient],
        additional_emails: list[str],
        hidden_contractor_ids: list[str],
        include_verified_contractors: bool,
        contractor_role_id: int,
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
            if normalized_email in recipient_emails:
                continue
            matched_verified_recipient = recipients_by_email.get(normalized_email)
            if matched_verified_recipient is not None:
                if matched_verified_recipient.email not in recipient_emails:
                    recipients.append(matched_verified_recipient)
                    recipient_emails.add(matched_verified_recipient.email)
                continue

            contractor_user_id = await self._profile_repository.find_contractor_user_id_by_notification_email(
                email=normalized_email,
                contractor_role_id=contractor_role_id,
            )
            recipients.append(
                NotificationRecipient(
                    email=normalized_email,
                    user_login=contractor_user_id,
                    tg_id=None,
                    is_verified_user=False,
                    has_economist_created_account=contractor_user_id is not None,
                )
            )
            recipient_emails.add(normalized_email)

        return recipients

    def _resolve_portal_url(self) -> str | None:
        if settings.invitation_portal_url:
            return settings.invitation_portal_url.rstrip("/")
        if settings.web_base_url:
            return f"{settings.web_base_url.rstrip('/')}/login"
        return f"{self._app_url}/login"

    async def _build_request_attachments(self, *, request_id: str) -> tuple[list[EmailAttachment], str | None]:
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

    async def _build_attachments_with_presentation(
        self,
        *,
        request_attachments: list[EmailAttachment],
        attachment_warning: str | None,
    ) -> list[EmailAttachment]:
        if self._presentation_attachment_service is None:
            return request_attachments

        presentation_attachment = await self._presentation_attachment_service.load_presentation_attachment()
        if presentation_attachment is None:
            return request_attachments

        combined = [presentation_attachment, *request_attachments]
        total_size_bytes = sum(len(item.content_bytes) for item in combined)
        max_total_size_bytes = MAX_EMAIL_ATTACHMENT_SIZE_MB * 1024 * 1024
        if total_size_bytes <= max_total_size_bytes:
            return combined

        presentation_only_size = len(presentation_attachment.content_bytes)
        if presentation_only_size <= max_total_size_bytes:
            return [presentation_attachment]

        return request_attachments
