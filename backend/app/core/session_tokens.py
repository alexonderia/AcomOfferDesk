from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac

from jose import JWTError, ExpiredSignatureError, jwt

from app.core.config import settings
from app.domain.exceptions import Unauthorized


@dataclass(frozen=True, slots=True)
class AccessTokenClaims:
    subject: str
    issued_at: int
    expires_at: int


@dataclass(frozen=True, slots=True)
class RefreshTokenClaims:
    subject: str
    issued_at: int
    expires_at: int
    max_expires_at: int
    fingerprint: str


def build_refresh_fingerprint(password_hash: str) -> str:
    return hmac.new(
        settings.resolved_refresh_token_secret.encode("utf-8"),
        password_hash.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _encode_access_payload(*, user_id: str, now: datetime) -> tuple[str, int]:
    expires_at = now + timedelta(seconds=settings.access_token_ttl_seconds)
    exp_ts = int(expires_at.timestamp())
    payload = {
        "sub": user_id,
        "type": "access",
        "scope": "session_access",
        "iat": int(now.timestamp()),
        "exp": exp_ts,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm), exp_ts


async def create_access_token(*, user_id: str) -> tuple[str, int]:
    now = datetime.now(timezone.utc)
    return _encode_access_payload(user_id=user_id, now=now)


async def decode_access_token(token: str) -> AccessTokenClaims:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except ExpiredSignatureError as exc:
        raise Unauthorized("Token expired") from exc
    except JWTError as exc:
        raise Unauthorized("Invalid token") from exc

    if payload.get("type") != "access" or payload.get("scope") != "session_access":
        raise Unauthorized("Invalid token payload")

    user_id = str(payload.get("sub") or "").strip()
    issued_at = payload.get("iat")
    expires_at = payload.get("exp")
    if not user_id or not isinstance(issued_at, int) or not isinstance(expires_at, int):
        raise Unauthorized("Invalid token payload")

    return AccessTokenClaims(subject=user_id, issued_at=issued_at, expires_at=expires_at)


async def create_refresh_token(
    *,
    user_id: str,
    password_hash: str,
    max_expires_at: int | None = None,
) -> tuple[str, int, int]:
    now = datetime.now(timezone.utc)
    now_ts = int(now.timestamp())
    max_exp_ts = max_expires_at or now_ts + settings.refresh_token_max_ttl_seconds
    exp_ts = min(now_ts + settings.refresh_token_idle_ttl_seconds, max_exp_ts)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "scope": "session_refresh",
        "iat": now_ts,
        "exp": exp_ts,
        "max_exp": max_exp_ts,
        "fp": build_refresh_fingerprint(password_hash),
    }
    token = jwt.encode(payload, settings.resolved_refresh_token_secret, algorithm=settings.jwt_algorithm)
    return token, exp_ts, max_exp_ts


async def decode_refresh_token(token: str) -> RefreshTokenClaims:
    try:
        payload = jwt.decode(token, settings.resolved_refresh_token_secret, algorithms=[settings.jwt_algorithm])
    except ExpiredSignatureError as exc:
        raise Unauthorized("Token expired") from exc
    except JWTError as exc:
        raise Unauthorized("Invalid token") from exc

    if payload.get("type") != "refresh" or payload.get("scope") != "session_refresh":
        raise Unauthorized("Invalid token payload")

    user_id = str(payload.get("sub") or "").strip()
    issued_at = payload.get("iat")
    expires_at = payload.get("exp")
    max_expires_at = payload.get("max_exp")
    fingerprint = str(payload.get("fp") or "").strip()
    if (
        not user_id
        or not isinstance(issued_at, int)
        or not isinstance(expires_at, int)
        or not isinstance(max_expires_at, int)
        or not fingerprint
    ):
        raise Unauthorized("Invalid token payload")

    now_ts = int(datetime.now(timezone.utc).timestamp())
    if max_expires_at < now_ts:
        raise Unauthorized("Token expired")
    if expires_at > max_expires_at:
        raise Unauthorized("Invalid token payload")

    return RefreshTokenClaims(
        subject=user_id,
        issued_at=issued_at,
        expires_at=expires_at,
        max_expires_at=max_expires_at,
        fingerprint=fingerprint,
    )
