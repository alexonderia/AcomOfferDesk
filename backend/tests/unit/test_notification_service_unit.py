from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.realtime.contracts import OutboundEnvelope
from app.services.notifications import NotificationService


class _Repo:
    def __init__(self) -> None:
        self.items = []
        self._seq = 0

    async def create(self, notification):
        self._seq += 1
        notification.id = self._seq
        notification.created_at = datetime.now(timezone.utc)
        self.items.append(notification)
        return notification


class _RealtimeSender:
    def __init__(self, *, delivered: bool = True, should_fail: bool = False) -> None:
        self.delivered = delivered
        self.should_fail = should_fail
        self.calls: list[tuple[str, OutboundEnvelope]] = []

    async def __call__(self, *, user_id: str, event: OutboundEnvelope) -> bool:
        self.calls.append((user_id, event))
        if self.should_fail:
            raise RuntimeError("ws send failed")
        return self.delivered


@pytest.mark.asyncio
async def test_notify_offer_created_skips_self_notification():
    repo = _Repo()
    sender = _RealtimeSender()
    service = NotificationService(repo, realtime_sender=sender)

    result = await service.notify_offer_created(
        actor_user_id="user-1",
        recipient_user_id="user-1",
        request_id=11,
        offer_id=77,
    )

    assert result is None
    assert repo.items == []
    assert sender.calls == []


@pytest.mark.asyncio
async def test_notify_offer_created_adds_actor_to_payload():
    repo = _Repo()
    sender = _RealtimeSender()
    service = NotificationService(repo, realtime_sender=sender)

    result = await service.notify_offer_created(
        actor_user_id="contractor-7",
        recipient_user_id="owner-3",
        request_id=11,
        offer_id=77,
    )

    assert result is not None
    assert result.type == "offer.created"
    assert result.payload == {
        "request_id": 11,
        "offer_id": 77,
        "actor_user_id": "contractor-7",
        "recipient_user_id": "owner-3",
    }
    assert len(sender.calls) == 1
    user_id, event = sender.calls[0]
    assert user_id == "owner-3"
    assert event.type == "notification.created"
    assert event.data["has_unread"] is True
    notification_payload = event.data["notification"]
    assert notification_payload["id"] == 1
    assert notification_payload["type"] == "offer.created"
    assert notification_payload["severity"] == "info"
    assert notification_payload["title"] == result.title
    assert notification_payload["body"] == result.body
    assert notification_payload["entity_type"] == "offer"
    assert notification_payload["entity_id"] == 77
    assert notification_payload["read_at"] is None
    assert "created_at" in notification_payload
    assert "user_id" not in notification_payload


@pytest.mark.asyncio
async def test_notify_message_created_excludes_author():
    repo = _Repo()
    sender = _RealtimeSender()
    service = NotificationService(repo, realtime_sender=sender)

    created = await service.notify_message_created(
        author_user_id="user-1",
        recipient_user_ids=["user-1", "user-2", "user-2"],
        request_id=99,
        offer_id=12,
        chat_id=12,
        message_id=45,
    )

    assert len(created) == 1
    assert created[0].user_id == "user-2"
    assert created[0].payload["author_user_id"] == "user-1"
    assert len(sender.calls) == 1
    assert sender.calls[0][0] == "user-2"


@pytest.mark.asyncio
async def test_notify_request_status_changed_uses_info_severity():
    repo = _Repo()
    sender = _RealtimeSender()
    service = NotificationService(repo, realtime_sender=sender)

    result = await service.notify_request_status_changed(
        actor_user_id="user-2",
        recipient_user_id="user-3",
        request_id=55,
        previous_status="open",
        new_status="review",
    )

    assert result is not None
    assert result.type == "request.status_changed"
    assert result.severity == "info"
    assert len(sender.calls) == 1


@pytest.mark.asyncio
async def test_create_for_user_keeps_flow_when_user_offline():
    repo = _Repo()
    sender = _RealtimeSender(delivered=False)
    service = NotificationService(repo, realtime_sender=sender)

    created = await service.create_for_user(
        user_id="user-offline",
        notification_type="system.warning",
        severity="warning",
        title="Offline user",
        body="Persist only",
    )

    assert created.id == 1
    assert len(repo.items) == 1
    assert len(sender.calls) == 1


@pytest.mark.asyncio
async def test_create_for_user_logs_and_keeps_flow_on_realtime_failure(caplog: pytest.LogCaptureFixture):
    repo = _Repo()
    sender = _RealtimeSender(should_fail=True)
    service = NotificationService(repo, realtime_sender=sender)

    with caplog.at_level("ERROR"):
        created = await service.create_for_user(
            user_id="user-1",
            notification_type="system.warning",
            severity="warning",
            title="Realtime failed",
            body="But DB row still created",
        )

    assert created.id == 1
    assert len(repo.items) == 1
    assert len(sender.calls) == 1
    assert "Failed to send realtime notification.created event" in caplog.text
