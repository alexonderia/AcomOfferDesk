from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings
from app.domain.exceptions import Unauthorized


@dataclass(frozen=True, slots=True)
class ChatUploadClaims:
    file_id: int
    offer_id: int
    user_id: str


async def create_chat_upload_token(*, file_id: int, offer_id: int, user_id: str, ttl_minutes: int = 15) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
    payload = {
        "scope": "chat_upload",
        "file_id": file_id,
        "offer_id": offer_id,
        "sub": user_id,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


async def decode_chat_upload_token(token: str) -> ChatUploadClaims:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise Unauthorized("Invalid token") from exc

    if payload.get("scope") != "chat_upload":
        raise Unauthorized("Invalid token payload")

    file_id = payload.get("file_id")
    offer_id = payload.get("offer_id")
    user_id = payload.get("sub")
    if not isinstance(file_id, int) or not isinstance(offer_id, int) or not isinstance(user_id, str) or not user_id:
        raise Unauthorized("Invalid token payload")

    return ChatUploadClaims(file_id=file_id, offer_id=offer_id, user_id=user_id)
