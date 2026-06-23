from __future__ import annotations

from types import SimpleNamespace

from app.core.config import settings
from app.domain.permissions import PermissionCodes


class _UnitsRepo:
    def __init__(self) -> None:
        self._next_unit_id = 2
        self._units = {
            1: SimpleNamespace(id=1, name="Департамент", id_parent=None, is_active=True, id_created_by_user="superadmin-1"),
        }
        self._members = {
            (1, "admin-1"): SimpleNamespace(
                id_unit=1,
                id_user="admin-1",
                id_assigned_by_user="superadmin-1",
                is_active=True,
                updated_at=None,
            ),
        }

    async def add(self, unit) -> None:
        unit.id = self._next_unit_id
        self._next_unit_id += 1
        self._units[unit.id] = unit

    async def add_member(self, member) -> None:
        self._members[(member.id_unit, member.id_user)] = member

    async def flush(self) -> None:
        return None

    async def get_by_id(self, unit_id: int):
        return self._units.get(unit_id)

    async def get_member(self, *, unit_id: int, user_id: str):
        return self._members.get((unit_id, user_id))

    async def find_sibling_by_name(self, *, id_parent: int | None, name: str):
        for unit in self._units.values():
            if unit.id_parent == id_parent and unit.name == name:
                return unit
        return None

    async def list_units(self, *, active_only: bool = True):
        return [unit for unit in self._units.values() if unit.is_active or not active_only]

    async def list_children(self, *, unit_id: int, active_only: bool = True):
        return [
            unit
            for unit in self._units.values()
            if unit.id_parent == unit_id and (unit.is_active or not active_only)
        ]

    async def list_members(self, *, unit_id: int, active_only: bool = True):
        rows = []
        for (member_unit_id, user_id), member in self._members.items():
            if member_unit_id != unit_id or (active_only and not member.is_active):
                continue
            user = self._users[user_id]
            rows.append((member, user, self._profiles[user_id], self._roles[user.id_role]))
        return rows

    async def list_members_for_units(self, *, unit_ids: list[int], active_only: bool = True):
        rows = []
        for unit_id in unit_ids:
            rows.extend(await self.list_members(unit_id=unit_id, active_only=active_only))
        return rows

    async def list_user_units(self, *, user_id: str, active_only: bool = True):
        rows = []
        for (unit_id, member_user_id), member in self._members.items():
            if member_user_id != user_id or (active_only and not member.is_active):
                continue
            unit = self._units[unit_id]
            if active_only and not unit.is_active:
                continue
            rows.append((member, unit))
        return rows

    async def list_user_root_unit_ids(self, *, user_id: str):
        root_ids = []
        for (unit_id, member_user_id), member in self._members.items():
            unit = self._units[unit_id]
            if member_user_id == user_id and member.is_active and unit.id_parent is None and unit.is_active:
                root_ids.append(unit_id)
        return root_ids

    async def list_available_users_for_unit(self, *, unit_id: int | None = None, search: str | None = None):
        normalized_search = (search or "").strip().lower()
        rows = []
        for user in self._users.values():
            if user.status != "active":
                continue
            if unit_id is not None and (unit_id, user.id) in self._members and self._members[(unit_id, user.id)].is_active:
                continue
            profile = self._profiles.get(user.id)
            searchable = " ".join(filter(None, [user.id, getattr(profile, "full_name", None)])).lower()
            if normalized_search and normalized_search not in searchable:
                continue
            rows.append((user, profile, self._roles[user.id_role]))
        return rows

    def bind_directory(self, users, profiles, roles) -> None:
        self._users = users
        self._profiles = profiles
        self._roles = roles


class _UsersRepo:
    def __init__(self) -> None:
        self._users = {
            "superadmin-1": SimpleNamespace(id="superadmin-1", id_role=settings.superadmin_role_id, id_parent=None, status="active"),
            "admin-1": SimpleNamespace(id="admin-1", id_role=settings.admin_role_id, id_parent=None, status="active"),
            "pm-1": SimpleNamespace(id="pm-1", id_role=settings.project_manager_role_id, id_parent=None, status="active"),
            "lead-1": SimpleNamespace(id="lead-1", id_role=settings.lead_economist_role_id, id_parent="pm-1", status="active"),
            "econ-1": SimpleNamespace(id="econ-1", id_role=settings.economist_role_id, id_parent="lead-1", status="active"),
        }
        self._profiles = {}
        self._roles = {}

    async def get_by_id(self, user_id: str):
        return self._users.get(user_id)

    async def list_by_role_ids_with_profiles_and_roles(self, *, role_ids: list[int]):
        rows = []
        for user in self._users.values():
            if user.id_role not in role_ids:
                continue
            rows.append((user, self._profiles.get(user.id), self._roles[user.id_role]))
        return rows


class _UnitsUow:
    def __init__(self) -> None:
        self.users = _UsersRepo()
        self.units = _UnitsRepo()
        profiles = {
            "superadmin-1": SimpleNamespace(full_name="Суперадмин"),
            "admin-1": SimpleNamespace(full_name="Администратор отдела"),
            "pm-1": SimpleNamespace(full_name="РП 1"),
            "lead-1": SimpleNamespace(full_name="ВЭ 1"),
            "econ-1": SimpleNamespace(full_name="Экономист 1"),
        }
        roles = {
            settings.superadmin_role_id: SimpleNamespace(id=settings.superadmin_role_id, role="Суперадмин"),
            settings.admin_role_id: SimpleNamespace(id=settings.admin_role_id, role="Администратор"),
            settings.project_manager_role_id: SimpleNamespace(id=settings.project_manager_role_id, role="Руководитель проекта"),
            settings.lead_economist_role_id: SimpleNamespace(id=settings.lead_economist_role_id, role="Ведущий экономист"),
            settings.economist_role_id: SimpleNamespace(id=settings.economist_role_id, role="Экономист"),
        }
        self.units.bind_directory(self.users._users, profiles, roles)
        self.users._profiles = profiles
        self.users._roles = roles

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        _ = (exc_type, exc, tb)


def test_units_tree_requires_permission(test_client, set_uow, set_current_user, make_current_user):
    set_uow(_UnitsUow())
    set_current_user(
        make_current_user(
            user_id="admin-1",
            role_id=settings.admin_role_id,
            permissions=set(),
        )
    )

    response = test_client.get("/api/v1/units/tree")

    assert response.status_code == 403


def test_superadmin_can_create_root_unit_via_api(test_client, set_uow, set_current_user, make_current_user):
    set_uow(_UnitsUow())
    set_current_user(
        make_current_user(
            user_id="superadmin-1",
            role_id=settings.superadmin_role_id,
            permissions={
                PermissionCodes.UNITS_READ,
                PermissionCodes.UNITS_CREATE,
                PermissionCodes.UNITS_UPDATE,
                PermissionCodes.UNITS_MEMBERS_MANAGE,
            },
        )
    )

    response = test_client.post("/api/v1/units", json={"name": "Новый департамент"})

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Новый департамент"
    assert response.json()["data"]["id_parent"] is None


def test_superadmin_can_load_recommended_units_tree(test_client, set_uow, set_current_user, make_current_user):
    set_uow(_UnitsUow())
    set_current_user(
        make_current_user(
            user_id="superadmin-1",
            role_id=settings.superadmin_role_id,
            permissions={PermissionCodes.UNITS_READ},
        )
    )

    response = test_client.get("/api/v1/units/recommended-tree")

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert [item["user_id"] for item in items] == ["admin-1", "pm-1"]
    assert items[1]["children"][0]["user_id"] == "lead-1"


def test_admin_can_load_global_available_users_for_unit_creation(test_client, set_uow, set_current_user, make_current_user):
    set_uow(_UnitsUow())
    set_current_user(
        make_current_user(
            user_id="admin-1",
            role_id=settings.admin_role_id,
            permissions={
                PermissionCodes.UNITS_READ,
                PermissionCodes.UNITS_CREATE,
                PermissionCodes.UNITS_UPDATE,
                PermissionCodes.UNITS_MEMBERS_MANAGE,
            },
        )
    )

    response = test_client.get("/api/v1/units/available-users", params={"search": "econ"})

    assert response.status_code == 200
    assert [item["user_id"] for item in response.json()["data"]["items"]] == ["econ-1"]
