from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


class RegistrationInviteTokenInvalidError(ValueError):
    pass


class RegistrationInviteTokenExpiredError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RegistrationInviteClaims:
    email: str
    exp: int
    nonce: str


class RegistrationInviteTokenCodec:
    PURPOSE = "registration_invite"

    def __init__(self, *, secret: str, ttl_seconds: int) -> None:
        self._secret = secret.encode("utf-8")
        self._ttl_seconds = ttl_seconds

    def create_token(self, *, email: str) -> str:
        normalized_email = email.strip().lower()
        if not normalized_email:
            raise RegistrationInviteTokenInvalidError("Invite email must not be blank")
        payload = {
            "purpose": self.PURPOSE,
            "email": normalized_email,
            "nonce": secrets.token_urlsafe(12),
            "exp": self._build_exp(),
        }
        payload_part = self._b64_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signature_part = self._sign(payload_part)
        return f"{payload_part}.{signature_part}"

    def parse_token(self, token: str) -> RegistrationInviteClaims:
        try:
            payload_part, signature_part = token.split(".", maxsplit=1)
        except ValueError as exc:
            raise RegistrationInviteTokenInvalidError("Invalid invite token format") from exc

        expected_signature = self._sign(payload_part)
        if not hmac.compare_digest(signature_part, expected_signature):
            raise RegistrationInviteTokenInvalidError("Invalid invite token signature")

        try:
            payload = json.loads(self._b64_decode(payload_part).decode("utf-8"))
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise RegistrationInviteTokenInvalidError("Malformed invite token") from exc

        purpose = str(payload.get("purpose") or "").strip()
        email = str(payload.get("email") or "").strip().lower()
        nonce = str(payload.get("nonce") or "").strip()
        try:
            exp = int(payload.get("exp", 0))
        except (TypeError, ValueError) as exc:
            raise RegistrationInviteTokenInvalidError("Invalid invite token payload") from exc

        if purpose != self.PURPOSE or not email or not nonce:
            raise RegistrationInviteTokenInvalidError("Invalid invite token payload")
        if exp <= int(datetime.now(timezone.utc).timestamp()):
            raise RegistrationInviteTokenExpiredError("Invite token expired")

        return RegistrationInviteClaims(email=email, exp=exp, nonce=nonce)

    def _build_exp(self) -> int:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self._ttl_seconds)
        return int(expires_at.timestamp())

    def _sign(self, payload_part: str) -> str:
        digest = hmac.new(self._secret, payload_part.encode("utf-8"), hashlib.sha256).digest()
        return self._b64_encode(digest)

    @staticmethod
    def _b64_encode(raw: bytes) -> str:
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("utf-8")

    @staticmethod
    def _b64_decode(value: str) -> bytes:
        padding = "=" * ((4 - len(value) % 4) % 4)
        return base64.urlsafe_b64decode(f"{value}{padding}".encode("utf-8"))
