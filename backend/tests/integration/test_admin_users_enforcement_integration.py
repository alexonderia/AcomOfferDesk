"""Integration-style tests for backend enforcement on /users* endpoints."""

from __future__ import annotations

from types import SimpleNamespace

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.domain.exceptions import Unauthorized
from app.domain.permissions import PermissionCodes
from app.services import users as users_service


ROLE_NAMES = {
    settings.superadmin_role_id: "Суперадмин",
    settings.admin_role_id: "Администратор",
    settings.project_manager_role_id: "Руководитель проекта",
    settings.lead_economist_role_id: "Ведущий экономист",
    settings.economist_role_id: "Экономист",
    settings.operator_role_id: "Оператор",
    settings.contractor_role_id: "Контрагент",
}


class _UsersRepo:
    def __init__(self) -> None:
        self._session = object()
        self._users: dict[str, SimpleNamespace] = {
            "pm-1": SimpleNamespace(id="pm-1", id_role=settings.project_manager_role_id, id_parent=None, status="active", tg_user_id=None),
            "pm-2": SimpleNamespace(id="pm-2", id_role=settings.project_manager_role_id, id_parent="pm-1", status="active", tg_user_id=None),
            "lead-1": SimpleNamespace(id="lead-1", id_role=settings.lead_economist_role_id, id_parent="pm-1", status="active", tg_user_id=None),
            "lead-2": SimpleNamespace(id="lead-2", id_role=settings.lead_economist_role_id, id_parent="lead-1", status="active", tg_user_id=None),
            "eco-1": SimpleNamespace(id="eco-1", id_role=settings.economist_role_id, id_parent="lead-1", status="active", tg_user_id=None),
            "eco-2": SimpleNamespace(id="eco-2", id_role=settings.economist_role_id, id_parent="eco-1", status="active", tg_user_id=None),
            "eco-3": SimpleNamespace(id="eco-3", id_role=settings.economist_role_id, id_parent="lead-2", status="active", tg_user_id=None),
            "operator-1": SimpleNamespace(id="operator-1", id_role=settings.operator_role_id, id_parent="lead-1", status="active", tg_user_id=None),
            "admin-1": SimpleNamespace(id="admin-1", id_role=settings.admin_role_id, id_parent=None, status="active", tg_user_id=None),
            "contractor-1": SimpleNamespace(id="contractor-1", id_role=settings.contractor_role_id, id_parent=None, status="active", tg_user_id=None),
        }
        self._profiles: dict[str, SimpleNamespace] = {
            user_id: SimpleNamespace(id=user_id, full_name=user_id, phone=None, mail=f"{user_id}@example.com")
            for user_id in self._users
        }

    async def get_by_id(self, user_id: str):
        return self._users.get(user_id)

    async def exists(self, user_id: str) -> bool:
        return user_id in self._users

    async def add(self, user) -> None:
        self._users[user.id] = user

    async def get_role_by_id(self, role_id: int):
        role_name = ROLE_NAMES.get(role_id)
        if role_name is None:
            return None
        return SimpleNamespace(id=role_id, role=role_name)

    async def update_status(self, user, status: str) -> None:
        user.status = status

    async def update_role(self, user, role_id: int) -> None:
        user.id_role = role_id

    async def update_parent(self, user, manager_user_id: str) -> None:
        user.id_parent = manager_user_id

    async def list_by_role_ids_with_profiles_and_roles(self, *, role_ids: list[int]):
        rows = []
        for user in self._users.values():
            if user.id_role not in role_ids:
                continue
            role = await self.get_role_by_id(user.id_role)
            rows.append((user, self._profiles.get(user.id), role))
        return rows

    async def list_users_with_profiles(self, *, role_id: int | None = None):
        rows = []
        for user in self._users.values():
            if role_id is not None and user.id_role != role_id:
                continue
            rows.append((user, self._profiles.get(user.id)))
        return rows

    async def list_contractors(self, *, contractor_role_id: int):
        rows = []
        for user in self._users.values():
            if user.id_role != contractor_role_id:
                continue
            rows.append((user, self._profiles.get(user.id), None, None))
        return rows

    async def list_active_user_parent_pairs(self):
        return [
            (user.id, user.id_parent)
            for user in self._users.values()
            if user.status == "active"
        ]


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


class _UserStatusPeriodsRepo:
    async def get_active_for_user(self, *, user_id: str):
        _ = user_id
        return None

    async def list_for_user(self, *, user_id: str):
        _ = user_id
        return []


class _UsersUow:
    def __init__(self) -> None:
        self.users = _UsersRepo()
        self.profiles = _ProfilesRepo(self.users)
        self.user_auth_accounts = _UserAuthAccountsRepo()
        self.tg_users = object()
        self.user_status_periods = _UserStatusPeriodsRepo()
        self.company_contacts = object()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        _ = (exc_type, exc, tb)


def _set_fake_keycloak(monkeypatch) -> None:
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
        _ = (self, username, email, first_name, last_name, middle_name, sync_names, email_verified)
        return SimpleNamespace(id=f"kc-{username}")

    async def _fake_sync_keycloak_app_role_for_user(*args, **kwargs) -> None:
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(users_service.KeycloakAdminService, "ensure_user", _fake_ensure_user)
    monkeypatch.setattr(users_service, "sync_keycloak_app_role_for_user", _fake_sync_keycloak_app_role_for_user)


def test_admin_can_create_user_with_permission(
    test_client,
    monkeypatch,
    set_uow,
    set_current_user,
    make_current_user,
):
    _set_fake_keycloak(monkeypatch)
    set_uow(_UsersUow())
    admin = make_current_user(
        user_id="admin-1",
        role_id=settings.admin_role_id,
        permissions={PermissionCodes.USERS_CREATE},
    )
    set_current_user(admin)

    response = test_client.post(
        "/api/v1/users/register",
        json={
            "login": "new-operator",
            "password": "StrongPass1!",
            "role_id": settings.operator_role_id,
            "mail": "new-operator@example.com",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["user_id"] == "new-operator"


def test_user_without_users_create_cannot_register_user(test_client, set_uow, set_current_user, make_current_user):
    set_uow(_UsersUow())
    contractor = make_current_user(
        user_id="contractor-1",
        role_id=settings.contractor_role_id,
        permissions=set(),
    )
    set_current_user(contractor)

    response = test_client.post(
        "/api/v1/users/register",
        json={
            "login": "blocked-user",
            "password": "StrongPass1!",
            "role_id": settings.operator_role_id,
            "mail": "blocked@example.com",
        },
    )

    assert response.status_code == 403


def test_superadmin_can_create_project_manager_without_manager(
    test_client,
    monkeypatch,
    set_uow,
    set_current_user,
    make_current_user,
):
    _set_fake_keycloak(monkeypatch)
    set_uow(_UsersUow())
    superadmin = make_current_user(
        user_id="root-1",
        role_id=settings.superadmin_role_id,
        permissions={PermissionCodes.USERS_CREATE},
    )
    set_current_user(superadmin)

    response = test_client.post(
        "/api/v1/users/register",
        json={
            "login": "pm-new",
            "role_id": settings.project_manager_role_id,
            "mail": "pm-new@example.com",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["user_id"] == "pm-new"


def test_superadmin_cannot_create_project_manager_with_lead_as_manager(
    test_client,
    monkeypatch,
    set_uow,
    set_current_user,
    make_current_user,
):
    _set_fake_keycloak(monkeypatch)
    set_uow(_UsersUow())
    superadmin = make_current_user(
        user_id="root-1",
        role_id=settings.superadmin_role_id,
        permissions={PermissionCodes.USERS_CREATE},
    )
    set_current_user(superadmin)

    response = test_client.post(
        "/api/v1/users/register",
        json={
            "login": "pm-invalid",
            "role_id": settings.project_manager_role_id,
            "id_parent": "lead-1",
            "mail": "pm-invalid@example.com",
        },
    )

    assert response.status_code == 409


def test_superadmin_cannot_create_lead_without_manager(
    test_client,
    monkeypatch,
    set_uow,
    set_current_user,
    make_current_user,
):
    _set_fake_keycloak(monkeypatch)
    set_uow(_UsersUow())
    superadmin = make_current_user(
        user_id="root-1",
        role_id=settings.superadmin_role_id,
        permissions={PermissionCodes.USERS_CREATE},
    )
    set_current_user(superadmin)

    response = test_client.post(
        "/api/v1/users/register",
        json={
            "login": "lead-no-manager",
            "role_id": settings.lead_economist_role_id,
            "mail": "lead-no-manager@example.com",
        },
    )

    assert response.status_code == 409


def test_superadmin_can_create_lead_with_lead_manager(
    test_client,
    monkeypatch,
    set_uow,
    set_current_user,
    make_current_user,
):
    _set_fake_keycloak(monkeypatch)
    set_uow(_UsersUow())
    superadmin = make_current_user(
        user_id="root-1",
        role_id=settings.superadmin_role_id,
        permissions={PermissionCodes.USERS_CREATE},
    )
    set_current_user(superadmin)

    response = test_client.post(
        "/api/v1/users/register",
        json={
            "login": "lead-second",
            "role_id": settings.lead_economist_role_id,
            "id_parent": "lead-1",
            "mail": "lead-second@example.com",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["user_id"] == "lead-second"


def test_superadmin_cannot_create_economist_with_project_manager_manager(
    test_client,
    monkeypatch,
    set_uow,
    set_current_user,
    make_current_user,
):
    _set_fake_keycloak(monkeypatch)
    set_uow(_UsersUow())
    superadmin = make_current_user(
        user_id="root-1",
        role_id=settings.superadmin_role_id,
        permissions={PermissionCodes.USERS_CREATE},
    )
    set_current_user(superadmin)

    response = test_client.post(
        "/api/v1/users/register",
        json={
            "login": "eco-invalid-manager",
            "role_id": settings.economist_role_id,
            "id_parent": "pm-1",
            "mail": "eco-invalid-manager@example.com",
        },
    )

    assert response.status_code == 409


def test_lead_economist_can_update_subordinate_status(
    test_client,
    set_uow,
    set_current_user,
    make_current_user,
):
    set_uow(_UsersUow())
    lead = make_current_user(
        user_id="lead-1",
        role_id=settings.lead_economist_role_id,
        permissions={PermissionCodes.USERS_STATUS_UPDATE},
    )
    set_current_user(lead)

    response = test_client.patch("/api/v1/users/eco-1/status", json={"user_status": "inactive"})

    assert response.status_code == 200
    assert response.json()["data"]["user_status"] == "Неактивен"


def test_user_without_users_status_update_cannot_change_status(test_client, set_uow, set_current_user, make_current_user):
    set_uow(_UsersUow())
    no_access = make_current_user(
        user_id="admin-1",
        role_id=settings.admin_role_id,
        permissions=set(),
    )
    set_current_user(no_access)

    response = test_client.patch("/api/v1/users/eco-1/status", json={"user_status": "inactive"})

    assert response.status_code == 403


def test_superadmin_can_update_user_role(test_client, set_uow, set_current_user, make_current_user):
    set_uow(_UsersUow())
    superadmin = make_current_user(
        user_id="root-1",
        role_id=settings.superadmin_role_id,
        permissions={PermissionCodes.USERS_ROLE_UPDATE_ANY},
    )
    set_current_user(superadmin)

    response = test_client.patch("/api/v1/users/eco-1/role", json={"role_id": settings.operator_role_id})

    assert response.status_code == 200
    assert response.json()["data"]["role_id"] == settings.operator_role_id


def test_user_without_role_update_permission_cannot_change_role(
    test_client,
    set_uow,
    set_current_user,
    make_current_user,
):
    set_uow(_UsersUow())
    no_access = make_current_user(
        user_id="lead-1",
        role_id=settings.lead_economist_role_id,
        permissions={PermissionCodes.USERS_READ},
    )
    set_current_user(no_access)

    response = test_client.patch("/api/v1/users/eco-1/role", json={"role_id": settings.operator_role_id})

    assert response.status_code == 403


def test_project_manager_can_update_subordinate_manager(
    test_client,
    monkeypatch,
    set_uow,
    set_current_user,
    make_current_user,
):
    async def _fake_manager_candidates(self, *, current_user, target_role_id, target_user_id=None):
        _ = (self, current_user, target_role_id, target_user_id)
        return [SimpleNamespace(user_id="lead-1")]

    monkeypatch.setattr(users_service.UserQueryService, "list_manager_candidates", _fake_manager_candidates)
    set_uow(_UsersUow())
    pm = make_current_user(
        user_id="pm-1",
        role_id=settings.project_manager_role_id,
        permissions={PermissionCodes.USERS_MANAGER_UPDATE},
    )
    set_current_user(pm)

    response = test_client.patch("/api/v1/users/eco-1/manager", json={"manager_user_id": "lead-1"})

    assert response.status_code == 200
    assert response.json()["data"]["manager_user_id"] == "lead-1"


def test_project_manager_can_remove_project_manager_manager(
    test_client,
    set_uow,
    set_current_user,
    make_current_user,
):
    set_uow(_UsersUow())
    manager = make_current_user(
        user_id="pm-1",
        role_id=settings.project_manager_role_id,
        permissions={PermissionCodes.USERS_MANAGER_UPDATE},
    )
    set_current_user(manager)

    response = test_client.patch("/api/v1/users/pm-2/manager", json={"manager_user_id": None})

    assert response.status_code == 200
    assert response.json()["data"]["manager_user_id"] is None


def test_project_manager_cannot_remove_lead_manager(
    test_client,
    set_uow,
    set_current_user,
    make_current_user,
):
    set_uow(_UsersUow())
    manager = make_current_user(
        user_id="pm-1",
        role_id=settings.project_manager_role_id,
        permissions={PermissionCodes.USERS_MANAGER_UPDATE},
    )
    set_current_user(manager)

    response = test_client.patch("/api/v1/users/lead-1/manager", json={"manager_user_id": None})

    assert response.status_code == 409


def test_project_manager_cannot_assign_project_manager_to_economist_directly(
    test_client,
    set_uow,
    set_current_user,
    make_current_user,
):
    set_uow(_UsersUow())
    manager = make_current_user(
        user_id="pm-1",
        role_id=settings.project_manager_role_id,
        permissions={PermissionCodes.USERS_MANAGER_UPDATE},
    )
    set_current_user(manager)

    response = test_client.patch("/api/v1/users/eco-1/manager", json={"manager_user_id": "pm-1"})

    assert response.status_code == 409


def test_project_manager_cannot_assign_descendant_as_manager_due_to_cycle(
    test_client,
    set_uow,
    set_current_user,
    make_current_user,
):
    set_uow(_UsersUow())
    manager = make_current_user(
        user_id="pm-1",
        role_id=settings.project_manager_role_id,
        permissions={PermissionCodes.USERS_MANAGER_UPDATE},
    )
    set_current_user(manager)

    response = test_client.patch("/api/v1/users/lead-1/manager", json={"manager_user_id": "eco-2"})

    assert response.status_code == 409


def test_user_without_users_manager_update_cannot_change_manager(
    test_client,
    set_uow,
    set_current_user,
    make_current_user,
):
    set_uow(_UsersUow())
    no_access = make_current_user(
        user_id="pm-1",
        role_id=settings.project_manager_role_id,
        permissions=set(),
    )
    set_current_user(no_access)

    response = test_client.patch("/api/v1/users/eco-1/manager", json={"manager_user_id": "lead-1"})

    assert response.status_code == 403


def test_economist_users_list_is_limited_to_own_contour(test_client, set_uow, set_current_user, make_current_user):
    set_uow(_UsersUow())
    economist = make_current_user(
        user_id="eco-1",
        role_id=settings.economist_role_id,
        permissions={PermissionCodes.USERS_READ},
    )
    set_current_user(economist)

    response = test_client.get("/api/v1/users")

    assert response.status_code == 200
    user_ids = {item["user_id"] for item in response.json()["data"]["items"]}
    assert "lead-1" in user_ids
    assert "eco-2" in user_ids
    assert "eco-3" in user_ids
    assert "operator-1" in user_ids
    assert "admin-1" not in user_ids


def test_manager_candidates_follow_new_matrix_and_exclude_self_and_descendants(
    test_client,
    set_uow,
    set_current_user,
    make_current_user,
):
    set_uow(_UsersUow())
    superadmin = make_current_user(
        user_id="root-1",
        role_id=settings.superadmin_role_id,
        permissions={PermissionCodes.USERS_CREATE},
    )
    set_current_user(superadmin)

    pm_response = test_client.get("/api/v1/users/manager-candidates?target_role_id=4&target_user_id=pm-2")
    lead_response = test_client.get("/api/v1/users/manager-candidates?target_role_id=5&target_user_id=lead-1")
    eco_response = test_client.get("/api/v1/users/manager-candidates?target_role_id=6&target_user_id=eco-1")

    assert pm_response.status_code == 200
    assert lead_response.status_code == 200
    assert eco_response.status_code == 200

    pm_candidate_ids = {item["user_id"] for item in pm_response.json()["data"]["items"]}
    lead_candidate_ids = {item["user_id"] for item in lead_response.json()["data"]["items"]}
    eco_candidate_ids = {item["user_id"] for item in eco_response.json()["data"]["items"]}

    assert pm_candidate_ids == {"pm-1"}
    assert "eco-2" not in lead_candidate_ids
    assert {"pm-1", "pm-2", "lead-1", "lead-2"}.issuperset(lead_candidate_ids)
    assert "pm-1" not in eco_candidate_ids
    assert {"lead-1", "lead-2", "eco-2", "eco-3"}.issuperset(eco_candidate_ids)


def test_anonymous_user_gets_401_for_users_endpoint(test_client, api_app):
    async def _anonymous():
        raise Unauthorized("Missing credentials")

    api_app.dependency_overrides[get_current_user] = _anonymous

    response = test_client.get("/api/v1/users")

    assert response.status_code == 401
