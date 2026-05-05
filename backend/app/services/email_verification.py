from __future__ import annotations

import smtplib
import time

from app.core.config import settings
from app.core.email_token import EmailVerificationClaims, EmailVerificationTokenCodec
from app.domain.exceptions import Conflict, Forbidden, NotFound
from app.infrastructure.email.email_templates.verification_email import build_verification_email_payload
from app.infrastructure.email.smtp_email_service import SMTPEmailService
from app.repositories.profiles import ProfileRepository
from app.services.tg_registration_links import build_keycloak_registration_link


class EmailVerificationService:
    _request_locks: dict[str, int] = {}

    def __init__(self, profiles: ProfileRepository) -> None:
        self._profiles = profiles
        self._token_codec = EmailVerificationTokenCodec(
            secret=settings.email_verification_secret,
            ttl_seconds=settings.email_verification_ttl_seconds,
        )
        self._email_service = SMTPEmailService(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            username=settings.email_address,
            password=settings.email_app_password,
            from_address=settings.email_address,
            from_name=settings.email_from_name,
        )

    async def request_profile_verification(self, *, user_id: str, email: str) -> str:
        normalized_email = email.strip()
        if not normalized_email:
            raise Conflict("Введите email для подтверждения")

        profile = await self._profiles.get_by_id(user_id)
        if profile is None:
            raise NotFound("Профиль пользователя не найден")

        current_email = (profile.mail or "").strip().lower()
        candidate_email = normalized_email.lower()
        if current_email == candidate_email and current_email not in {"", "не указано", "none", "null"}:
            return "same_email"

        if await self._profiles.exists_by_mail(email=normalized_email, exclude_user_id=user_id):
            raise Conflict("Эта электронная почта уже используется")

        lock_key = f"{user_id}:{candidate_email}"
        now_ts = int(time.time())
        lock_exp = self._request_locks.get(lock_key, 0)
        if lock_exp > now_ts:
            return "already_sent"
        
        token = await self._token_codec.create_profile_token(user_id=user_id, email=normalized_email)
        verification_link = self._build_frontend_verify_link(token=token)
        await self._send_verification_email(
            email=normalized_email,
            verification_link=verification_link,
            recipient_context={"user_login": user_id, "tg_id": None},
        )
        self._request_locks[lock_key] = now_ts + settings.email_verification_ttl_seconds
        return "sent"

    async def request_tg_registration_verification(self, *, tg_id: int, email: str, tg_token: str) -> None:
        normalized_email = email.strip()
        if await self._profiles.exists_by_mail(email=normalized_email):
            raise Conflict("Эта электронная почта уже используется")
        verification_link = build_keycloak_registration_link(token=tg_token)
        await self._send_verification_email(
            email=normalized_email,
            verification_link=verification_link,
            recipient_context=None,
        )

    async def confirm_profile_verification(self, *, token: str) -> bool:
        claims = await self._token_codec.parse_token(token)
        if claims.purpose != EmailVerificationTokenCodec.PURPOSE_PROFILE or not claims.user_id:
            raise Forbidden("Invalid verification flow")
        if await self._profiles.exists_by_mail(email=claims.email, exclude_user_id=claims.user_id):
            raise Conflict("Эта электронная почта уже используется")
        return await self._profiles.update_mail_after_verification(user_id=claims.user_id, email=claims.email)

    async def parse_claims(self, *, token: str) -> EmailVerificationClaims:
        return await self._token_codec.parse_token(token)

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
