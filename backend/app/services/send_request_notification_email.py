from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

from app.core.config import settings
from app.domain.exceptions import NotFound
from app.infrastructure.email.email_attachment import EmailAttachment
from app.infrastructure.email.email_templates.email_contact_blocks import contact_info_from_invitation_settings
from app.infrastructure.email.email_templates.request_invited_contractor_email import (
    build_request_invited_contractor_email_payload,
)
from app.infrastructure.email.email_templates.request_notification_email import (
    build_request_notification_email_payload,
)
from app.infrastructure.email.reply_token_codec import ReplyTokenCodec
from app.infrastructure.email_service import SMTPEmailService
from app.repositories.profiles import ActiveContractorEmailRecipient, ProfileRepository
from app.repositories.requests import RequestRepository
from app.repositories.users import UserRepository
from app.services.contractor_units import ContractorUnitService
from app.services.email_delivery_events import (
    BATCH_OPERATION_KIND_REQUEST_ADDITIONAL,
    record_email_batch_operation_state,
)
from app.services.files import FileService
from app.services.normative_email_attachment import NormativeEmailAttachmentService
from app.services.user_notification_preferences import UserNotificationPreferencesService
from shared.email_delivery import generate_correlation_id

MAX_EMAIL_ATTACHMENT_SIZE_MB = 20
_GENERIC_QUEUE_ERROR_MESSAGE = "Не удалось поставить письмо в очередь на отправку."


@dataclass(frozen=True, slots=True)
class NotificationRecipient:
    email: str
    user_login: str | None
    is_verified_user: bool


@dataclass(frozen=True, slots=True)
class EmailBatchDispatchResult:
    operation_id: str | None
    expected_total: int
    immediate_failure_count: int
    first_error_message: str | None


class SendRequestNotificationEmailUseCase:
    def __init__(
        self,
        *,
        request_repository: RequestRepository,
        profile_repository: ProfileRepository,
        users: UserRepository,
        email_service: SMTPEmailService,
        app_url: str,
        file_service: FileService | None = None,
        presentation_attachment_service: NormativeEmailAttachmentService | None = None,
        notification_preferences: UserNotificationPreferencesService | None = None,
        after_commit_hook_registrar=None,
    ) -> None:
        self._request_repository = request_repository
        self._profile_repository = profile_repository
        self._users = users
        self._email_service = email_service
        self._app_url = app_url.rstrip("/")
        self._file_service = file_service or FileService()
        self._presentation_attachment_service = presentation_attachment_service
        self._notification_preferences = notification_preferences
        self._after_commit_hook_registrar = after_commit_hook_registrar

    async def execute(
        self,
        *,
        request_id: str,
        contractor_role_id: int,
        initiator_user_id: str | None = None,
        additional_emails: list[str] | None = None,
        hidden_contractor_ids: list[str] | None = None,
        include_verified_contractors: bool = True,
    ) -> EmailBatchDispatchResult:
        request = await self._request_repository.get_by_id(request_id=request_id)
        if request is None:
            return EmailBatchDispatchResult(
                operation_id=None,
                expected_total=0,
                immediate_failure_count=0,
                first_error_message=None,
            )

        active_contractors = await self._profile_repository.list_active_contractor_email_recipients(
            contractor_role_id=contractor_role_id,
        )
        recipients = await self._build_recipients(
            request_owner_user_id=request.id_user,
            active_contractors=active_contractors,
            additional_emails=additional_emails or [],
            hidden_contractor_ids=hidden_contractor_ids or [],
            include_verified_contractors=include_verified_contractors,
            contractor_role_id=contractor_role_id,
        )
        if not recipients:
            return EmailBatchDispatchResult(
                operation_id=None,
                expected_total=0,
                immediate_failure_count=0,
                first_error_message=None,
            )

        reply_secret = settings.reply_email_token_secret
        if not reply_secret and any(recipient.is_verified_user for recipient in recipients):
            return EmailBatchDispatchResult(
                operation_id=None,
                expected_total=0,
                immediate_failure_count=0,
                first_error_message=None,
            )

        token_codec = ReplyTokenCodec(secret=reply_secret) if reply_secret else None
        request_attachments, attachment_warning = await self._build_request_attachments(request_id=request_id)
        request_url = f"{self._app_url}/login?next={quote(f'/requests/{request_id}/contractor', safe='/')}"
        invitation_contact = contact_info_from_invitation_settings(
            contact_name=settings.invitation_contact_name,
            contact_email=settings.invitation_contact_email,
            contact_phone=settings.invitation_contact_phone,
        )
        portal_url = self._resolve_portal_url()
        operation_id = generate_correlation_id() if initiator_user_id else None
        immediate_failure_count = 0
        first_error_message: str | None = None

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
            else:
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
            try:
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
                    operation_id=operation_id,
                    operation_kind=BATCH_OPERATION_KIND_REQUEST_ADDITIONAL if operation_id else None,
                    operation_expected_total=len(recipients) if operation_id else None,
                    recipient_context={
                        "user_login": recipient.user_login,
                    }
                    if recipient.user_login is not None
                    else None,
                )
            except Exception:
                immediate_failure_count += 1
                if first_error_message is None:
                    first_error_message = _GENERIC_QUEUE_ERROR_MESSAGE
                continue

        if operation_id and self._after_commit_hook_registrar is not None:
            self._after_commit_hook_registrar(
                lambda: record_email_batch_operation_state(
                    recipient_user_id=initiator_user_id or "",
                    operation_id=operation_id,
                    operation_kind=BATCH_OPERATION_KIND_REQUEST_ADDITIONAL,
                    expected_total=len(recipients),
                    request_id=str(request_id),
                    immediate_failure_count=immediate_failure_count,
                    first_error_message=first_error_message,
                )
            )

        return EmailBatchDispatchResult(
            operation_id=operation_id,
            expected_total=len(recipients),
            immediate_failure_count=immediate_failure_count,
            first_error_message=first_error_message,
        )

    async def _build_recipients(
        self,
        *,
        request_owner_user_id: str,
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
        normalized_additional_emails = [
            email.strip().lower()
            for email in additional_emails
            if email.strip()
        ]
        additional_email_to_user_id: dict[str, str | None] = {}
        for email in normalized_additional_emails:
            if email in additional_email_to_user_id:
                continue
            additional_email_to_user_id[email] = await self._profile_repository.find_contractor_user_id_by_notification_email(
                email=email,
                contractor_role_id=contractor_role_id,
            )
        visible_contractor_user_ids = set(
            await ContractorUnitService(users=self._users).filter_contractor_user_ids_for_request_owner(
                contractor_user_ids=list({
                    contractor.user_id for contractor in active_contractors
                } | {
                    contractor_user_id
                    for contractor_user_id in additional_email_to_user_id.values()
                    if contractor_user_id is not None
                }),
                request_owner_user_id=request_owner_user_id,
            )
        )

        for contractor in active_contractors:
            normalized_email = contractor.email.strip().lower()
            if contractor.user_id in hidden_contractor_id_set:
                hidden_emails.add(normalized_email)
                continue
            if contractor.user_id not in visible_contractor_user_ids:
                hidden_emails.add(normalized_email)
                continue
            if self._notification_preferences is not None:
                is_enabled = await self._notification_preferences.is_channel_enabled(
                    user_id=contractor.user_id,
                    channel_type="email",
                    notification_type="request",
                )
                if not is_enabled:
                    hidden_emails.add(normalized_email)
                    continue
            recipient = NotificationRecipient(
                email=normalized_email,
                user_login=contractor.user_id,
                is_verified_user=True,
            )
            recipients_by_email[normalized_email] = recipient

        if include_verified_contractors:
            for email, recipient in recipients_by_email.items():
                recipients.append(recipient)
                recipient_emails.add(email)

        for normalized_email in normalized_additional_emails:
            if normalized_email in hidden_emails:
                continue
            if normalized_email in recipient_emails:
                continue
            matched_verified_recipient = recipients_by_email.get(normalized_email)
            if matched_verified_recipient is not None:
                if matched_verified_recipient.email not in recipient_emails:
                    recipients.append(matched_verified_recipient)
                    recipient_emails.add(matched_verified_recipient.email)
                continue
            contractor_user_id = additional_email_to_user_id.get(normalized_email)
            if contractor_user_id is not None and contractor_user_id not in visible_contractor_user_ids:
                continue
            recipients.append(
                NotificationRecipient(
                    email=normalized_email,
                    user_login=contractor_user_id,
                    is_verified_user=False,
                )
            )
            recipient_emails.add(normalized_email)

        return recipients

    def _resolve_portal_url(self) -> str:
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
