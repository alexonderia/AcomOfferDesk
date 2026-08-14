from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import anyio
from jose import JWTError, jwt
from passlib.context import CryptContext

from iam_app.core.config import settings


_password_context = CryptContext(schemes=["argon2"], deprecated="auto")
_dummy_password_hash = _password_context.hash(secrets.token_urlsafe(32))


def utc_now() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    """Normalize driver-returned timestamps (SQLite may drop tzinfo) to UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


async def hash_password(password: str) -> str:
    return await anyio.to_thread.run_sync(_password_context.hash, password)


async def verify_password(password: str, password_hash: str) -> bool:
    try:
        return await anyio.to_thread.run_sync(_password_context.verify, password, password_hash)
    except (TypeError, ValueError):
        return False


async def perform_dummy_password_check(password: str) -> None:
    await verify_password(password, _dummy_password_hash)


def random_token(bytes_length: int = 48) -> str:
    return secrets.token_urlsafe(bytes_length)


def hash_secret(raw_secret: str) -> str:
    return hmac.new(
        settings.token_hash_secret.encode("utf-8"),
        raw_secret.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def pkce_s256(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def encode_access_token(
    *,
    account_id: str,
    session_id: str,
    role: str,
    permissions: list[str],
) -> tuple[str, int]:
    now = datetime.now(UTC)
    expires_at = now + timedelta(seconds=settings.access_token_ttl_seconds)
    payload: dict[str, Any] = {
        "sub": account_id,
        "sid": session_id,
        "role": role,
        "permissions": sorted(set(permissions)),
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "iss": settings.issuer,
        "aud": settings.audience,
        "jti": random_token(18),
    }
    token = jwt.encode(
        payload,
        settings.signing_private_key,
        algorithm="RS256",
        headers={"kid": settings.signing_kid, "typ": "JWT"},
    )
    return token, int(expires_at.timestamp())


def encode_auth_request(payload: dict[str, Any]) -> str:
    now = datetime.now(UTC)
    claims = {
        **payload,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=10)).timestamp()),
        "type": "iam_auth_request",
    }
    return jwt.encode(claims, settings.auth_request_secret, algorithm="HS256")


def decode_auth_request(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.auth_request_secret, algorithms=["HS256"])
    except JWTError as exc:
        raise ValueError("invalid auth request") from exc
    if payload.get("type") != "iam_auth_request":
        raise ValueError("invalid auth request")
    return payload


def encode_browser_session(*, account_id: str, password_version: int) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": account_id,
        "password_version": password_version,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.browser_session_ttl_seconds)).timestamp()),
        "type": "iam_browser_session",
    }
    return jwt.encode(claims, settings.auth_request_secret, algorithm="HS256")


def decode_browser_session(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.auth_request_secret, algorithms=["HS256"])
    except JWTError as exc:
        raise ValueError("invalid browser session") from exc
    if payload.get("type") != "iam_browser_session":
        raise ValueError("invalid browser session")
    return payload


def constant_time_equal(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))
