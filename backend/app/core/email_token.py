from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.domain.exceptions import Unauthorized


@dataclass(frozen=True)
class EmailVerificationClaims:
    purpose: str
    email: str
    exp: int
    user_id: str | None = None
    tg_id: int | None = None


class EmailVerificationTokenCodec:
    PURPOSE_PROFILE = "verify_email"
    PURPOSE_TG_REGISTER = "verify_email_tg_register"

    def __init__(self, secret: str, ttl_seconds: int) -> None:
        self._secret = secret.encode("utf-8")
        self._ttl_seconds = ttl_seconds

    async def create_profile_token(self, *, user_id: str, email: str) -> str:
        return self._encode(
            {
                "purpose": self.PURPOSE_PROFILE,
                "user_id": user_id,
                "email": email,
                "exp": self._build_exp(),
            }
        )

    async def create_tg_registration_token(self, *, tg_id: int, email: str) -> str:
        return self._encode(
            {
                "purpose": self.PURPOSE_TG_REGISTER,
                "tg_id": tg_id,
                "email": email,
                "exp": self._build_exp(),
            }
        )

    async def parse_token(self, token: str) -> EmailVerificationClaims:
        payload = self._decode(token)
        purpose = str(payload.get("purpose", "")).strip()
        email = str(payload.get("email", "")).strip()
        if purpose not in {self.PURPOSE_PROFILE, self.PURPOSE_TG_REGISTER} or not email:
            raise Unauthorized("Invalid verification token payload")

        user_id: str | None = None
        tg_id: int | None = None
        if purpose == self.PURPOSE_PROFILE:
            user_id = str(payload.get("user_id", "")).strip()
            if not user_id:
                raise Unauthorized("Invalid verification token payload")
        if purpose == self.PURPOSE_TG_REGISTER:
            try:
                tg_id = int(payload.get("tg_id"))
            except (TypeError, ValueError) as exc:
                raise Unauthorized("Invalid verification token payload") from exc

        exp = self._extract_exp(payload)
        return EmailVerificationClaims(purpose=purpose, email=email, exp=exp, user_id=user_id, tg_id=tg_id)

    def _build_exp(self) -> int:
        return int((datetime.now(timezone.utc) + timedelta(seconds=self._ttl_seconds)).timestamp())

    def _extract_exp(self, payload: dict[str, object]) -> int:
        try:
            exp = int(payload.get("exp", 0))
        except (TypeError, ValueError) as exc:
            raise Unauthorized("Invalid verification token payload") from exc
        if exp <= int(datetime.now(timezone.utc).timestamp()):
            raise Unauthorized("Verification token expired")
        return exp

    def _encode(self, payload: dict[str, object]) -> str:
        payload_part = self._b64_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signature_part = self._sign(payload_part)
        return f"{payload_part}.{signature_part}"

    def _decode(self, token: str) -> dict[str, object]:
        try:
            payload_part, signature_part = token.split(".", maxsplit=1)
        except ValueError as exc:
            raise Unauthorized("Invalid verification token") from exc

        expected_signature = self._sign(payload_part)
        if not hmac.compare_digest(signature_part, expected_signature):
            raise Unauthorized("Invalid verification token signature")

        try:
            return json.loads(self._b64_decode(payload_part).decode("utf-8"))
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise Unauthorized("Malformed verification token") from exc

    def _sign(self, value: str) -> str:
        digest = hmac.new(self._secret, value.encode("utf-8"), hashlib.sha256).digest()
        return self._b64_encode(digest)

    @staticmethod
    def _b64_encode(raw: bytes) -> str:
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("utf-8")

    @staticmethod
    def _b64_decode(value: str) -> bytes:
        padding = "=" * ((4 - len(value) % 4) % 4)
        return base64.urlsafe_b64decode(f"{value}{padding}".encode("utf-8"))
