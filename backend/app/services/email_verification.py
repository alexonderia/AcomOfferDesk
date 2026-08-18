from __future__ import annotations

from dataclasses import dataclass
import smtplib
import time
from urllib.parse import quote

from app.core.config import settings
from app.domain.exceptions import Conflict, NotFound, Unauthorized
from app.infrastructure.email.email_templates.verification_email import build_verification_email_payload
from app.infrastructure.email.smtp_email_service import SMTPEmailService
from app.infrastructure.iam_client import IamClient
from app.repositories.profiles import ProfileRepository
from app.repositories.user_auth_accounts import UserAuthAccountRepository
from app.repositories.user_contact_channels import UserContactChannelRepository


VERIFY_EMAIL_PURPOSE = "verify_email"
FIRST_ACCESS_PURPOSE = "first_access"
PROFILE_CHANGE_PURPOSE = "profile_change"
EMAIL_ACTION_PURPOSES = (VERIFY_EMAIL_PURPOSE, FIRST_ACCESS_PURPOSE, PROFILE_CHANGE_PURPOSE)


@dataclass(frozen=True, slots=True)
class EmailVerificationConfirmResult:
    updated: bool
    user_id: str
    email: str
    purpose: str
    next_action: str
    redirect_url: str | None = None


class EmailVerificationService:
    _request_locks: dict[str, int] = {}

    def __init__(
        self,
        profiles: ProfileRepository,
        user_contact_channels: UserContactChannelRepository | None = None,
        *,
        user_auth_accounts: UserAuthAccountRepository | None = None,
        iam_client: IamClient | None = None,
    ) -> None:
        self._profiles = profiles
        self._user_contact_channels = user_contact_channels
        self._user_auth_accounts = user_auth_accounts
        self._iam_client = iam_client or IamClient()
        self._email_service = SMTPEmailService(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            username=settings.email_address,
            password=settings.email_app_password,
            from_address=settings.email_address,
            from_name=settings.email_from_name,
        )

    async def request_profile_verification(
        self,
        *,
        user_id: str,
        email: str,
        purpose: str = VERIFY_EMAIL_PURPOSE,
        account_id: str | None = None,
    ) -> str:
        normalized_email = email.strip().lower()
        if not normalized_email:
            raise Conflict("Введите email для подтверждения")
        if purpose not in EMAIL_ACTION_PURPOSES:
            raise Conflict("Неизвестный сценарий подтверждения email")

        profile = await self._profiles.get_by_id(user_id)
        if profile is None:
            raise NotFound("Профиль пользователя не найден")

        if self._user_contact_channels is not None:
            channel = await self._user_contact_channels.get_primary_by_type(
                user_id=user_id,
                channel_type="email",
            )
            if (
                channel is not None
                and channel.is_verified
                and (channel.channel_value or "").strip().lower() == normalized_email
            ):
                return "same_email"
            if await self._user_contact_channels.exists_primary_email(
                email=normalized_email,
                exclude_user_id=user_id,
            ):
                raise Conflict("Эта электронная почта уже используется")

        if await self._profiles.exists_by_mail(email=normalized_email, exclude_user_id=user_id):
            raise Conflict("Эта электронная почта уже используется")

        resolved_account_id = account_id or await self._account_id_for_user(user_id)
        lock_key = f"{purpose}:{resolved_account_id}:{normalized_email}"
        now_ts = int(time.time())
        if self._request_locks.get(lock_key, 0) > now_ts:
            return "already_sent"

        if self._user_contact_channels is not None:
            await self._user_contact_channels.upsert_channel(
                user_id=user_id,
                channel_type="email",
                channel_value=normalized_email,
                is_verified=False,
                is_primary=True,
            )

        action = await self._iam_client.create_action_token(
            account_id=resolved_account_id,
            purpose=purpose,
            context={"email": normalized_email},
        )
        await self._send_verification_email(
            email=normalized_email,
            verification_link=self._build_frontend_verify_link(token=action.token),
            recipient_context={"user_login": user_id},
        )
        self._request_locks[lock_key] = now_ts + settings.email_verification_ttl_seconds
        return "sent"

    async def confirm_profile_verification(self, *, token: str) -> EmailVerificationConfirmResult:
        consumed = None
        matched_purpose = None
        last_error: Exception | None = None
        for purpose in EMAIL_ACTION_PURPOSES:
            try:
                consumed = await self._iam_client.consume_action_token(token=token, purpose=purpose)
                matched_purpose = purpose
                break
            except Unauthorized as exc:
                last_error = exc
        if consumed is None or matched_purpose is None:
            raise Unauthorized("Ссылка подтверждения недействительна") from last_error

        email = str((consumed.context or {}).get("email") or "").strip().lower()
        if not email:
            raise Unauthorized("Ссылка подтверждения недействительна")
        user_id = await self._user_id_for_account(str(consumed.account_id))
        if await self._profiles.exists_by_mail(email=email, exclude_user_id=user_id):
            raise Conflict("Эта электронная почта уже используется")
        if self._user_contact_channels is not None and await self._user_contact_channels.exists_primary_email(
            email=email,
            exclude_user_id=user_id,
        ):
            raise Conflict("Эта электронная почта уже используется")

        updated = await self._profiles.update_mail_after_verification(user_id=user_id, email=email)
        if self._user_contact_channels is not None:
            channel = await self._user_contact_channels.upsert_channel(
                user_id=user_id,
                channel_type="email",
                channel_value=email,
                is_verified=True,
                is_primary=True,
            )
            updated = updated or bool(channel and channel.is_verified)
        return EmailVerificationConfirmResult(
            updated=bool(updated),
            user_id=user_id,
            email=email,
            purpose=matched_purpose,
            next_action="login",
        )

    async def _account_id_for_user(self, user_id: str) -> str:
        if self._user_auth_accounts is None:
            raise Conflict("IAM binding is unavailable")
        binding = await self._user_auth_accounts.get_by_user_provider(
            user_id=user_id,
            provider="iam",
            include_inactive=True,
        )
        if binding is None:
            raise Conflict("IAM binding is unavailable")
        return binding.external_subject_id

    async def _user_id_for_account(self, account_id: str) -> str:
        if self._user_auth_accounts is None:
            raise Unauthorized("Ссылка подтверждения недействительна")
        binding = await self._user_auth_accounts.get_by_provider_subject(
            provider="iam",
            subject=account_id,
        )
        if binding is None:
            raise Unauthorized("Ссылка подтверждения недействительна")
        return binding.id_user

    async def _send_verification_email(
        self,
        *,
        email: str,
        verification_link: str,
        recipient_context: dict | None,
    ) -> None:
        payload = build_verification_email_payload(
            to_email=email,
            verification_link=verification_link,
            ttl_seconds=settings.email_verification_ttl_seconds,
            service_name=settings.email_from_name,
        )
        try:
            await self._email_service.send_email(
                payload.to_email,
                payload.subject,
                payload.text_content,
                payload.html_content,
                recipient_context=recipient_context,
            )
        except smtplib.SMTPException as exc:
            raise Conflict(f"Не удалось отправить письмо для подтверждения email: {exc}") from exc

    def _build_frontend_verify_link(self, *, token: str) -> str:
        if not settings.web_base_url:
            raise Conflict("WEB_BASE_URL не настроен")
        return f"{settings.web_base_url.rstrip('/')}/verify-email?token={quote(token, safe='')}"
