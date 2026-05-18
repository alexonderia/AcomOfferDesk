from __future__ import annotations

import pytest

from app.infrastructure import notification_publisher as module
from shared.broker import RK_NOTIFICATION_PROCESS
from shared.process_notifications import build_process_notification_event


@pytest.mark.asyncio
async def test_publish_process_notification_event_uses_process_routing_key(monkeypatch):
    calls: list[tuple[str, dict]] = []

    async def _fake_publish_notification(event_type: str, payload: dict) -> None:
        calls.append((event_type, payload))

    monkeypatch.setattr(module, "publish_notification", _fake_publish_notification)
    event = build_process_notification_event(event_type="offer.created", offer_id=123, request_id=42)

    result = await module.publish_process_notification_event(event)

    assert result is True
    assert len(calls) == 1
    assert calls[0][0] == RK_NOTIFICATION_PROCESS
    assert calls[0][1]["event_type"] == "offer.created"


@pytest.mark.asyncio
async def test_publish_process_notification_event_retries_and_returns_false(monkeypatch):
    attempts = {"count": 0}

    async def _always_fail(event_type: str, payload: dict) -> None:
        _ = (event_type, payload)
        attempts["count"] += 1
        raise RuntimeError("boom")

    async def _no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(module, "publish_notification", _always_fail)
    monkeypatch.setattr(module.asyncio, "sleep", _no_sleep)

    event = build_process_notification_event(event_type="request.status_changed", request_id=1)
    result = await module.publish_process_notification_event(event)

    assert result is False
    assert attempts["count"] == 4
