from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core.uow import UnitOfWork
from app.infrastructure import notification_publisher as publisher_module
from app.services import process_notification_events as process_events_module
from shared.process_notifications import build_process_notification_event


class _FakeNotificationsRepo:
    def __init__(self) -> None:
        self.created = []
        self._dedupe: set[tuple[str, str, str, str]] = set()

    async def create(self, notification):
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


class _FakeProcessUow:
    def __init__(self, repo: _FakeNotificationsRepo) -> None:
        self.notifications = repo
        self.requests = SimpleNamespace(get_by_id=self._get_request_by_id)
        self.chats = SimpleNamespace(list_active_participant_user_ids=self._list_chat_participants)
        self.users = SimpleNamespace(
            list_by_ids_with_profiles_and_roles=self._list_users_by_ids_with_roles,
            get_by_id=self._get_user_by_id,
        )
        self.user_auth_accounts = SimpleNamespace(get_by_user_provider=self._get_auth_by_user_provider)

    async def _get_request_by_id(self, *, request_id: int):
        return SimpleNamespace(id=request_id, id_user="owner-1")

    async def _list_chat_participants(self, *, chat_id: int):
        _ = chat_id
        return ["owner-1", "contractor-2"]

    async def _list_users_by_ids_with_roles(self, *, user_ids: list[str]):
        role_by_user_id = {
            "owner-1": process_events_module.settings.project_manager_role_id,
            "contractor-2": process_events_module.settings.contractor_role_id,
        }
        rows = []
        for user_id in user_ids:
            role_id = role_by_user_id.get(user_id)
            if role_id is None:
                continue
            rows.append((SimpleNamespace(id=user_id, id_role=role_id), None, None))
        return rows

    async def _get_user_by_id(self, user_id: str):
        role_by_user_id = {
            "owner-1": process_events_module.settings.project_manager_role_id,
            "contractor-2": process_events_module.settings.contractor_role_id,
        }
        role_id = role_by_user_id.get(user_id)
        if role_id is None:
            return None
        return SimpleNamespace(id=user_id, id_role=role_id)

    async def _get_auth_by_user_provider(
        self,
        *,
        user_id: str,
        provider: str,
        include_inactive: bool = False,
    ):
        _ = include_inactive
        if provider != "keycloak":
            return None
        if user_id != "contractor-2":
            return None
        return SimpleNamespace(id_user=user_id, provider=provider, is_active=True)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        _ = (exc_type, exc, tb)


class _FakeSession:
    def __init__(self, *, fail_commit: bool = False) -> None:
        self.fail_commit = fail_commit
        self.begin_called = False
        self.commit_called = False
        self.rollback_called = False
        self.close_called = False

    async def begin(self):
        self.begin_called = True

    async def commit(self):
        self.commit_called = True
        if self.fail_commit:
            raise RuntimeError("commit failed")

    async def rollback(self):
        self.rollback_called = True

    async def close(self):
        self.close_called = True


@pytest.mark.asyncio
async def test_publish_event_then_consume_creates_one_notification_and_dedupes(monkeypatch):
    published_messages: list[dict] = []

    async def _fake_publish_notification(event_type: str, payload: dict) -> None:
        _ = event_type
        published_messages.append(payload)

    monkeypatch.setattr(publisher_module, "publish_notification", _fake_publish_notification)

    repo = _FakeNotificationsRepo()
    monkeypatch.setattr(process_events_module, "UnitOfWork", lambda: _FakeProcessUow(repo))
    handler = process_events_module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type="offer.created",
        actor_user_id="contractor-1",
        request_id=42,
        offer_id=100,
        dedupe_key="offer.created:100",
    )
    ok = await publisher_module.publish_process_notification_event(event)
    assert ok is True

    assert len(published_messages) == 1
    payload = published_messages[0]
    await handler.handle(payload=payload)
    await handler.handle(payload=payload)

    assert len(repo.created) == 1
    assert repo.created[0].type == "offer.created"


@pytest.mark.asyncio
async def test_consumer_handler_handles_invalid_payload_without_crash(monkeypatch):
    repo = _FakeNotificationsRepo()
    monkeypatch.setattr(process_events_module, "UnitOfWork", lambda: _FakeProcessUow(repo))
    handler = process_events_module.ProcessNotificationEventHandler()

    await handler.handle(payload={"invalid": True})

    assert repo.created == []


@pytest.mark.asyncio
async def test_after_commit_hooks_not_executed_when_commit_fails():
    session = _FakeSession(fail_commit=True)
    uow = UnitOfWork(session_factory=lambda: session)
    called = {"value": False}

    with pytest.raises(RuntimeError):
        async with uow:
            uow.add_after_commit_hook(_mark_called(called))

    assert called["value"] is False


@pytest.mark.asyncio
async def test_after_commit_hook_failure_does_not_break_business_flow():
    session = _FakeSession(fail_commit=False)
    uow = UnitOfWork(session_factory=lambda: session)

    async with uow:
        uow.add_after_commit_hook(_raise_hook_error)

    assert session.commit_called is True
    assert session.close_called is True


def _mark_called(flag_store: dict[str, bool]):
    async def _hook() -> None:
        flag_store["value"] = True

    return _hook


async def _raise_hook_error() -> None:
    raise RuntimeError("publish failed")
