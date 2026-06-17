from __future__ import annotations

from types import SimpleNamespace

from app.core.config import settings
from app.domain.permissions import PermissionCodes
from tests.integration.conftest import DummyUow


class _ScopedUsersRepo:
    def __init__(self) -> None:
        self._users: dict[str, SimpleNamespace] = {
            "pm-1": SimpleNamespace(
                id="pm-1",
                id_role=settings.project_manager_role_id,
                id_parent=None,
                status="active",
                tg_user_id=None,
            ),
            "lead-1": SimpleNamespace(
                id="lead-1",
                id_role=settings.lead_economist_role_id,
                id_parent="pm-1",
                status="active",
                tg_user_id=None,
            ),
            "lead-2": SimpleNamespace(
                id="lead-2",
                id_role=settings.lead_economist_role_id,
                id_parent="pm-1",
                status="active",
                tg_user_id=None,
            ),
            "eco-1": SimpleNamespace(
                id="eco-1",
                id_role=settings.economist_role_id,
                id_parent="lead-1",
                status="active",
                tg_user_id=None,
            ),
            "eco-2": SimpleNamespace(
                id="eco-2",
                id_role=settings.economist_role_id,
                id_parent="lead-1",
                status="active",
                tg_user_id=None,
            ),
            "eco-3": SimpleNamespace(
                id="eco-3",
                id_role=settings.economist_role_id,
                id_parent="lead-2",
                status="active",
                tg_user_id=None,
            ),
            "operator-1": SimpleNamespace(
                id="operator-1",
                id_role=settings.operator_role_id,
                id_parent="lead-1",
                status="active",
                tg_user_id=None,
            ),
            "operator-2": SimpleNamespace(
                id="operator-2",
                id_role=settings.operator_role_id,
                id_parent="lead-2",
                status="active",
                tg_user_id=None,
            ),
            "admin-1": SimpleNamespace(
                id="admin-1",
                id_role=settings.admin_role_id,
                id_parent=None,
                status="active",
                tg_user_id=None,
            ),
        }
        self._profiles = {
            user_id: SimpleNamespace(
                id=user_id,
                full_name=user_id,
                phone=None,
                mail=f"{user_id}@example.com",
            )
            for user_id in self._users
        }

    async def get_by_id(self, user_id: str):
        return self._users.get(user_id)

    async def list_users_with_profiles(self, role_id: int | None = None):
        rows = []
        for user in self._users.values():
            if role_id is not None and user.id_role != role_id:
                continue
            rows.append((user, self._profiles.get(user.id)))
        return rows

    async def list_by_role_ids_with_profiles_and_roles(self, *, role_ids: list[int]):
        rows = []
        for user in self._users.values():
            if user.id_role not in role_ids:
                continue
            role = SimpleNamespace(id=user.id_role, role=f"role-{user.id_role}")
            rows.append((user, self._profiles.get(user.id), role))
        return rows

    async def list_active_user_parent_pairs(self):
        return [
            (user.id, user.id_parent)
            for user in self._users.values()
            if user.status == "active"
        ]

    async def list_contractors(self, *, contractor_role_id: int):
        return [
            (user, self._profiles.get(user.id), None, None, None)
            for user in self._users.values()
            if user.id_role == contractor_role_id
        ]


class _EmptyUserStatusPeriodsRepo:
    async def list_active_for_users(self, *, user_ids):
        _ = user_ids
        return {}


def test_economist_users_list_defaults_to_module_scope(
    test_client,
    set_uow,
    set_current_user,
    make_current_user,
):
    uow = DummyUow()
    uow.users = _ScopedUsersRepo()
    uow.user_status_periods = object()
    set_uow(uow)
    set_current_user(
        make_current_user(
            user_id="eco-1",
            role_id=settings.economist_role_id,
            permissions={PermissionCodes.USERS_READ},
        )
    )

    response = test_client.get("/api/v1/users")

    assert response.status_code == 200
    user_ids = {item["user_id"] for item in response.json()["data"]["items"]}
    assert user_ids == {"lead-1", "eco-1", "eco-2", "operator-1"}


def test_economist_users_list_expands_to_department_scope_with_delegation(
    test_client,
    set_uow,
    set_current_user,
    make_current_user,
):
    uow = DummyUow()
    uow.users = _ScopedUsersRepo()
    uow.user_status_periods = object()
    set_uow(uow)
    set_current_user(
        make_current_user(
            user_id="eco-1",
            role_id=settings.economist_role_id,
            permissions={
                PermissionCodes.USERS_READ,
                PermissionCodes.DEPARTMENT_REQUESTS_READ,
            },
        )
    )

    response = test_client.get("/api/v1/users")

    assert response.status_code == 200
    user_ids = {item["user_id"] for item in response.json()["data"]["items"]}
    assert user_ids == {"lead-1", "lead-2", "eco-1", "eco-2", "eco-3", "operator-1", "operator-2"}


def test_project_manager_users_list_keeps_department_scope_and_leads(
    test_client,
    set_uow,
    set_current_user,
    make_current_user,
):
    uow = DummyUow()
    uow.users = _ScopedUsersRepo()
    uow.user_status_periods = object()
    set_uow(uow)
    set_current_user(
        make_current_user(
            user_id="pm-1",
            role_id=settings.project_manager_role_id,
            permissions={PermissionCodes.USERS_READ},
        )
    )

    response = test_client.get("/api/v1/users")

    assert response.status_code == 200
    user_ids = {item["user_id"] for item in response.json()["data"]["items"]}
    assert user_ids == {"lead-1", "lead-2", "eco-1", "eco-2", "eco-3", "operator-1", "operator-2"}


def test_request_economists_for_lead_default_to_descendants_only(
    test_client,
    set_uow,
    set_current_user,
    make_current_user,
):
    uow = DummyUow()
    uow.users = _ScopedUsersRepo()
    uow.user_status_periods = _EmptyUserStatusPeriodsRepo()
    set_uow(uow)
    set_current_user(
        make_current_user(
            user_id="lead-1",
            role_id=settings.lead_economist_role_id,
            permissions={PermissionCodes.REQUESTS_OWNER_CHANGE},
        )
    )

    response = test_client.get("/api/v1/users/request-economists")

    assert response.status_code == 200
    user_ids = {item["user_id"] for item in response.json()["data"]["items"]}
    assert user_ids == {"lead-1", "eco-1", "eco-2"}


def test_request_economists_for_lead_expand_to_department_scope_with_assign_delegation(
    test_client,
    set_uow,
    set_current_user,
    make_current_user,
):
    uow = DummyUow()
    uow.users = _ScopedUsersRepo()
    uow.user_status_periods = _EmptyUserStatusPeriodsRepo()
    set_uow(uow)
    set_current_user(
        make_current_user(
            user_id="lead-1",
            role_id=settings.lead_economist_role_id,
            permissions={PermissionCodes.DEPARTMENT_REQUESTS_ASSIGN},
        )
    )

    response = test_client.get("/api/v1/users/request-economists")

    assert response.status_code == 200
    user_ids = {item["user_id"] for item in response.json()["data"]["items"]}
    assert user_ids == {"lead-1", "lead-2", "eco-1", "eco-2", "eco-3"}
