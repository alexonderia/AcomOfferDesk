from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from starlette.websockets import WebSocketDisconnect

from app.api.dependencies import get_current_user
from app.api.v1 import ws as ws_module
from app.domain.exceptions import Unauthorized
from app.realtime.manager import WebSocketConnectionManager
from app.services.ws_ticket_service import get_ws_ticket_service


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

    async def mark_delivered_for_online_user(self, *, offer_id: int, user_id: str, up_to_message_id=None, message_ids=None):
        _ = (offer_id, user_id, up_to_message_id, message_ids)
        return SimpleNamespace(updated_message_ids=[])

    async def create_message(self, *, current_user, offer_id: int, text: str, file_refs):
        _ = (current_user, text, file_refs)
        return (
            SimpleNamespace(chat_id=offer_id, message_id=901),
            {
                "chat_id": offer_id,
                "message": {
                    "id": 901,
                    "user_id": current_user.user_id,
                    "text": text,
                },
            },
        )

    async def mark_read(self, *, current_user, offer_id: int, message_ids, up_to_message_id):
        _ = (current_user, message_ids, up_to_message_id)
        return SimpleNamespace(
            chat_id=offer_id,
            updated_count=1,
            updated_message_ids=[901],
            last_read_message_id=901,
        )


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


def _patch_fake_ws_runtimes(monkeypatch):
    shared_manager = WebSocketConnectionManager()
    fake_chat_runtime = _FakeChatRuntime(shared_manager)
    fake_unified_runtime = _FakeUnifiedRuntime(shared_manager)
    monkeypatch.setattr(ws_module, "get_chat_runtime", lambda: fake_chat_runtime)
    monkeypatch.setattr(ws_module, "get_unified_realtime_runtime", lambda: fake_unified_runtime)



def test_create_ws_ticket_requires_auth(test_client, api_app):
    async def _anonymous():
        raise Unauthorized("Missing credentials")

    api_app.dependency_overrides[get_current_user] = _anonymous
    response = test_client.post("/api/v1/ws/tickets", json={"purpose": "realtime_ws"})

    assert response.status_code == 401



def test_create_ws_ticket_unknown_purpose_returns_400(test_client, set_current_user, make_current_user):
    set_current_user(make_current_user())

    response = test_client.post("/api/v1/ws/tickets", json={"purpose": "unknown"})

    assert response.status_code == 400



def test_create_ws_ticket_rejects_removed_chat_purpose(test_client, set_current_user, make_current_user):
    set_current_user(make_current_user())

    response = test_client.post("/api/v1/ws/tickets", json={"purpose": "chat_ws"})

    assert response.status_code == 400



def test_create_ws_ticket_returns_ticket_payload(test_client, set_current_user, make_current_user):
    set_current_user(make_current_user())

    response = test_client.post("/api/v1/ws/tickets", json={"purpose": "realtime_ws"})

    assert response.status_code == 200
    body = response.json()
    assert body["ticket"]
    assert body["expires_in"] >= 0
    assert body["expires_at"]



def test_realtime_websocket_accepts_realtime_ticket(test_client, set_current_user, make_current_user):
    set_current_user(make_current_user(user_id="user-1"))
    ticket_response = test_client.post("/api/v1/ws/tickets", json={"purpose": "realtime_ws"})
    ticket = ticket_response.json()["ticket"]

    with test_client.websocket_connect(f"/api/v1/ws/realtime?ticket={ticket}") as websocket:
        envelope = websocket.receive_json()

    assert envelope["type"] == "connection.ready"
    assert envelope["data"]["user_id"] == "user-1"
    assert "ack" in envelope["data"]["supported_event_types"]
    assert "chat.unsubscribed" in envelope["data"]["supported_event_types"]
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
    _patch_fake_ws_runtimes(monkeypatch)

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



def test_realtime_websocket_emits_canonical_message_events(
    test_client,
    set_current_user,
    make_current_user,
    monkeypatch,
):
    _patch_fake_ws_runtimes(monkeypatch)
    async def _fake_get_user_full_name(_user_id: str) -> str:
        return "Пользователь"

    monkeypatch.setattr(ws_module, "_get_user_full_name", _fake_get_user_full_name)

    set_current_user(make_current_user(user_id="user-1"))
    ticket_response = test_client.post("/api/v1/ws/tickets", json={"purpose": "realtime_ws"})
    ticket = ticket_response.json()["ticket"]

    with test_client.websocket_connect(f"/api/v1/ws/realtime?ticket={ticket}") as websocket:
        websocket.receive_json()  # connection.ready

        websocket.send_json({"type": "chat.subscribe", "request_id": "sub-1", "data": {"chat_id": 10}})
        websocket.receive_json()  # ack
        websocket.receive_json()  # chat.sync

        websocket.send_json(
            {
                "type": "message.send",
                "request_id": "msg-1",
                "data": {"chat_id": 10, "text": "hello", "files": []},
            }
        )
        send_ack = websocket.receive_json()
        created_event = websocket.receive_json()

        websocket.send_json(
            {
                "type": "message.read",
                "request_id": "read-1",
                "data": {"chat_id": 10, "message_ids": [901]},
            }
        )
        read_ack = websocket.receive_json()
        read_event = websocket.receive_json()

    assert send_ack["type"] == "ack"
    assert send_ack["request_id"] == "msg-1"
    assert created_event["type"] == "chat.message.created"

    assert read_ack["type"] == "ack"
    assert read_ack["request_id"] == "read-1"
    assert read_event["type"] == "chat.message.read"



def test_realtime_websocket_emits_canonical_typing_events(
    test_client,
    set_current_user,
    make_current_user,
    monkeypatch,
):
    _patch_fake_ws_runtimes(monkeypatch)

    set_current_user(make_current_user(user_id="user-1"))
    user1_ticket = test_client.post("/api/v1/ws/tickets", json={"purpose": "realtime_ws"}).json()["ticket"]

    set_current_user(make_current_user(user_id="user-2"))
    user2_ticket = test_client.post("/api/v1/ws/tickets", json={"purpose": "realtime_ws"}).json()["ticket"]

    with (
        test_client.websocket_connect(f"/api/v1/ws/realtime?ticket={user1_ticket}") as user1_ws,
        test_client.websocket_connect(f"/api/v1/ws/realtime?ticket={user2_ticket}") as user2_ws,
    ):
        user1_ws.receive_json()  # connection.ready
        user2_ws.receive_json()  # connection.ready

        user1_ws.send_json({"type": "chat.subscribe", "request_id": "sub-1", "data": {"chat_id": 10}})
        user1_ws.receive_json()  # ack
        user1_ws.receive_json()  # chat.sync

        user2_ws.send_json({"type": "chat.subscribe", "request_id": "sub-2", "data": {"chat_id": 10}})
        user2_ws.receive_json()  # ack
        user2_ws.receive_json()  # chat.sync

        user1_ws.send_json({"type": "typing.start", "request_id": "typing-1", "data": {"chat_id": 10}})
        start_ack = user1_ws.receive_json()
        start_event = user2_ws.receive_json()

        user1_ws.send_json({"type": "typing.stop", "request_id": "typing-2", "data": {"chat_id": 10}})
        stop_ack = user1_ws.receive_json()
        stop_event = user2_ws.receive_json()

    assert start_ack["type"] == "ack"
    assert start_ack["request_id"] == "typing-1"
    assert start_event["type"] == "chat.typing.started"

    assert stop_ack["type"] == "ack"
    assert stop_ack["request_id"] == "typing-2"
    assert stop_event["type"] == "chat.typing.stopped"



def test_realtime_websocket_rejects_notifications_ticket(test_client, set_current_user, make_current_user):
    set_current_user(make_current_user(user_id="user-1"))
    ticket_response = test_client.post("/api/v1/ws/tickets", json={"purpose": "notifications_ws"})
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
