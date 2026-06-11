from __future__ import annotations

import pytest

from app.core.config import settings
from app.services import max_notifications as module
from shared.broker import RK_MAX


@pytest.mark.asyncio
async def test_notify_registration_completed_publishes_to_max_queue(monkeypatch):
    calls: list[tuple[str, dict]] = []

    async def _fake_publish(routing_key: str, payload: dict) -> None:
        calls.append((routing_key, payload))

    monkeypatch.setattr(module, "publish_notification", _fake_publish)
    monkeypatch.setattr(settings, "max_bot_enabled", True)

    await module.notify_registration_completed("482403059838")

    assert len(calls) == 1
    assert calls[0][0] == RK_MAX
    assert calls[0][1]["user_id"] == "482403059838"
    assert "Регистрация пройдена" in calls[0][1]["text"]


@pytest.mark.asyncio
async def test_notify_skipped_when_max_bot_disabled(monkeypatch):
    calls: list[tuple[str, dict]] = []

    async def _fake_publish(routing_key: str, payload: dict) -> None:
        calls.append((routing_key, payload))

    monkeypatch.setattr(module, "publish_notification", _fake_publish)
    monkeypatch.setattr(settings, "max_bot_enabled", False)

    await module.notify_access_opened("482403059838")

    assert calls == []


@pytest.mark.asyncio
async def test_notify_new_request_sends_to_each_recipient(monkeypatch):
    calls: list[tuple[str, dict]] = []

    async def _fake_publish(routing_key: str, payload: dict) -> None:
        calls.append((routing_key, payload))

    monkeypatch.setattr(module, "publish_notification", _fake_publish)
    monkeypatch.setattr(settings, "max_bot_enabled", True)
    monkeypatch.setattr(settings, "public_backend_base_url", "https://example.com")

    from datetime import datetime, timezone

    await module.notify_new_request(
        max_user_ids=["111", "222"],
        request_id="REQ-1",
        description="Test request",
        deadline_at=datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc),
    )

    assert len(calls) == 2
    assert all(call[0] == RK_MAX for call in calls)
    user_ids = {call[1]["user_id"] for call in calls}
    assert user_ids == {"111", "222"}
    assert all("REQ-1" in call[1]["text"] for call in calls)
    assert all(call[1]["button_url"].startswith("https://example.com/login") for call in calls)
