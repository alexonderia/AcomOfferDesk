from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.email_token import EmailVerificationTokenCodec
from app.domain.exceptions import Unauthorized


INVITATION_PURPOSE = "registration_invite"


@dataclass(frozen=True, slots=True)
class RegistrationInviteClaims:
    purpose: str
    email: str
    role_id: int
    unit_id: int | None
    inviter_id: str
    nonce: str
    exp: int


class RegistrationInviteTokenCodec:
    def __init__(self, secret: str | None = None, ttl_seconds: int | None = None) -> None:
        self._ttl_seconds = ttl_seconds or settings.registration_invite_ttl_seconds
        self._codec = EmailVerificationTokenCodec(
            secret=secret or settings.email_verification_secret,
            ttl_seconds=self._ttl_seconds,
        )

    def issue(
        self,
        *,
        email: str,
        role_id: int,
        inviter_id: str,
        unit_id: int | None = None,
    ) -> str:
        return self._codec.encode_payload(
            {
                "purpose": INVITATION_PURPOSE,
                "email": email,
                "role_id": role_id,
                "unit_id": unit_id,
                "inviter_id": inviter_id,
                "nonce": secrets.token_urlsafe(16),
                "exp": int(
                    (
                        datetime.now(timezone.utc)
                        + timedelta(seconds=self._ttl_seconds)
                    ).timestamp()
                ),
            }
        )

    def parse(self, token: str) -> RegistrationInviteClaims:
        try:
            payload = self._codec.decode_payload(token)
        except Unauthorized as exc:
            detail = str(exc).lower()
            if "expired" in detail or "истёк" in str(exc):
                raise Unauthorized("Срок действия ссылки истёк") from exc
            raise Unauthorized("Ссылка регистрации недействительна") from exc
        purpose = str(payload.get("purpose", "")).strip()
        email = str(payload.get("email", "")).strip().lower()
        inviter_id = str(payload.get("inviter_id", "")).strip()
        nonce = str(payload.get("nonce", "")).strip()
        try:
            role_id = int(payload.get("role_id"))
            exp = int(payload.get("exp", 0))
        except (TypeError, ValueError) as exc:
            raise Unauthorized("Ссылка регистрации недействительна") from exc
        raw_unit = payload.get("unit_id")
        unit_id = int(raw_unit) if raw_unit not in {None, ""} else None
        if purpose != INVITATION_PURPOSE or not email or not inviter_id or not nonce:
            raise Unauthorized("Ссылка регистрации недействительна")
        if exp <= int(datetime.now(timezone.utc).timestamp()):
            raise Unauthorized("Срок действия ссылки истёк")
        return RegistrationInviteClaims(
            purpose=purpose,
            email=email,
            role_id=role_id,
            unit_id=unit_id,
            inviter_id=inviter_id,
            nonce=nonce,
            exp=exp,
        )
