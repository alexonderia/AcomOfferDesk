from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.domain.exceptions import Unauthorized
from app.services.ws_ticket_service import WsTicketService


@pytest.mark.asyncio
async def test_issue_ticket_creates_hash_only_store_record() -> None:
    service = WsTicketService(ttl_seconds=30)

    raw_ticket, _ = await service.issue_ticket(
        user_id="user-1",
        role_id=3,
        status="active",
        identity_roles=frozenset({"chat.read"}),
        purpose="realtime_ws",
    )

    assert raw_ticket
    assert raw_ticket not in service._store  # noqa: SLF001
    assert len(service._store) == 1  # noqa: SLF001


@pytest.mark.asyncio
async def test_consume_valid_ticket_returns_user_once() -> None:
    service = WsTicketService(ttl_seconds=30)
    raw_ticket, _ = await service.issue_ticket(
        user_id="user-1",
        role_id=3,
        status="active",
        identity_roles=frozenset({"chat.read"}),
        purpose="realtime_ws",
    )

    access = await service.consume_ticket(raw_ticket=raw_ticket, expected_purpose="realtime_ws")

    assert access.user_id == "user-1"
    assert access.role_id == 3
    assert access.status == "active"
    assert access.identity_roles == frozenset({"chat.read"})
    with pytest.raises(Unauthorized):
        await service.consume_ticket(raw_ticket=raw_ticket, expected_purpose="notifications_ws")


@pytest.mark.asyncio
async def test_consume_rejects_expired_ticket() -> None:
    service = WsTicketService(ttl_seconds=30)
    raw_ticket, _ = await service.issue_ticket(
        user_id="user-1",
        role_id=3,
        status="active",
        identity_roles=frozenset({"chat.read"}),
        purpose="realtime_ws",
    )
    await service.cleanup_expired()
    ticket_hash = service._hash_ticket(raw_ticket)  # noqa: SLF001
    service._store[ticket_hash].access.expires_at = datetime.now(UTC)  # noqa: SLF001

    with pytest.raises(Unauthorized):
        await service.consume_ticket(raw_ticket=raw_ticket, expected_purpose="notifications_ws")


@pytest.mark.asyncio
async def test_consume_rejects_wrong_purpose() -> None:
    service = WsTicketService(ttl_seconds=30)
    raw_ticket, _ = await service.issue_ticket(
        user_id="user-1",
        role_id=3,
        status="active",
        identity_roles=frozenset({"chat.read"}),
        purpose="realtime_ws",
    )

    with pytest.raises(Unauthorized):
        await service.consume_ticket(raw_ticket=raw_ticket, expected_purpose="notifications_ws")
