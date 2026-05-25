from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from starlette.websockets import WebSocketDisconnect

from app.api.v1 import ws as ws_module
from app.api.dependencies import get_current_user
from app.domain.exceptions import Unauthorized
from app.realtime.manager import WebSocketConnectionManager
from app.services.ws_ticket_service import get_ws_ticket_service


def test_create_ws_ticket_requires_auth(test_client, api_app):
    async def _anonymous():
        raise Unauthorized("Missing credentials")

    api_app.dependency_overrides[get_current_user] = _anonymous
    response = test_client.post("/api/v1/ws/tickets", json={"purpose": "chat_ws"})

    assert response.status_code == 401


def test_create_ws_ticket_unknown_purpose_returns_400(test_client, set_current_user, make_current_user):
    set_current_user(make_current_user())

    response = test_client.post("/api/v1/ws/tickets", json={"purpose": "unknown"})

    assert response.status_code == 400


def test_create_ws_ticket_returns_ticket_payload(test_client, set_current_user, make_current_user):
    set_current_user(make_current_user())

    response = test_client.post("/api/v1/ws/tickets", json={"purpose": "chat_ws"})

    assert response.status_code == 200
    body = response.json()
    assert body["ticket"]
    assert body["expires_in"] >= 0
    assert body["expires_at"]


def test_chat_websocket_rejects_invalid_ticket(test_client):
    with pytest.raises(WebSocketDisconnect) as exc:
        with test_client.websocket_connect("/api/v1/ws/chat?ticket=invalid"):
            pass
    assert exc.value.code == 4401


def test_chat_websocket_rejects_wrong_purpose_ticket(test_client, set_current_user, make_current_user):
    set_current_user(make_current_user(user_id="user-1"))
    ticket_response = test_client.post("/api/v1/ws/tickets", json={"purpose": "realtime_ws"})
    ticket = ticket_response.json()["ticket"]

    with pytest.raises(WebSocketDisconnect) as exc:
        with test_client.websocket_connect(f"/api/v1/ws/chat?ticket={ticket}"):
            pass
    assert exc.value.code == 4401


def test_realtime_websocket_accepts_realtime_ticket(test_client, set_current_user, make_current_user):
    set_current_user(make_current_user(user_id="user-1"))
    ticket_response = test_client.post("/api/v1/ws/tickets", json={"purpose": "realtime_ws"})
    ticket = ticket_response.json()["ticket"]

    with test_client.websocket_connect(f"/api/v1/ws/realtime?ticket={ticket}") as websocket:
        envelope = websocket.receive_json()

    assert envelope["type"] == "connection.ready"
    assert envelope["data"]["user_id"] == "user-1"
    assert "notification.created" in envelope["data"]["supported_event_types"]
    assert "chat.message.created" in envelope["data"]["supported_event_types"]
    assert "chat.message.read" in envelope["data"]["supported_event_types"]
    assert "chat.typing.started" in envelope["data"]["supported_event_types"]


def test_realtime_websocket_accepts_chat_subscribe_commands(
    test_client,
    set_current_user,
    make_current_user,
    monkeypatch,
):
    class _FakeChatService:
        async def sync_chat(self, *, current_user, offer_id: int, last_known_message_id):
            _ = (current_user, last_known_message_id)
            return SimpleNamespace(
                chat_id=offer_id,
                last_message_id=321,
                last_read_message_id=300,
                last_read_at=None,
                is_muted=False,
                is_archived=False,
                resync_required=False,
            )

        async def mark_delivered_for_online_user(self, *, offer_id: int, user_id: str, up_to_message_id):
            _ = (offer_id, user_id, up_to_message_id)
            return SimpleNamespace(updated_message_ids=[])

    class _FakeChatRuntime:
        def __init__(self, manager: WebSocketConnectionManager) -> None:
            self.manager = manager
            self.service = _FakeChatService()

        async def send_to_connection(self, *, connection_id: str, event):
            await self.manager.send_to_connection(connection_id=connection_id, event=event)

        async def publish_chat_event(self, *, chat_id: int, event, exclude_user_ids=None):
            await self.manager.broadcast_to_chat(
                chat_id=chat_id,
                event=event,
                exclude_user_ids=exclude_user_ids,
            )

    class _FakeUnifiedRuntime:
        def __init__(self, manager: WebSocketConnectionManager) -> None:
            self.manager = manager

        async def connect(self, *, websocket, user_id: str) -> str:
            return await self.manager.connect(websocket=websocket, user_id=user_id)

        async def disconnect(self, *, connection_id: str) -> None:
            await self.manager.disconnect(connection_id=connection_id)

    shared_manager = WebSocketConnectionManager()
    fake_chat_runtime = _FakeChatRuntime(shared_manager)
    fake_unified_runtime = _FakeUnifiedRuntime(shared_manager)
    monkeypatch.setattr(ws_module, "get_chat_runtime", lambda: fake_chat_runtime)
    monkeypatch.setattr(ws_module, "get_unified_realtime_runtime", lambda: fake_unified_runtime)

    set_current_user(make_current_user(user_id="user-1"))
    ticket_response = test_client.post("/api/v1/ws/tickets", json={"purpose": "realtime_ws"})
    ticket = ticket_response.json()["ticket"]

    with test_client.websocket_connect(f"/api/v1/ws/realtime?ticket={ticket}") as websocket:
        websocket.receive_json()  # connection.ready
        websocket.send_json({"type": "chat.subscribe", "request_id": "req-1", "data": {"chat_id": 10}})
        first = websocket.receive_json()
        second = websocket.receive_json()

    payloads_by_type = {first["type"]: first, second["type"]: second}
    assert "ack" in payloads_by_type
    assert payloads_by_type["ack"]["request_id"] == "req-1"
    assert payloads_by_type["ack"]["data"]["event_type"] == "chat.subscribe"
    assert payloads_by_type["ack"]["data"]["chat_id"] == 10

    assert "chat.sync" in payloads_by_type
    assert payloads_by_type["chat.sync"]["request_id"] == "req-1"
    assert payloads_by_type["chat.sync"]["data"]["chat_id"] == 10


def test_realtime_websocket_rejects_chat_ticket(test_client, set_current_user, make_current_user):
    set_current_user(make_current_user(user_id="user-1"))
    ticket_response = test_client.post("/api/v1/ws/tickets", json={"purpose": "chat_ws"})
    ticket = ticket_response.json()["ticket"]

    with pytest.raises(WebSocketDisconnect) as exc:
        with test_client.websocket_connect(f"/api/v1/ws/realtime?ticket={ticket}"):
            pass
    assert exc.value.code == 4401


def test_realtime_websocket_rejects_used_ticket(test_client, set_current_user, make_current_user):
    set_current_user(make_current_user(user_id="user-1"))
    ticket_response = test_client.post("/api/v1/ws/tickets", json={"purpose": "realtime_ws"})
    ticket = ticket_response.json()["ticket"]

    with test_client.websocket_connect(f"/api/v1/ws/realtime?ticket={ticket}") as websocket:
        websocket.receive_json()

    with pytest.raises(WebSocketDisconnect) as exc:
        with test_client.websocket_connect(f"/api/v1/ws/realtime?ticket={ticket}"):
            pass
    assert exc.value.code == 4401


def test_realtime_websocket_rejects_expired_ticket(test_client, set_current_user, make_current_user):
    set_current_user(make_current_user(user_id="user-1"))
    ticket_response = test_client.post("/api/v1/ws/tickets", json={"purpose": "realtime_ws"})
    ticket = ticket_response.json()["ticket"]

    service = get_ws_ticket_service()
    ticket_hash = service._hash_ticket(ticket)  # noqa: SLF001
    service._store[ticket_hash].access.expires_at = datetime.now(UTC)  # noqa: SLF001

    with pytest.raises(WebSocketDisconnect) as exc:
        with test_client.websocket_connect(f"/api/v1/ws/realtime?ticket={ticket}"):
            pass
    assert exc.value.code == 4401
