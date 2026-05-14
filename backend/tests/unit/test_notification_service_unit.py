from __future__ import annotations

import pytest

from app.services.notifications import NotificationService


class _Repo:
    def __init__(self) -> None:
        self.items = []

    async def create(self, notification):
        self.items.append(notification)
        return notification


@pytest.mark.asyncio
async def test_notify_offer_created_skips_self_notification():
    repo = _Repo()
    service = NotificationService(repo)

    result = await service.notify_offer_created(
        actor_user_id="user-1",
        recipient_user_id="user-1",
        request_id=11,
        offer_id=77,
    )

    assert result is None
    assert repo.items == []


@pytest.mark.asyncio
async def test_notify_offer_created_adds_actor_to_payload():
    repo = _Repo()
    service = NotificationService(repo)

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


@pytest.mark.asyncio
async def test_notify_message_created_excludes_author():
    repo = _Repo()
    service = NotificationService(repo)

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


@pytest.mark.asyncio
async def test_notify_request_status_changed_uses_info_severity():
    repo = _Repo()
    service = NotificationService(repo)

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

