import pytest
from starlette.websockets import WebSocketDisconnect

from app.api.dependencies import get_current_user
from app.domain.exceptions import Unauthorized


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


def test_realtime_websocket_fails_closed_during_iam_transition(test_client):
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with test_client.websocket_connect("/api/v1/ws/realtime?ticket=legacy-ticket"):
            pass

    assert exc_info.value.code == 4401
