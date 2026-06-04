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
    def __init__(
        self,
        *,
        owner_id: str = "owner-1",
        visible_contractors_by_request: dict[str, list[str]] | None = None,
    ) -> None:
        self._owner_id = owner_id
        self._visible_contractors_by_request = visible_contractors_by_request or {}

    async def get_by_id(self, *, request_id: str):
        return SimpleNamespace(id=request_id, id_user=self._owner_id)

    async def list_active_keycloak_visible_contractor_user_ids(
        self,
        *,
        request_id: str,
        contractor_role_id: int,
    ) -> list[str]:
        _ = contractor_role_id
        return list(self._visible_contractors_by_request.get(request_id, []))


class _FakeChatsRepo:
    def __init__(self, recipients: list[str] | None = None) -> None:
        self._recipients = recipients or []

    async def list_active_participant_user_ids(self, *, chat_id: int) -> list[str]:
        _ = chat_id
        return list(self._recipients)


class _FakeOffersRepo:
    def __init__(self, *, offers_by_request: dict[str, list[SimpleNamespace]] | None = None) -> None:
        self._offers_by_request = offers_by_request or {}

    async def list_by_request(self, *, request_id: str):
        return list(self._offers_by_request.get(request_id, []))

    async def get_by_id(self, *, offer_id: int):
        for items in self._offers_by_request.values():
            for offer in items:
                if offer.id == offer_id:
                    return offer
        return None


class _FakeUsersRepo:
    def __init__(self, *, role_by_user_id: dict[str, int]) -> None:
        self._role_by_user_id = role_by_user_id

    async def list_by_role_ids_with_profiles_and_roles(self, *, role_ids: list[int]):
        role_set = set(role_ids)
        rows = []
        for user_id, role_id in sorted(self._role_by_user_id.items()):
            if role_id not in role_set:
                continue
            rows.append((SimpleNamespace(id=user_id, id_role=role_id), None, None))
        return rows

    async def list_by_ids_with_profiles_and_roles(self, *, user_ids: list[str]):
        rows = []
        for user_id in user_ids:
            role_id = self._role_by_user_id.get(user_id)
            if role_id is None:
                continue
            rows.append((SimpleNamespace(id=user_id, id_role=role_id), None, None))
        return rows

    async def get_by_id(self, user_id: str):
        role_id = self._role_by_user_id.get(user_id)
        if role_id is None:
            return None
        return SimpleNamespace(id=user_id, id_role=role_id)


class _FakeUserAuthAccountsRepo:
    def __init__(self, *, keycloak_user_ids: set[str]) -> None:
        self._keycloak_user_ids = keycloak_user_ids

    async def get_by_user_provider(
        self,
        *,
        user_id: str,
        provider: str,
        include_inactive: bool = False,
    ):
        _ = include_inactive
        if provider != "keycloak":
            return None
        if user_id not in self._keycloak_user_ids:
            return None
        return SimpleNamespace(id_user=user_id, provider=provider, is_active=True)


class _FakeProfilesRepo:
    def __init__(
        self,
        *,
        full_name: str = "Target User",
        mail: str = "target@example.com",
    ) -> None:
        self._full_name = full_name
        self._mail = mail

    async def get_by_id(self, user_id: str):
        return SimpleNamespace(full_name=self._full_name, mail=self._mail, id=user_id)


class _FakeUow:
    def __init__(
        self,
        repo: _FakeNotificationsRepo,
        *,
        owner_id: str = "owner-1",
        chat_recipients: list[str] | None = None,
        offers_by_request: dict[str, list[SimpleNamespace]] | None = None,
        role_by_user_id: dict[str, int] | None = None,
        keycloak_user_ids: set[str] | None = None,
        visible_contractors_by_request: dict[str, list[str]] | None = None,
        profiles_repo: _FakeProfilesRepo | None = None,
    ) -> None:
        if role_by_user_id is None:
            role_by_user_id = {
                "admin-1": module.settings.admin_role_id,
                "admin-2": module.settings.superadmin_role_id,
                "owner-1": module.settings.project_manager_role_id,
                "owner-2": module.settings.project_manager_role_id,
                "owner-9": module.settings.project_manager_role_id,
                "manager-1": module.settings.project_manager_role_id,
                "employee-1": module.settings.economist_role_id,
                "actor-1": module.settings.project_manager_role_id,
                "user-1": module.settings.economist_role_id,
                "user-2": module.settings.economist_role_id,
                "user-3": module.settings.economist_role_id,
                "old-owner": module.settings.project_manager_role_id,
                "new-owner": module.settings.project_manager_role_id,
                "contractor-1": module.settings.contractor_role_id,
                "contractor-submitted": module.settings.contractor_role_id,
                "contractor-accepted": module.settings.contractor_role_id,
                "contractor-rejected": module.settings.contractor_role_id,
                "target-1": module.settings.contractor_role_id,
            }
        if keycloak_user_ids is None:
            keycloak_user_ids = {
                "contractor-1",
                "contractor-submitted",
                "contractor-accepted",
                "target-1",
            }

        self.notifications = repo
        self.requests = _FakeRequestsRepo(
            owner_id=owner_id,
            visible_contractors_by_request=visible_contractors_by_request,
        )
        self.chats = _FakeChatsRepo(chat_recipients)
        self.offers = _FakeOffersRepo(offers_by_request=offers_by_request)
        self.users = _FakeUsersRepo(role_by_user_id=role_by_user_id)
        self.user_auth_accounts = _FakeUserAuthAccountsRepo(keycloak_user_ids=keycloak_user_ids)
        self.profiles = profiles_repo or _FakeProfilesRepo()

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
    ("new_status", "expected_title"),
    (
        ("accepted", "Коммерческое предложение принято"),
        ("rejected", "Коммерческое предложение отклонено"),
        ("deleted", "Коммерческое предложение удалено"),
    ),
)
async def test_handler_offer_status_events_create_notifications(monkeypatch, new_status: str, expected_title: str):
    repo = _FakeNotificationsRepo()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo, owner_id="owner-2"))
    handler = module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type="offer.status_changed",
        actor_user_id="actor-1",
        request_id=10,
        offer_id=100,
        dedupe_key=f"offer.status_changed:100:{new_status}",
        payload={"recipient_user_ids": ["owner-2", "contractor-1"], "new_status": new_status},
    )
    await handler.handle(payload=event.to_payload())

    assert len(repo.created) == 2
    assert sorted(item.user_id for item in repo.created) == ["contractor-1", "owner-2"]
    assert all(item.title == expected_title for item in repo.created)
    assert all(item.type == "offer.status_changed" for item in repo.created)


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
    assert repo.created[0].title == "Изменен ответственный по заявке"


@pytest.mark.asyncio
async def test_handler_request_responsible_changed_skips_old_operator(monkeypatch):
    repo = _FakeNotificationsRepo()
    role_by_user_id = {
        "admin-1": module.settings.admin_role_id,
        "admin-2": module.settings.superadmin_role_id,
        "old-owner": module.settings.operator_role_id,
        "new-owner": module.settings.project_manager_role_id,
        "manager-1": module.settings.project_manager_role_id,
    }
    monkeypatch.setattr(
        module,
        "UnitOfWork",
        lambda: _FakeUow(repo, owner_id="owner-2", role_by_user_id=role_by_user_id),
    )
    handler = module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type="request.responsible_changed",
        actor_user_id="manager-1",
        request_id=55,
        dedupe_key="request.responsible_changed:55:old-owner:new-owner:operator",
        payload={
            "old_responsible_user_id": "old-owner",
            "new_responsible_user_id": "new-owner",
        },
    )
    await handler.handle(payload=event.to_payload())

    assert len(repo.created) == 1
    assert repo.created[0].user_id == "new-owner"
    assert repo.created[0].title == "Вам назначена заявка"
    assert repo.created[0].type == "request.responsible_changed"


@pytest.mark.asyncio
async def test_handler_offer_status_event_filters_non_keycloak_contractor(monkeypatch):
    repo = _FakeNotificationsRepo()
    monkeypatch.setattr(
        module,
        "UnitOfWork",
        lambda: _FakeUow(repo, owner_id="owner-2", keycloak_user_ids=set()),
    )
    handler = module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type="offer.status_changed",
        actor_user_id="actor-1",
        request_id=10,
        offer_id=100,
        dedupe_key="offer.status_changed:100:accepted:no-keycloak",
        payload={"recipient_user_ids": ["owner-2", "contractor-1"], "new_status": "accepted"},
    )
    await handler.handle(payload=event.to_payload())

    assert len(repo.created) == 1
    assert repo.created[0].user_id == "owner-2"
    assert repo.created[0].type == "offer.status_changed"


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


@pytest.mark.asyncio
async def test_handler_request_files_changed_notifies_responsible_and_submitted_accepted(monkeypatch):
    repo = _FakeNotificationsRepo()
    offers = {
        "77": [
            SimpleNamespace(id=1, id_user="contractor-submitted", status="submitted"),
            SimpleNamespace(id=2, id_user="contractor-accepted", status="accepted"),
            SimpleNamespace(id=3, id_user="contractor-rejected", status="rejected"),
        ]
    }
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo, owner_id="owner-9", offers_by_request=offers))
    handler = module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type="request.files_changed",
        actor_user_id="owner-9",
        request_id=77,
        dedupe_key="request.files_changed:77:1",
        payload={"file_ids": [1], "changed_file_count": 1},
    )
    await handler.handle(payload=event.to_payload())

    assert sorted(item.user_id for item in repo.created) == ["contractor-accepted", "contractor-submitted"]


@pytest.mark.asyncio
async def test_handler_user_status_changed_notifies_admins_except_actor(monkeypatch):
    repo = _FakeNotificationsRepo()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo))
    handler = module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type="user.status_changed",
        actor_user_id="admin-1",
        dedupe_key="user.status_changed:target-1:review:active",
        payload={
            "target_user_id": "target-1",
            "old_status": "review",
            "new_status": "active",
            "target_role": 7,
            "email_notification_queued": True,
        },
    )
    await handler.handle(payload=event.to_payload())

    assert len(repo.created) == 1
    assert repo.created[0].user_id == "admin-2"
    assert repo.created[0].type == "user.status_changed"


@pytest.mark.asyncio
async def test_handler_user_status_changed_uses_login_when_profile_name_missing(monkeypatch):
    repo = _FakeNotificationsRepo()
    monkeypatch.setattr(
        module,
        "UnitOfWork",
        lambda: _FakeUow(
            repo,
            profiles_repo=_FakeProfilesRepo(full_name="Не указано", mail="Не указано"),
        ),
    )
    handler = module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type="user.status_changed",
        actor_user_id="admin-1",
        dedupe_key="user.status_changed:contractor-login:review:active",
        payload={
            "target_user_id": "contractor-login",
            "old_status": "review",
            "new_status": "active",
        },
    )
    await handler.handle(payload=event.to_payload())

    assert repo.created[0].body == "Изменен статус пользователя contractor-login."


@pytest.mark.asyncio
async def test_handler_user_review_required_notifies_admin_and_superadmin(monkeypatch):
    repo = _FakeNotificationsRepo()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo))
    handler = module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type="user.review_required",
        actor_user_id="admin-1",
        dedupe_key="user.review_required:target-1",
        payload={
            "target_user_id": "target-1",
            "target_role": module.settings.contractor_role_id,
        },
    )
    await handler.handle(payload=event.to_payload())

    assert [item.user_id for item in repo.created] == ["admin-1", "admin-2"]
    assert all(item.type == "user.review_required" for item in repo.created)


@pytest.mark.asyncio
async def test_handler_user_review_required_excludes_contractor_target_from_recipients(monkeypatch):
    repo = _FakeNotificationsRepo()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo))
    handler = module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type="user.review_required",
        actor_user_id="target-1",
        dedupe_key="user.review_required:target-1:self-register",
        payload={
            "target_user_id": "target-1",
            "target_role": module.settings.contractor_role_id,
        },
    )
    await handler.handle(payload=event.to_payload())

    assert [item.user_id for item in repo.created] == ["admin-1", "admin-2"]
    assert all(item.user_id != "target-1" for item in repo.created)


@pytest.mark.asyncio
async def test_handler_plan_assigned_notifies_responsible(monkeypatch):
    repo = _FakeNotificationsRepo()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo))
    handler = module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type="plan.assigned",
        actor_user_id="manager-1",
        dedupe_key="plan.assigned:101:employee-1",
        payload={
            "plan_id": 101,
            "responsible_user_id": "employee-1",
            "assigned_by_user_id": "manager-1",
            "parent_plan_id": 55,
            "plan_sum": "150000.00",
            "period": "2026-05",
        },
    )
    await handler.handle(payload=event.to_payload())

    assert len(repo.created) == 1
    assert repo.created[0].user_id == "employee-1"
    assert repo.created[0].type == "plan.assigned"


@pytest.mark.asyncio
async def test_handler_plan_assigned_skips_self_notification(monkeypatch):
    repo = _FakeNotificationsRepo()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo))
    handler = module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type="plan.assigned",
        actor_user_id="employee-1",
        dedupe_key="plan.assigned:101:employee-1",
        payload={
            "plan_id": 101,
            "responsible_user_id": "employee-1",
        },
    )
    await handler.handle(payload=event.to_payload())

    assert repo.created == []


@pytest.mark.asyncio
async def test_handler_plan_updated_notifies_responsible(monkeypatch):
    repo = _FakeNotificationsRepo()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo))
    handler = module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type="plan.updated",
        actor_user_id="manager-1",
        dedupe_key="plan.updated:101:employee-1:2026-05-19T12:00:00Z",
        payload={
            "plan_id": 101,
            "responsible_user_id": "employee-1",
            "old_plan_sum": "120000.00",
            "new_plan_sum": "150000.00",
        },
    )
    await handler.handle(payload=event.to_payload())

    assert len(repo.created) == 1
    assert repo.created[0].user_id == "employee-1"
    assert repo.created[0].type == "plan.updated"


@pytest.mark.asyncio
async def test_handler_plan_updated_skips_self_notification(monkeypatch):
    repo = _FakeNotificationsRepo()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo))
    handler = module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type="plan.updated",
        actor_user_id="employee-1",
        dedupe_key="plan.updated:101:employee-1:2026-05-19T12:00:00Z",
        payload={
            "plan_id": 101,
            "responsible_user_id": "employee-1",
        },
    )
    await handler.handle(payload=event.to_payload())

    assert repo.created == []


@pytest.mark.asyncio
async def test_handler_plan_updated_skips_empty_recipients(monkeypatch):
    repo = _FakeNotificationsRepo()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo))
    handler = module.ProcessNotificationEventHandler()

    event = build_process_notification_event(
        event_type="plan.updated",
        actor_user_id="manager-1",
        dedupe_key="plan.updated:101:none:2026-05-19T12:00:00Z",
        payload={"plan_id": 101},
    )
    await handler.handle(payload=event.to_payload())

    assert repo.created == []
