from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(f"{data}{padding}")


def _sign(value: str, secret: str) -> str:
    signature = hmac.new(secret.encode(), value.encode(), hashlib.sha256).digest()
    return _b64encode(signature)


@dataclass(frozen=True)
class MaxLinkPayload:
    max_user_id: str
    purpose: str
    exp: int
    nonce: str
    request_id: str | None = None

    def to_token(self, secret: str) -> str:
        payload = {
            "max_user_id": self.max_user_id,
            "purpose": self.purpose,
            "exp": self.exp,
            "nonce": self.nonce,
        }
        if self.request_id is not None:
            payload["request_id"] = self.request_id
        payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        encoded_payload = _b64encode(payload_json.encode())
        signature = _sign(encoded_payload, secret)
        return f"{encoded_payload}.{signature}"


def decode_max_token(token: str, secret: str) -> MaxLinkPayload:
    try:
        encoded_payload, signature = token.split(".", 1)
    except ValueError as exc:
        raise ValueError("Invalid token format") from exc

    expected_signature = _sign(encoded_payload, secret)
    if not hmac.compare_digest(signature, expected_signature):
        raise ValueError("Invalid token signature")

    try:
        payload_bytes = _b64decode(encoded_payload)
        payload = json.loads(payload_bytes)
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid token payload") from exc

    try:
        return MaxLinkPayload(
            max_user_id=str(payload["max_user_id"]).strip(),
            purpose=str(payload["purpose"]),
            exp=int(payload["exp"]),
            nonce=str(payload["nonce"]),
            request_id=str(payload["request_id"]).strip() if payload.get("request_id") not in (None, "") else None,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Invalid token payload") from exc


def build_max_link_payload(
    *,
    max_user_id: str,
    purpose: str,
    ttl_seconds: int,
    request_id: str | None = None,
) -> MaxLinkPayload:
    exp = int(time.time()) + ttl_seconds
    return MaxLinkPayload(
        max_user_id=max_subject_value(max_user_id),
        purpose=purpose,
        exp=exp,
        nonce=uuid.uuid4().hex,
        request_id=request_id,
    )


def max_subject_value(max_user_id: int | str) -> str:
    return str(max_user_id).strip()
