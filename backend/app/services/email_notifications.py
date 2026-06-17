from __future__ import annotations

from app.core.config import settings
from app.infrastructure.email_service import SMTPEmailService
from app.repositories.files import FileRepository
from app.repositories.profiles import ProfileRepository
from app.repositories.requests import RequestRepository
from app.services.normative_email_attachment import NormativeEmailAttachmentService
from app.services.send_request_notification_email import SendRequestNotificationEmailUseCase
from app.services.user_notification_preferences import UserNotificationPreferencesService


class EmailNotificationService:
    def __init__(
        self,
        profiles: ProfileRepository,
        requests: RequestRepository,
        files: FileRepository | None = None,
        *,
        notification_preferences: UserNotificationPreferencesService | None = None,
        after_commit_hook_registrar=None,
    ) -> None:
        self._profiles = profiles
        self._requests = requests
        self._files = files
        self._notification_preferences = notification_preferences
        self._after_commit_hook_registrar = after_commit_hook_registrar
        self._email_service = SMTPEmailService(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            username=settings.email_address,
            password=settings.email_app_password,
            from_address=settings.email_address,
            from_name=settings.email_from_name,
        )

    async def notify_new_request(
        self,
        *,
        request_id: str,
        additional_emails: list[str] | None = None,
        hidden_contractor_ids: list[str] | None = None,
    ) -> None:
        if not settings.web_base_url:
            return

        use_case = SendRequestNotificationEmailUseCase(
            request_repository=self._requests,
            profile_repository=self._profiles,
            email_service=self._email_service,
            app_url=settings.web_base_url,
            presentation_attachment_service=self._presentation_attachment_service(),
            notification_preferences=self._notification_preferences,
            after_commit_hook_registrar=self._after_commit_hook_registrar,
        )
        await use_case.execute(
            request_id=request_id,
            contractor_role_id=settings.contractor_role_id,
            additional_emails=additional_emails or [],
            hidden_contractor_ids=hidden_contractor_ids or [],
        )

    async def notify_request_to_additional_emails(
        self,
        *,
        request_id: str,
        additional_emails: list[str],
        initiator_user_id: str | None = None,
    ) -> None:
        if not settings.web_base_url:
            return

        use_case = SendRequestNotificationEmailUseCase(
            request_repository=self._requests,
            profile_repository=self._profiles,
            email_service=self._email_service,
            app_url=settings.web_base_url,
            presentation_attachment_service=self._presentation_attachment_service(),
            notification_preferences=self._notification_preferences,
            after_commit_hook_registrar=self._after_commit_hook_registrar,
        )
        await use_case.execute(
            request_id=request_id,
            contractor_role_id=settings.contractor_role_id,
            initiator_user_id=initiator_user_id,
            additional_emails=additional_emails,
            hidden_contractor_ids=[],
            include_verified_contractors=False,
        )

    def _presentation_attachment_service(self) -> NormativeEmailAttachmentService | None:
        if self._files is None:
            return None
        return NormativeEmailAttachmentService(self._files)
