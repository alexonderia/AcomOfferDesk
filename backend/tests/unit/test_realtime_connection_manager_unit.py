from __future__ import annotations

import pytest

from app.realtime.contracts import OutboundEnvelope
from app.realtime.manager import WebSocketConnectionManager


class _FailingWebSocket:
    async def accept(self) -> None:
        return None

    async def send_json(self, payload):
        _ = payload
        raise RuntimeError("socket closed")


@pytest.mark.asyncio
async def test_send_to_user_is_safe_for_disconnected_socket() -> None:
    manager = WebSocketConnectionManager()
    connection_id = await manager.connect(websocket=_FailingWebSocket(), user_id="user-1")

    delivered = await manager.send_to_user(
        user_id="user-1",
        event=OutboundEnvelope(type="system.toast", data={"message": "test"}),
    )

    assert delivered is False

    with pytest.raises(KeyError):
        await manager.send_to_connection(
            connection_id=connection_id,
            event=OutboundEnvelope(type="system.toast", data={"message": "test"}),
        )
