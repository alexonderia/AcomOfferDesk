from __future__ import annotations

import asyncio
import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from app.core.config import settings
from app.domain.exceptions import Unauthorized

WsTicketPurpose = Literal["chat_ws", "realtime_ws", "notifications_ws"]


@dataclass(slots=True)
class _StoredTicket:
    user_id: str
    purpose: WsTicketPurpose
    expires_at: datetime
    used_at: datetime | None = None


class WsTicketService:
    def __init__(self, *, ttl_seconds: int | None = None) -> None:
        self._ttl_seconds = ttl_seconds or settings.ws_ticket_ttl_seconds
        self._store: dict[str, _StoredTicket] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def _hash_ticket(raw_ticket: str) -> str:
        return hashlib.sha256(raw_ticket.encode("utf-8")).hexdigest()

    async def issue_ticket(self, *, user_id: str, purpose: WsTicketPurpose) -> tuple[str, datetime]:
        await self.cleanup_expired()
        raw_ticket = secrets.token_urlsafe(48)
        expires_at = datetime.now(UTC) + timedelta(seconds=self._ttl_seconds)
        record = _StoredTicket(user_id=user_id, purpose=purpose, expires_at=expires_at)
        ticket_hash = self._hash_ticket(raw_ticket)
        async with self._lock:
            self._store[ticket_hash] = record
        return raw_ticket, expires_at

    async def consume_ticket(self, *, raw_ticket: str, expected_purpose: WsTicketPurpose) -> str:
        if not raw_ticket.strip():
            raise Unauthorized("Invalid websocket ticket")
        ticket_hash = self._hash_ticket(raw_ticket.strip())
        now = datetime.now(UTC)
        async with self._lock:
            record = self._store.get(ticket_hash)
            if record is None:
                raise Unauthorized("Invalid websocket ticket")
            if record.used_at is not None:
                self._store.pop(ticket_hash, None)
                raise Unauthorized("Invalid websocket ticket")
            if record.expires_at <= now:
                self._store.pop(ticket_hash, None)
                raise Unauthorized("Websocket ticket expired")
            if record.purpose != expected_purpose:
                raise Unauthorized("Invalid websocket ticket purpose")
            record.used_at = now
            self._store.pop(ticket_hash, None)
            return record.user_id

    async def cleanup_expired(self) -> None:
        now = datetime.now(UTC)
        async with self._lock:
            expired = [
                ticket_hash
                for ticket_hash, record in self._store.items()
                if record.expires_at <= now or record.used_at is not None
            ]
            for ticket_hash in expired:
                self._store.pop(ticket_hash, None)


_ws_ticket_service = WsTicketService()


def get_ws_ticket_service() -> WsTicketService:
    return _ws_ticket_service
