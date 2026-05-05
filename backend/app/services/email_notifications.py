from __future__ import annotations

from app.core.config import settings
from app.infrastructure.email_service import SMTPEmailService
from app.repositories.profiles import ProfileRepository
from app.repositories.requests import RequestRepository
from app.services.send_request_notification_email import SendRequestNotificationEmailUseCase


class EmailNotificationService:
    def __init__(self, profiles: ProfileRepository, requests: RequestRepository) -> None:
        self._profiles = profiles
        self._requests = requests
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
        request_id: int,
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
        request_id: int,
        additional_emails: list[str],
    ) -> None:
        if not settings.web_base_url:
            return

        use_case = SendRequestNotificationEmailUseCase(
            request_repository=self._requests,
            profile_repository=self._profiles,
            email_service=self._email_service,
            app_url=settings.web_base_url,
        )
        await use_case.execute(
            request_id=request_id,
            contractor_role_id=settings.contractor_role_id,
            additional_emails=additional_emails,
            hidden_contractor_ids=[],
            include_verified_contractors=False,
        )
