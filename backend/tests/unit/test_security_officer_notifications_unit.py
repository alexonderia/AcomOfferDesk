from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.services import process_notification_events as module
from shared.process_notifications import build_process_notification_event


class _Repo:
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


class _UsersRepo:
    def __init__(self) -> None:
        self._role_by_user_id = {
            "admin-1": module.settings.admin_role_id,
            "superadmin-1": module.settings.superadmin_role_id,
            "security-1": module.settings.security_officer_role_id,
            "contractor-1": module.settings.contractor_role_id,
        }

    async def list_by_role_ids_with_profiles_and_roles(self, *, role_ids: list[int]):
        role_set = set(role_ids)
        return [
            (SimpleNamespace(id=user_id, id_role=role_id), None, None)
            for user_id, role_id in sorted(self._role_by_user_id.items())
            if role_id in role_set
        ]

    async def list_by_ids_with_profiles_and_roles(self, *, user_ids: list[str]):
        return [
            (SimpleNamespace(id=user_id, id_role=self._role_by_user_id[user_id]), None, None)
            for user_id in user_ids
            if user_id in self._role_by_user_id
        ]

    async def get_by_id(self, user_id: str):
        role_id = self._role_by_user_id.get(user_id)
        if role_id is None:
            return None
        return SimpleNamespace(id=user_id, id_role=role_id)


class _ProfilesRepo:
    async def get_by_id(self, user_id: str):
        if user_id == "contractor-1":
            return SimpleNamespace(id=user_id, full_name="ООО Ромашка", mail="contractor@example.com")
        return SimpleNamespace(id=user_id, full_name=user_id, mail=f"{user_id}@example.com")


class _Uow:
    def __init__(self, repo: _Repo) -> None:
        self.notifications = repo
        self.users = _UsersRepo()
        self.profiles = _ProfilesRepo()
        self.requests = None
        self.chats = None
        self.offers = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        _ = (exc_type, exc, tb)


@pytest.mark.asyncio
async def test_contractor_registration_notifies_security_officer(monkeypatch):
    repo = _Repo()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _Uow(repo))
    handler = module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type="user.review_required",
        actor_user_id="admin-1",
        dedupe_key="user.review_required:contractor-1:contractor_tg",
        payload={
            "target_user_id": "contractor-1",
            "target_role": module.settings.contractor_role_id,
            "source": "contractor_tg",
        },
    )
    await handler.handle(payload=event.to_payload())

    assert [item.user_id for item in repo.created] == ["admin-1", "security-1", "superadmin-1"]
    assert all(item.title == "Зарегистрирован новый контрагент" for item in repo.created)
    assert all(item.link_url == "/contractors" for item in repo.created)


@pytest.mark.asyncio
async def test_manual_contractor_creation_notifies_security_officer(monkeypatch):
    repo = _Repo()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _Uow(repo))
    handler = module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type="user.review_required",
        actor_user_id="admin-1",
        dedupe_key="user.review_required:contractor-1:manual_contractor",
        payload={
            "target_user_id": "contractor-1",
            "target_role": module.settings.contractor_role_id,
            "source": "manual_contractor",
        },
    )
    await handler.handle(payload=event.to_payload())

    assert [item.user_id for item in repo.created] == ["admin-1", "security-1", "superadmin-1"]
    assert all(item.title == "Создан новый контрагент" for item in repo.created)
    assert all(item.body == "Создан новый контрагент: ООО Ромашка." for item in repo.created)


@pytest.mark.asyncio
async def test_contractor_status_changed_notifies_security_officer_without_actor(monkeypatch):
    repo = _Repo()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _Uow(repo))
    handler = module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type="user.status_changed",
        actor_user_id="admin-1",
        dedupe_key="user.status_changed:contractor-1:review:active",
        payload={
            "target_user_id": "contractor-1",
            "target_role": module.settings.contractor_role_id,
            "target_is_contractor": True,
            "old_status": "review",
            "new_status": "active",
        },
    )
    await handler.handle(payload=event.to_payload())

    assert [item.user_id for item in repo.created] == ["security-1", "superadmin-1"]
    assert all(item.title == "Изменен статус контрагента" for item in repo.created)
    assert all(item.body == "Изменен статус контрагента ООО Ромашка: На проверке -> Активен." for item in repo.created)
    assert all(item.link_url == "/contractors" for item in repo.created)
