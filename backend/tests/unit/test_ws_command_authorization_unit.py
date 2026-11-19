from types import SimpleNamespace
from dataclasses import replace
import time
from unittest.mock import AsyncMock

import pytest
from fastapi import WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.api.v1.ws import _run_chat_event_loop
from app.api.v1 import ws as ws_api
from app.domain.exceptions import AuthenticationUnavailable, Forbidden, Unauthorized


@pytest.mark.asyncio
@pytest.mark.parametrize("event_type", ["message.send", "typing.start", "typing.stop"])
@pytest.mark.parametrize("failure", [Unauthorized, AuthenticationUnavailable])
async def test_revoked_or_unavailable_identity_cannot_send_websocket_commands(make_current_user, event_type, failure):
    socket = SimpleNamespace(
        client_state=WebSocketState.CONNECTED,
        receive_json=AsyncMock(side_effect=[
            {"type": event_type, "data": {"chat_id": 1, "text": "message"}},
            WebSocketDisconnect(),
        ]),
    )
    service = SimpleNamespace(
        refresh_current_user=AsyncMock(side_effect=failure()),
        create_message=AsyncMock(), ensure_can_type=AsyncMock(),
    )
    runtime = SimpleNamespace(
        service=service, send_to_connection=AsyncMock(), publish_chat_event=AsyncMock(),
    )
    await _run_chat_event_loop(websocket=socket, runtime=runtime, connection_id="connection", current_user=make_current_user())
    service.create_message.assert_not_awaited()
    service.ensure_can_type.assert_not_awaited()
    runtime.publish_chat_event.assert_not_awaited()
    assert runtime.send_to_connection.call_args.kwargs["event"].type == "error"


@pytest.mark.asyncio
@pytest.mark.parametrize("event_type", ["typing.start", "typing.stop"])
async def test_typing_cannot_be_injected_into_an_unauthorized_chat(make_current_user, event_type):
    actor = make_current_user()
    socket = SimpleNamespace(
        client_state=WebSocketState.CONNECTED,
        receive_json=AsyncMock(side_effect=[
            {"type": event_type, "data": {"chat_id": 999}}, WebSocketDisconnect(),
        ]),
    )
    runtime = SimpleNamespace(
        service=SimpleNamespace(
            refresh_current_user=AsyncMock(return_value=actor), ensure_can_type=AsyncMock(side_effect=Forbidden()),
        ),
        send_to_connection=AsyncMock(), publish_chat_event=AsyncMock(),
    )
    await _run_chat_event_loop(websocket=socket, runtime=runtime, connection_id="connection", current_user=actor)
    runtime.publish_chat_event.assert_not_awaited()
    assert runtime.send_to_connection.call_args.kwargs["event"].type == "error"


@pytest.mark.asyncio
async def test_websocket_lifetime_is_bounded_by_access_token(monkeypatch, make_current_user):
    actor = replace(make_current_user(), access_expires_at=int(time.time()) + 60)
    monkeypatch.setattr(ws_api, "_get_current_user_from_websocket_with_purpose", AsyncMock(return_value=actor))
    runtime = SimpleNamespace(
        connect=AsyncMock(return_value="connection"), disconnect=AsyncMock(),
        manager=SimpleNamespace(send_to_connection=AsyncMock()),
    )
    monkeypatch.setattr(ws_api, "get_unified_realtime_runtime", lambda: runtime)
    monkeypatch.setattr(ws_api, "get_chat_runtime", lambda: SimpleNamespace())

    async def expire(coroutine, *, timeout):
        coroutine.close()
        assert 0 < timeout <= 60
        raise TimeoutError

    monkeypatch.setattr(ws_api.asyncio, "wait_for", expire)
    socket = SimpleNamespace(close=AsyncMock())
    await ws_api.unified_realtime_websocket(socket)
    socket.close.assert_awaited_once_with(code=4401)
    runtime.disconnect.assert_awaited_once_with(connection_id="connection")
