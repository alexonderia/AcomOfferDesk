from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.domain.exceptions import Conflict
from app.models.orm_models import Profile, Role, Unit, UnitMember, User
from app.services.units import UnitService


class _FakeUsersRepo:
    def __init__(self) -> None:
        self.users = {
            "superadmin-1": User(id="superadmin-1", id_role=settings.superadmin_role_id, id_parent=None, status="active"),
            "admin-1": User(id="admin-1", id_role=settings.admin_role_id, id_parent=None, status="active"),
            "pm-1": User(id="pm-1", id_role=settings.project_manager_role_id, id_parent=None, status="active"),
            "lead-1": User(id="lead-1", id_role=settings.lead_economist_role_id, id_parent="pm-1", status="active"),
            "econ-1": User(id="econ-1", id_role=settings.economist_role_id, id_parent="lead-1", status="active"),
            "econ-2": User(id="econ-2", id_role=settings.economist_role_id, id_parent="lead-1", status="active"),
        }
        self._profiles: dict[str, Profile] = {}
        self._roles: dict[int, Role] = {}

    async def get_by_id(self, user_id: str) -> User | None:
        return self.users.get(user_id)

    async def list_by_role_ids_with_profiles_and_roles(self, *, role_ids: list[int]):
        rows = []
        for user in self.users.values():
            if user.id_role not in role_ids:
                continue
            profile = self._profiles.get(user.id)
            role = self._roles[user.id_role]
            rows.append((user, profile, role))
        return sorted(rows, key=lambda row: (row[2].id, row[1].full_name if row[1] is not None else "", row[0].id))


class _FakeUnitsRepo:
    def __init__(self, users_repo: _FakeUsersRepo) -> None:
        self._users_repo = users_repo
        self._next_unit_id = 4
        self.roles = {
            settings.superadmin_role_id: Role(id=settings.superadmin_role_id, role="Суперадмин"),
            settings.admin_role_id: Role(id=settings.admin_role_id, role="Администратор"),
            settings.project_manager_role_id: Role(id=settings.project_manager_role_id, role="Руководитель проекта"),
            settings.lead_economist_role_id: Role(id=settings.lead_economist_role_id, role="Ведущий экономист"),
            settings.economist_role_id: Role(id=settings.economist_role_id, role="Экономист"),
        }
        self.profiles = {
            "superadmin-1": Profile(id="superadmin-1", full_name="Суперадмин", phone=None, mail=None),
            "admin-1": Profile(id="admin-1", full_name="Администратор отдела", phone=None, mail=None),
            "pm-1": Profile(id="pm-1", full_name="РП 1", phone=None, mail=None),
            "lead-1": Profile(id="lead-1", full_name="ВЭ 1", phone=None, mail=None),
            "econ-1": Profile(id="econ-1", full_name="Экономист 1", phone=None, mail=None),
            "econ-2": Profile(id="econ-2", full_name="Экономист 2", phone=None, mail=None),
        }
        self.units = {
            1: Unit(id=1, name="Департамент", id_parent=None, is_active=True, id_created_by_user="superadmin-1"),
            2: Unit(id=2, name="Проект", id_parent=1, is_active=True, id_created_by_user="superadmin-1"),
            3: Unit(id=3, name="Модуль", id_parent=2, is_active=True, id_created_by_user="superadmin-1"),
        }
        self.members = {
            (1, "admin-1"): UnitMember(id_unit=1, id_user="admin-1", id_assigned_by_user="superadmin-1", is_active=True),
            (2, "econ-1"): UnitMember(id_unit=2, id_user="econ-1", id_assigned_by_user="admin-1", is_active=True),
        }

    async def add(self, unit: Unit) -> None:
        if getattr(unit, "id", None) is None:
            unit.id = self._next_unit_id
            self._next_unit_id += 1
        self.units[int(unit.id)] = unit

    async def add_member(self, member: UnitMember) -> None:
        self.members[(int(member.id_unit), member.id_user)] = member

    async def flush(self) -> None:
        return None

    async def get_by_id(self, unit_id: int) -> Unit | None:
        return self.units.get(unit_id)

    async def get_member(self, *, unit_id: int, user_id: str) -> UnitMember | None:
        return self.members.get((unit_id, user_id))

    async def find_sibling_by_name(self, *, id_parent: int | None, name: str) -> Unit | None:
        for unit in self.units.values():
            if unit.name == name and unit.id_parent == id_parent:
                return unit
        return None

    async def list_units(self, *, active_only: bool = True) -> list[Unit]:
        units = [unit for unit in self.units.values() if (unit.is_active or not active_only)]
        return sorted(units, key=lambda item: ((item.id_parent is not None), item.id_parent or 0, item.name, item.id))

    async def list_children(self, *, unit_id: int, active_only: bool = True) -> list[Unit]:
        children = [
            unit
            for unit in self.units.values()
            if unit.id_parent == unit_id and (unit.is_active or not active_only)
        ]
        return sorted(children, key=lambda item: (item.name, item.id))

    async def list_members(
        self,
        *,
        unit_id: int,
        active_only: bool = True,
    ) -> list[tuple[UnitMember, User, Profile | None, Role]]:
        rows = []
        for (member_unit_id, member_user_id), member in self.members.items():
            if member_unit_id != unit_id:
                continue
            if active_only and not member.is_active:
                continue
            user = self._users_repo.users[member_user_id]
            profile = self.profiles.get(member_user_id)
            role = self.roles[user.id_role]
            rows.append((member, user, profile, role))
        return sorted(rows, key=lambda row: (row[3].id, row[1].id))

    async def list_members_for_units(
        self,
        *,
        unit_ids: list[int],
        active_only: bool = True,
    ) -> list[tuple[UnitMember, User, Profile | None, Role]]:
        rows: list[tuple[UnitMember, User, Profile | None, Role]] = []
        for unit_id in unit_ids:
            rows.extend(await self.list_members(unit_id=unit_id, active_only=active_only))
        return rows

    async def list_user_units(
        self,
        *,
        user_id: str,
        active_only: bool = True,
    ) -> list[tuple[UnitMember, Unit]]:
        rows = []
        for (unit_id, member_user_id), member in self.members.items():
            if member_user_id != user_id:
                continue
            unit = self.units[unit_id]
            if active_only and (not member.is_active or not unit.is_active):
                continue
            rows.append((member, unit))
        return rows

    async def list_user_root_unit_ids(self, *, user_id: str) -> list[int]:
        unit_ids: list[int] = []
        for (unit_id, member_user_id), member in self.members.items():
            if member_user_id != user_id or not member.is_active:
                continue
            unit = self.units[unit_id]
            if unit.is_active and unit.id_parent is None:
                unit_ids.append(unit_id)
        return sorted(unit_ids)

    async def list_available_users_for_unit(
        self,
        *,
        unit_id: int | None = None,
        search: str | None = None,
    ) -> list[tuple[User, Profile | None, Role]]:
        normalized_search = (search or "").strip().lower()
        assigned_user_ids = {
            user_id
            for (member_unit_id, user_id), member in self.members.items()
            if unit_id is not None and member_unit_id == unit_id and member.is_active
        }
        rows = []
        for user in self._users_repo.users.values():
            if user.status != "active" or user.id in assigned_user_ids:
                continue
            profile = self.profiles.get(user.id)
            role = self.roles[user.id_role]
            searchable = " ".join(filter(None, [user.id, profile.full_name if profile else None])).lower()
            if normalized_search and normalized_search not in searchable:
                continue
            rows.append((user, profile, role))
        return sorted(rows, key=lambda row: (row[2].id, row[0].id))


@pytest.fixture
def service_context():
    users = _FakeUsersRepo()
    units = _FakeUnitsRepo(users)
    users._profiles = units.profiles
    users._roles = units.roles
    service = UnitService(units, users)
    return SimpleNamespace(service=service, users=users, units=units)


@pytest.mark.asyncio
async def test_superadmin_can_create_root_unit(service_context, make_current_user) -> None:
    created = await service_context.service.create_unit(
        current_user=make_current_user(
            user_id="superadmin-1",
            role_id=settings.superadmin_role_id,
            permissions={"units.create", "units.read", "units.update", "units.members.manage"},
        ),
        name="Новый департамент",
        id_parent=None,
    )

    assert created.id_parent is None
    assert created.name == "Новый департамент"
    assert created.actions.can_create_child is True


@pytest.mark.asyncio
async def test_admin_can_create_child_unit_inside_assigned_root(service_context, make_current_user) -> None:
    created = await service_context.service.create_unit(
        current_user=make_current_user(
            user_id="admin-1",
            role_id=settings.admin_role_id,
            permissions={"units.create", "units.read", "units.update", "units.members.manage"},
        ),
        name="Проект 2",
        id_parent=1,
    )

    assert created.id_parent == 1
    assert created.name == "Проект 2"


@pytest.mark.asyncio
async def test_duplicate_sibling_name_is_rejected(service_context, make_current_user) -> None:
    with pytest.raises(Conflict, match="существует"):
        await service_context.service.create_unit(
            current_user=make_current_user(
                user_id="admin-1",
                role_id=settings.admin_role_id,
                permissions={"units.create", "units.read", "units.update", "units.members.manage"},
            ),
            name="Проект",
            id_parent=1,
        )


@pytest.mark.asyncio
async def test_add_member_and_prevent_duplicate_membership(service_context, make_current_user) -> None:
    current_user = make_current_user(
        user_id="admin-1",
        role_id=settings.admin_role_id,
        permissions={"units.create", "units.read", "units.update", "units.members.manage"},
    )

    created_member = await service_context.service.add_member(
        current_user=current_user,
        unit_id=1,
        user_id="econ-2",
    )

    assert created_member.user_id == "econ-2"
    assert created_member.role_id == settings.economist_role_id

    with pytest.raises(Conflict, match="уже добавлен"):
        await service_context.service.add_member(
            current_user=current_user,
            unit_id=1,
            user_id="econ-2",
        )


@pytest.mark.asyncio
async def test_admin_can_list_available_users_without_target_unit(service_context, make_current_user) -> None:
    rows = await service_context.service.list_available_users_for_unit(
        current_user=make_current_user(
            user_id="admin-1",
            role_id=settings.admin_role_id,
            permissions={"units.create", "units.read", "units.update", "units.members.manage"},
        ),
        unit_id=None,
        search="econ",
    )

    assert [row.user_id for row in rows] == ["econ-1", "econ-2"]


@pytest.mark.asyncio
async def test_remove_member_deactivates_membership(service_context, make_current_user) -> None:
    current_user = make_current_user(
        user_id="admin-1",
        role_id=settings.admin_role_id,
        permissions={"units.create", "units.read", "units.update", "units.members.manage"},
    )

    await service_context.service.remove_member(
        current_user=current_user,
        unit_id=2,
        user_id="econ-1",
    )

    assert service_context.units.members[(2, "econ-1")].is_active is False


@pytest.mark.asyncio
async def test_get_tree_returns_units_with_members(service_context, make_current_user) -> None:
    tree = await service_context.service.get_tree(
        current_user=make_current_user(
            user_id="superadmin-1",
            role_id=settings.superadmin_role_id,
            permissions={"units.create", "units.read", "units.update", "units.members.manage"},
        ),
    )

    assert len(tree) == 1
    assert tree[0].name == "Департамент"
    assert tree[0].members[0].user_id == "admin-1"
    assert tree[0].children[0].name == "Проект"
    assert tree[0].children[0].members[0].user_id == "econ-1"


@pytest.mark.asyncio
async def test_get_recommended_tree_returns_current_user_hierarchy(service_context, make_current_user) -> None:
    tree = await service_context.service.get_recommended_tree(
        current_user=make_current_user(
            user_id="superadmin-1",
            role_id=settings.superadmin_role_id,
            permissions={"units.read"},
        ),
    )

    assert len(tree) == 2
    assert tree[0].user_id == "admin-1"
    assert tree[1].user_id == "pm-1"
    assert tree[1].children[0].user_id == "lead-1"
    assert [child.user_id for child in tree[1].children[0].children] == ["econ-1", "econ-2"]
