from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone

# NOTE: This codec is stateless and does not guarantee one-time use.
# It relies on signature + TTL + rotating derived secrets only.

SIGNATURE_BYTES = 8


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(f"{data}{padding}")


def _sign(payload: bytes, secret: bytes) -> bytes:
    return hmac.new(secret, payload, hashlib.sha256).digest()[:SIGNATURE_BYTES]


def _daily_bucket(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y%m%d")


def _weekly_bucket(ts: int) -> str:
    return str(ts // (7 * 86400))


def _derive_secret(secret: str, *, purpose: str, exp: int) -> bytes:
    if purpose == "tg_register":
        bucket = _daily_bucket(exp)
    else:
        bucket = _weekly_bucket(exp)
    material = f"{secret}:{purpose}:{bucket}".encode("utf-8")
    return hashlib.sha256(material).digest()


@dataclass(frozen=True)
class TgShortcodePayload:
    tg_id: int
    purpose: str
    exp: int
    nonce: str
    request_id: str | None = None


class TgShortcodeCodec:
    @staticmethod
    def encode(payload: TgShortcodePayload, *, secret: str) -> str:
        payload_dict = {
            "tg_id": payload.tg_id,
            "purpose": payload.purpose,
            "exp": payload.exp,
            "nonce": payload.nonce,
        }
        if payload.request_id is not None:
            payload_dict["request_id"] = payload.request_id
        payload_bytes = json.dumps(payload_dict, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        derived_secret = _derive_secret(secret, purpose=payload.purpose, exp=payload.exp)
        signature = _sign(payload_bytes, derived_secret)
        return _b64encode(payload_bytes + signature)

    @staticmethod
    def decode(code: str, *, secret: str) -> TgShortcodePayload:
        raw = _b64decode(code)
        if len(raw) <= SIGNATURE_BYTES:
            raise ValueError("Invalid shortcode")
        payload_bytes = raw[:-SIGNATURE_BYTES]
        signature = raw[-SIGNATURE_BYTES:]
        payload = json.loads(payload_bytes)
        exp = int(payload["exp"])
        purpose = str(payload["purpose"])
        derived_secret = _derive_secret(secret, purpose=purpose, exp=exp)
        expected_signature = _sign(payload_bytes, derived_secret)
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid shortcode signature")
        return TgShortcodePayload(
            tg_id=int(payload["tg_id"]),
            purpose=purpose,
            exp=exp,
            nonce=str(payload["nonce"]),
            request_id=str(payload["request_id"]).strip() if payload.get("request_id") not in (None, "") else None,
        )

    @staticmethod
    def build(
        *,
        tg_id: int,
        purpose: str,
        ttl_seconds: int,
        request_id: str | None = None,
    ) -> TgShortcodePayload:
        exp = int(time.time()) + ttl_seconds
        return TgShortcodePayload(
            tg_id=tg_id,
            purpose=purpose,
            exp=exp,
            nonce=_b64encode(os.urandom(8)),
            request_id=request_id,
        )

    @staticmethod
    def ensure_valid(payload: TgShortcodePayload, *, now: int | None = None) -> None:
        current = now if now is not None else int(time.time())
        if payload.exp < current:
            raise ValueError("Shortcode expired")
