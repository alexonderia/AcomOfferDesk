from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models.orm_models import UserNotification


def _dt(minutes: int) -> datetime:
    return datetime(2026, 5, 14, 9, 0, tzinfo=timezone.utc) + timedelta(minutes=minutes)


class _NotificationRepo:
    def __init__(self, notifications: list[UserNotification]) -> None:
        self._notifications = notifications

    async def create(self, notification: UserNotification) -> UserNotification:
        self._notifications.append(notification)
        return notification

    async def list_for_user(self, *, user_id: str, limit: int, offset: int) -> list[UserNotification]:
        items = [
            item
            for item in self._notifications
            if item.user_id == user_id
        ]
        items.sort(key=lambda item: (item.created_at, item.id), reverse=True)
        return items[offset : offset + limit]

    async def count_unread(self, *, user_id: str) -> int:
        return sum(1 for item in self._notifications if item.user_id == user_id and item.read_at is None)

    async def mark_as_read(self, *, user_id: str, notification_id: int) -> UserNotification | None:
        for item in self._notifications:
            if item.id == notification_id and item.user_id == user_id:
                if item.read_at is None:
                    item.read_at = _dt(120)
                return item
        return None

    async def mark_all_as_read(self, *, user_id: str) -> int:
        updated_count = 0
        for item in self._notifications:
            if item.user_id != user_id or item.read_at is not None:
                continue
            item.read_at = _dt(120)
            updated_count += 1
        return updated_count


class _NotificationUow:
    def __init__(self, repo: _NotificationRepo) -> None:
        self.notifications = repo

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)


def _notification(
    *,
    notification_id: int,
    user_id: str,
    read_at: datetime | None = None,
    created_at: datetime,
) -> UserNotification:
    return UserNotification(
        id=notification_id,
        user_id=user_id,
        type="message.created",
        severity="info",
        title="Новое сообщение",
        body="В чате появилось новое сообщение.",
        entity_type="message",
        entity_id=77,
        link_url="/offers/7/workspace",
        payload={"chat_id": 7},
        read_at=read_at,
        created_at=created_at,
    )


def test_list_notifications_returns_only_current_user_sorted(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    set_current_user(make_current_user(user_id="user-1"))
    repo = _NotificationRepo(
        [
            _notification(notification_id=1, user_id="user-1", created_at=_dt(1)),
            _notification(notification_id=2, user_id="user-2", created_at=_dt(2)),
            _notification(notification_id=3, user_id="user-1", created_at=_dt(3)),
        ]
    )
    set_uow(_NotificationUow(repo))

    response = test_client.get("/api/v1/notifications?limit=10&offset=0")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert [item["id"] for item in payload["items"]] == [3, 1]
    assert all(item["user_id"] == "user-1" for item in payload["items"])


def test_unread_count_returns_only_current_user(test_client, set_current_user, set_uow, make_current_user):
    set_current_user(make_current_user(user_id="user-1"))
    repo = _NotificationRepo(
        [
            _notification(notification_id=1, user_id="user-1", created_at=_dt(1), read_at=None),
            _notification(notification_id=2, user_id="user-1", created_at=_dt(2), read_at=_dt(4)),
            _notification(notification_id=3, user_id="user-2", created_at=_dt(3), read_at=None),
        ]
    )
    set_uow(_NotificationUow(repo))

    response = test_client.get("/api/v1/notifications/unread-count")

    assert response.status_code == 200
    assert response.json()["data"]["count"] == 1


def test_mark_notification_as_read(test_client, set_current_user, set_uow, make_current_user):
    set_current_user(make_current_user(user_id="user-1"))
    repo = _NotificationRepo(
        [
            _notification(notification_id=11, user_id="user-1", created_at=_dt(1), read_at=None),
        ]
    )
    set_uow(_NotificationUow(repo))

    response = test_client.patch("/api/v1/notifications/11/read")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["notification_id"] == 11
    assert payload["read_at"] is not None


def test_mark_all_notifications_as_read(test_client, set_current_user, set_uow, make_current_user):
    set_current_user(make_current_user(user_id="user-1"))
    repo = _NotificationRepo(
        [
            _notification(notification_id=1, user_id="user-1", created_at=_dt(1), read_at=None),
            _notification(notification_id=2, user_id="user-1", created_at=_dt(2), read_at=None),
            _notification(notification_id=3, user_id="user-1", created_at=_dt(3), read_at=_dt(4)),
            _notification(notification_id=4, user_id="user-2", created_at=_dt(5), read_at=None),
        ]
    )
    set_uow(_NotificationUow(repo))

    response = test_client.patch("/api/v1/notifications/read-all")

    assert response.status_code == 200
    assert response.json()["data"]["updated_count"] == 2


def test_mark_notification_from_another_user_returns_not_found(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    set_current_user(make_current_user(user_id="user-1"))
    repo = _NotificationRepo(
        [
            _notification(notification_id=55, user_id="user-2", created_at=_dt(1), read_at=None),
        ]
    )
    set_uow(_NotificationUow(repo))

    response = test_client.patch("/api/v1/notifications/55/read")

    assert response.status_code == 404
    assert response.json()["detail"] == "Notification not found"

