from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.domain.exceptions import Forbidden
from app.domain.permissions import PermissionCodes
from app.services import users as users_module
from app.services.contractors import ContractorService
from app.services.users import UserRegistrationService, UserStatusService


class _UsersRepo:
    def __init__(self) -> None:
        self._users: dict[str, SimpleNamespace] = {
            "contractor-1": SimpleNamespace(
                id="contractor-1",
                id_role=settings.contractor_role_id,
                id_parent=None,
                status="review",
                tg_user_id=None,
                created_at=None,
            ),
            "economist-1": SimpleNamespace(
                id="economist-1",
                id_role=settings.economist_role_id,
                id_parent=None,
                status="active",
                tg_user_id=None,
                created_at=None,
            ),
            "admin-1": SimpleNamespace(
                id="admin-1",
                id_role=settings.admin_role_id,
                id_parent=None,
                status="active",
                tg_user_id=None,
                created_at=None,
            ),
        }
        self._profiles: dict[str, SimpleNamespace] = {
            "contractor-1": SimpleNamespace(id="contractor-1", full_name="Иван Петров", phone="+79990000000", mail="contractor@example.com"),
            "economist-1": SimpleNamespace(id="economist-1", full_name="Экономист", phone="+79991112233", mail="economist@example.com"),
        }
        self._companies: dict[str, SimpleNamespace] = {
            "contractor-1": SimpleNamespace(
                id="contractor-1",
                company_name="ООО Ромашка",
                inn="1234567890",
                phone="+79990000000",
                mail="office@example.com",
                address="Moscow",
                note="Trusted",
            )
        }

    async def get_by_id(self, user_id: str):
        return self._users.get(user_id)

    async def exists(self, user_id: str) -> bool:
        return user_id in self._users

    async def add(self, user) -> None:
        self._users[user.id] = user

    async def get_role_by_id(self, role_id: int):
        role_names = {
            settings.superadmin_role_id: "Суперадмин",
            settings.admin_role_id: "Администратор",
            settings.security_officer_role_id: "Служба безопасности",
            settings.contractor_role_id: "Контрагент",
            settings.economist_role_id: "Экономист",
        }
        role_name = role_names.get(role_id)
        if role_name is None:
            return None
        return SimpleNamespace(id=role_id, role=role_name)

    async def list_contractors(self, *, contractor_role_id: int):
        return [
            (
                user,
                self._profiles.get(user.id),
                self._companies.get(user.id),
                None,
            )
            for user in self._users.values()
            if user.id_role == contractor_role_id
        ]

    async def get_with_profile_and_company_contacts(self, *, user_id: str):
        user = self._users.get(user_id)
        if user is None:
            return None
        return (user, self._profiles.get(user_id), self._companies.get(user_id))

    async def update_status(self, user, status: str) -> None:
        user.status = status


class _ProfilesRepo:
    def __init__(self, users_repo: _UsersRepo) -> None:
        self._users_repo = users_repo

    async def add(self, profile) -> None:
        self._users_repo._profiles[profile.id] = profile

    async def get_by_id(self, user_id: str):
        return self._users_repo._profiles.get(user_id)


class _UserAuthAccountsRepo:
    async def get_conflicting_subject(self, *, provider: str, subject: str, exclude_user_id: str):
        _ = (provider, subject, exclude_user_id)
        return None

    async def get_by_user_provider(self, *, user_id: str, provider: str, include_inactive: bool = True):
        _ = (user_id, provider, include_inactive)
        return None

    async def add(self, row) -> None:
        _ = row


class _TgUsersRepo:
    async def get_by_id(self, user_id: str):
        _ = user_id
        return None


@pytest.mark.asyncio
async def test_security_officer_can_list_and_read_contractors(make_current_user):
    users_repo = _UsersRepo()
    profiles_repo = _ProfilesRepo(users_repo)
    service = ContractorService(users_repo, profiles_repo)
    current_user = make_current_user(
        user_id="security-1",
        role_id=settings.security_officer_role_id,
        permissions={
            PermissionCodes.CONTRACTORS_READ,
            PermissionCodes.CONTRACTORS_PROFILE_READ,
        },
    )

    items = await service.list_contractors(current_user=current_user)
    profile = await service.get_contractor(current_user=current_user, contractor_id="contractor-1")

    assert [item.user_id for item in items] == ["contractor-1"]
    assert profile.user_id == "contractor-1"
    assert profile.company_name == "ООО Ромашка"


@pytest.mark.asyncio
async def test_security_officer_can_update_only_contractor_status(make_current_user, monkeypatch):
    users_repo = _UsersRepo()
    profiles_repo = _ProfilesRepo(users_repo)
    service = UserStatusService(users_repo, _TgUsersRepo(), profiles_repo)
    async def _fake_notify_contractor_status_changed_email(*, to_email: str, user_status: str, recipient_user_id: str, initiator_user_id: str) -> bool:
        _ = (to_email, user_status, recipient_user_id, initiator_user_id)
        return True

    monkeypatch.setattr(
        users_module,
        "notify_contractor_status_changed_email",
        _fake_notify_contractor_status_changed_email,
    )
    current_user = make_current_user(
        user_id="security-1",
        role_id=settings.security_officer_role_id,
        permissions={
            PermissionCodes.CONTRACTORS_PROFILE_STATUS_UPDATE,
        },
    )

    result = await service.update_statuses(
        current_user=current_user,
        user_id="contractor-1",
        user_status="active",
        tg_status=None,
        contractor_only=True,
    )

    assert result.user_id == "contractor-1"
    assert result.user_status == "active"

    with pytest.raises(Forbidden):
        await service.update_statuses(
            current_user=current_user,
            user_id="economist-1",
            user_status="inactive",
            tg_status=None,
            contractor_only=True,
        )


@pytest.mark.asyncio
async def test_superadmin_can_create_security_officer_but_admin_cannot(make_current_user, monkeypatch):
    users_repo = _UsersRepo()
    profiles_repo = _ProfilesRepo(users_repo)
    auth_accounts_repo = _UserAuthAccountsRepo()
    service = UserRegistrationService(users_repo, profiles_repo, auth_accounts_repo)

    async def _fake_ensure_user(
        self,
        *,
        username: str,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        middle_name: str | None = None,
        sync_names: bool = False,
        email_verified: bool = False,
    ):
        _ = (self, email, first_name, last_name, middle_name, sync_names, email_verified)
        return SimpleNamespace(id=f"kc-{username}")

    async def _fake_sync_keycloak_app_role_for_user(*args, **kwargs) -> None:
        _ = (args, kwargs)

    async def _fake_notify_new_user_registration(ctx) -> None:
        _ = ctx

    monkeypatch.setattr(users_module.KeycloakAdminService, "ensure_user", _fake_ensure_user)
    monkeypatch.setattr(users_module, "sync_keycloak_app_role_for_user", _fake_sync_keycloak_app_role_for_user)
    monkeypatch.setattr(users_module, "notify_new_user_registration", _fake_notify_new_user_registration)

    superadmin = make_current_user(
        user_id="root-1",
        role_id=settings.superadmin_role_id,
        permissions={PermissionCodes.USERS_CREATE},
    )
    created = await service.register_user(
        superadmin,
        user_id="security-new",
        password=None,
        role_id=settings.security_officer_role_id,
        id_parent=None,
        full_name="Security Officer",
        phone="+79990001122",
        mail="security@example.com",
    )

    assert created.id == "security-new"
    assert created.id_role == settings.security_officer_role_id

    admin = make_current_user(
        user_id="admin-1",
        role_id=settings.admin_role_id,
        permissions={PermissionCodes.USERS_CREATE},
    )
    with pytest.raises(Forbidden):
        await service.register_user(
            admin,
            user_id="security-blocked",
            password=None,
            role_id=settings.security_officer_role_id,
            id_parent=None,
            full_name="Blocked Security",
            phone="+79990002233",
            mail="blocked-security@example.com",
        )
