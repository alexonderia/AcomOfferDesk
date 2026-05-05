from __future__ import annotations

import anyio
from passlib.context import CryptContext

from app.core.session_tokens import create_access_token as create_session_access_token
from app.core.session_tokens import decode_access_token as decode_session_access_token

_password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def hash_password(password: str) -> str:
    return await anyio.to_thread.run_sync(_password_context.hash, password)


async def verify_password(password: str, password_hash: str) -> bool:
    return await anyio.to_thread.run_sync(_password_context.verify, password, password_hash)


async def create_access_token(subject: str, role_id: int) -> str:
    _ = role_id
    token, _ = await create_session_access_token(user_id=subject)
    return token


async def decode_access_token(token: str) -> dict[str, str | int]:
    claims = await decode_session_access_token(token)
    return {
        "sub": claims.subject,
        "type": "access",
        "scope": "session_access",
        "iat": claims.issued_at,
        "exp": claims.expires_at,
    }
