from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.services import process_notification_events as module
from shared.process_notifications import build_process_notification_event


class _FakeNotificationsRepo:
    def __init__(self) -> None:
        self.created = []
        self._dedupe: set[tuple[str, str, str, str]] = set()
        self._seq = 0

    async def create(self, notification):
        self._seq += 1
        notification.id = self._seq
        notification.created_at = datetime.now(timezone.utc)
        self.created.append(notification)
        payload = notification.payload or {}
        event_id = str(payload.get("event_id") or "")
        dedupe_key = str(payload.get("dedupe_key") or "")
        if event_id:
            self._dedupe.add((notification.user_id, notification.type, "event_id", event_id))
        if dedupe_key:
            self._dedupe.add((notification.user_id, notification.type, "dedupe_key", dedupe_key))
        return notification

    async def exists_by_type_user_and_payload_key(
        self,
        *,
        user_id: str,
        notification_type: str,
        key_name: str,
        key_value: str,
    ) -> bool:
        return (user_id, notification_type, key_name, key_value) in self._dedupe


class _FakeRequestsRepo:
    def __init__(self, *, owner_id: str = "owner-1") -> None:
        self._owner_id = owner_id

    async def get_by_id(self, *, request_id: int):
        return SimpleNamespace(id=request_id, id_user=self._owner_id)


class _FakeChatsRepo:
    def __init__(self, recipients: list[str] | None = None) -> None:
        self._recipients = recipients or []

    async def list_active_participant_user_ids(self, *, chat_id: int) -> list[str]:
        _ = chat_id
        return list(self._recipients)


class _FakeUow:
    def __init__(self, repo: _FakeNotificationsRepo, *, owner_id: str = "owner-1", chat_recipients: list[str] | None = None) -> None:
        self.notifications = repo
        self.requests = _FakeRequestsRepo(owner_id=owner_id)
        self.chats = _FakeChatsRepo(chat_recipients)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        _ = (exc_type, exc, tb)


class _FakeRealtimeRuntime:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    async def send_to_user(self, *, user_id: str, event) -> bool:
        self.calls.append((user_id, event))
        return True


@pytest.mark.asyncio
async def test_handler_offer_created_creates_notification_for_owner(monkeypatch):
    repo = _FakeNotificationsRepo()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo, owner_id="owner-2"))
    handler = module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type="offer.created",
        actor_user_id="contractor-1",
        request_id=10,
        offer_id=100,
        dedupe_key="offer.created:100",
    )
    await handler.handle(payload=event.to_payload())

    assert len(repo.created) == 1
    assert repo.created[0].user_id == "owner-2"
    assert repo.created[0].type == "offer.created"


@pytest.mark.asyncio
async def test_handler_message_created_excludes_actor(monkeypatch):
    repo = _FakeNotificationsRepo()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo, chat_recipients=["user-1", "user-2", "user-3"]))
    handler = module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type="message.created",
        actor_user_id="user-1",
        request_id=11,
        offer_id=12,
        chat_id=12,
        message_id=77,
        dedupe_key="message.created:77",
    )
    await handler.handle(payload=event.to_payload())

    assert sorted(item.user_id for item in repo.created) == ["user-2", "user-3"]


@pytest.mark.asyncio
async def test_handler_request_status_changed_excludes_actor(monkeypatch):
    repo = _FakeNotificationsRepo()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo, owner_id="owner-1"))
    handler = module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type="request.status_changed",
        actor_user_id="owner-1",
        request_id=55,
        dedupe_key="request.status_changed:55:review",
        payload={"old_status": "open", "new_status": "review"},
    )
    await handler.handle(payload=event.to_payload())

    assert repo.created == []


@pytest.mark.asyncio
async def test_handler_dedupe_skips_duplicate_event(monkeypatch):
    repo = _FakeNotificationsRepo()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo, owner_id="owner-2"))
    handler = module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type="offer.created",
        actor_user_id="contractor-1",
        request_id=10,
        offer_id=100,
        dedupe_key="offer.created:100",
    )
    payload = event.to_payload()
    await handler.handle(payload=payload)
    await handler.handle(payload=payload)

    assert len(repo.created) == 1


@pytest.mark.asyncio
async def test_handler_ignores_invalid_event_payload(monkeypatch):
    repo = _FakeNotificationsRepo()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo))
    handler = module.ProcessNotificationEventHandler()

    await handler.handle(payload={"event_type": "offer.created"})

    assert repo.created == []


@pytest.mark.asyncio
async def test_handler_offer_created_sends_realtime_created_event(monkeypatch):
    repo = _FakeNotificationsRepo()
    runtime = _FakeRealtimeRuntime()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo, owner_id="owner-2"))
    monkeypatch.setattr("app.realtime.runtime.get_unified_realtime_runtime", lambda: runtime)
    handler = module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type="offer.created",
        actor_user_id="contractor-1",
        request_id=10,
        offer_id=100,
        dedupe_key="offer.created:100",
    )
    await handler.handle(payload=event.to_payload())

    assert len(runtime.calls) == 1
    user_id, envelope = runtime.calls[0]
    assert user_id == "owner-2"
    assert envelope.type == "notification.created"
    assert envelope.data["has_unread"] is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("event_type", "expected_title"),
    (
        ("offer.accepted", "Коммерческое предложение принято"),
        ("offer.rejected", "Коммерческое предложение отклонено"),
        ("offer.deleted", "Коммерческое предложение удалено"),
    ),
)
async def test_handler_offer_status_events_create_notifications(monkeypatch, event_type: str, expected_title: str):
    repo = _FakeNotificationsRepo()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo, owner_id="owner-2"))
    handler = module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type=event_type,
        actor_user_id="actor-1",
        request_id=10,
        offer_id=100,
        dedupe_key=f"{event_type}:100",
        payload={"recipient_user_ids": ["owner-2", "contractor-1"]},
    )
    await handler.handle(payload=event.to_payload())

    assert len(repo.created) == 2
    assert sorted(item.user_id for item in repo.created) == ["contractor-1", "owner-2"]
    assert all(item.title == expected_title for item in repo.created)
    assert all(item.type == event_type for item in repo.created)


@pytest.mark.asyncio
async def test_handler_request_responsible_changed_notifies_old_and_new_without_actor(monkeypatch):
    repo = _FakeNotificationsRepo()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo, owner_id="owner-2"))
    handler = module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type="request.responsible_changed",
        actor_user_id="old-owner",
        request_id=55,
        dedupe_key="request.responsible_changed:55:old-owner:new-owner",
        payload={
            "old_responsible_user_id": "old-owner",
            "new_responsible_user_id": "new-owner",
            "recipient_user_ids": ["old-owner", "new-owner"],
        },
    )
    await handler.handle(payload=event.to_payload())

    assert len(repo.created) == 1
    assert repo.created[0].user_id == "new-owner"
    assert repo.created[0].type == "request.responsible_changed"


@pytest.mark.asyncio
async def test_handler_request_deadline_changed_notifies_responsible(monkeypatch):
    repo = _FakeNotificationsRepo()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo))
    handler = module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type="request.deadline_changed",
        actor_user_id="manager-1",
        request_id=77,
        dedupe_key="request.deadline_changed:77",
        payload={
            "responsible_user_id": "owner-9",
            "old_deadline": "2026-05-20T10:00:00Z",
            "new_deadline": "2026-05-21T10:00:00Z",
        },
    )
    await handler.handle(payload=event.to_payload())

    assert len(repo.created) == 1
    assert repo.created[0].user_id == "owner-9"
    assert repo.created[0].type == "request.deadline_changed"
