from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.api.v1 import ws as ws_module
from app.domain.permissions import PermissionCodes
from app.services.ws_ticket_service import WsTicketAccessContext


class _FakeWsService:
    def __init__(self) -> None:
        self.expected_purpose: str | None = None

    async def consume_ticket(self, *, raw_ticket: str, expected_purpose: str) -> WsTicketAccessContext:
        _ = raw_ticket
        self.expected_purpose = expected_purpose
        return WsTicketAccessContext(
            user_id="contractor-1",
            role_id=3,
            status="active",
            keycloak_api_roles=frozenset(
                {
                    PermissionCodes.CHAT_MESSAGE_SEND,
                    PermissionCodes.CHAT_READ,
                    "app.contractor",
                }
            ),
            purpose="chat_ws",
            expires_at=datetime.now(UTC),
        )


class _FakeWebSocket:
    def __init__(self, ticket: str) -> None:
        self.query_params = {"ticket": ticket}


@pytest.mark.asyncio
async def test_ticket_auth_builds_current_user_from_ticket_keycloak_roles(monkeypatch):
    service = _FakeWsService()
    monkeypatch.setattr(ws_module, "get_ws_ticket_service", lambda: service)

    current_user, claims = await ws_module._get_current_user_from_websocket(_FakeWebSocket("ticket-1"))  # noqa: SLF001

    assert claims is None
    assert current_user.user_id == "contractor-1"
    assert PermissionCodes.CHAT_MESSAGE_SEND in current_user.permissions
    assert PermissionCodes.CHAT_READ in current_user.permissions
    assert service.expected_purpose == "chat_ws"


@pytest.mark.asyncio
async def test_ticket_auth_supports_realtime_ticket_purpose(monkeypatch):
    service = _FakeWsService()
    monkeypatch.setattr(ws_module, "get_ws_ticket_service", lambda: service)

    current_user, claims = await ws_module._get_current_user_from_websocket_with_purpose(  # noqa: SLF001
        _FakeWebSocket("ticket-2"),
        expected_purpose="realtime_ws",
    )

    assert claims is None
    assert current_user.user_id == "contractor-1"
    assert service.expected_purpose == "realtime_ws"
