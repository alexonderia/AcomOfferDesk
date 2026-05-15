from __future__ import annotations

import pytest
from starlette.websockets import WebSocketDisconnect

from app.api.dependencies import get_current_user
from app.domain.exceptions import Unauthorized


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
