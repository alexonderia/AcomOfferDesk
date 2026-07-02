from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.domain.exceptions import Conflict, Forbidden
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
            "contractor-1": User(
                id="contractor-1",
                id_role=settings.contractor_role_id,
                id_parent=None,
                status="active",
            ),
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
            settings.contractor_role_id: Role(id=settings.contractor_role_id, role="Контрагент"),
        }
        self.profiles = {
            "superadmin-1": Profile(id="superadmin-1", full_name="Суперадмин", phone=None, mail=None),
            "admin-1": Profile(id="admin-1", full_name="Администратор отдела", phone=None, mail=None),
            "pm-1": Profile(id="pm-1", full_name="РП 1", phone=None, mail=None),
            "lead-1": Profile(id="lead-1", full_name="ВЭ 1", phone=None, mail=None),
            "econ-1": Profile(id="econ-1", full_name="Экономист 1", phone=None, mail=None),
            "econ-2": Profile(id="econ-2", full_name="Экономист 2", phone=None, mail=None),
            "contractor-1": Profile(id="contractor-1", full_name="Контрагент 1", phone=None, mail=None),
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
        root_ids: set[int] = set()
        for _member, unit in await self.list_user_units(user_id=user_id, active_only=True):
            current = unit
            seen: set[int] = set()
            while current.id_parent is not None and int(current.id) not in seen:
                seen.add(int(current.id))
                parent = self.units.get(int(current.id_parent))
                if parent is None:
                    break
                current = parent
            root_ids.add(int(current.id))
        return sorted(root_ids)

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

    async def list_active_units():
        return [
            (int(unit.id), int(unit.id_parent) if unit.id_parent is not None else None)
            for unit in units.units.values()
            if unit.is_active
        ]

    async def list_active_unit_details():
        return [
            (int(unit.id), unit.name, int(unit.id_parent) if unit.id_parent is not None else None)
            for unit in units.units.values()
            if unit.is_active
        ]

    async def list_active_unit_memberships():
        return [
            (member_user_id, unit_id)
            for (unit_id, member_user_id), member in units.members.items()
            if member.is_active
        ]

    users.list_active_units = list_active_units
    users.list_active_unit_details = list_active_unit_details
    users.list_active_unit_memberships = list_active_unit_memberships

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

    assert [row.user_id for row in rows] == ["econ-1"]


@pytest.mark.asyncio
async def test_available_users_exclude_contractors(service_context, make_current_user) -> None:
    rows = await service_context.service.list_available_users_for_unit(
        current_user=make_current_user(
            user_id="admin-1",
            role_id=settings.admin_role_id,
            permissions={"units.create", "units.read", "units.update", "units.members.manage"},
        ),
        unit_id=None,
    )

    assert "contractor-1" not in [row.user_id for row in rows]


@pytest.mark.asyncio
async def test_admin_available_users_are_scoped_to_own_department_and_exclude_superadmin(
    service_context,
    make_current_user,
) -> None:
    service_context.users.users["pm-foreign"] = User(
        id="pm-foreign",
        id_role=settings.project_manager_role_id,
        id_parent=None,
        status="active",
    )
    service_context.units.profiles["pm-foreign"] = Profile(
        id="pm-foreign",
        full_name="РП вне департамента",
        phone=None,
        mail=None,
    )
    service_context.units.units[4] = Unit(
        id=4,
        name="Департамент B",
        id_parent=None,
        is_active=True,
        id_created_by_user="superadmin-1",
    )
    service_context.units.members[(4, "pm-foreign")] = UnitMember(
        id_unit=4,
        id_user="pm-foreign",
        id_assigned_by_user="superadmin-1",
        is_active=True,
    )
    service_context.units.members[(1, "superadmin-1")] = UnitMember(
        id_unit=1,
        id_user="superadmin-1",
        id_assigned_by_user="superadmin-1",
        is_active=True,
    )

    rows = await service_context.service.list_available_users_for_unit(
        current_user=make_current_user(
            user_id="admin-1",
            role_id=settings.admin_role_id,
            permissions={"units.create", "units.read", "units.update", "units.members.manage"},
        ),
        unit_id=None,
    )

    visible_ids = [row.user_id for row in rows]
    assert "econ-1" in visible_ids
    assert "pm-foreign" not in visible_ids
    assert "superadmin-1" not in visible_ids


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
async def test_add_member_rejects_contractors(service_context, make_current_user) -> None:
    with pytest.raises(Conflict, match="Контрагентов нельзя назначать"):
        await service_context.service.add_member(
            current_user=make_current_user(
                user_id="admin-1",
                role_id=settings.admin_role_id,
                permissions={"units.create", "units.read", "units.update", "units.members.manage"},
            ),
            unit_id=1,
            user_id="contractor-1",
        )


@pytest.mark.asyncio
async def test_admin_cannot_add_superadmin_to_unit(service_context, make_current_user) -> None:
    with pytest.raises(Forbidden, match="Суперадмина нельзя привязывать"):
        await service_context.service.add_member(
            current_user=make_current_user(
                user_id="admin-1",
                role_id=settings.admin_role_id,
                permissions={"units.create", "units.read", "units.update", "units.members.manage"},
            ),
            unit_id=1,
            user_id="superadmin-1",
        )


@pytest.mark.asyncio
async def test_admin_cannot_remove_superadmin_from_unit(service_context, make_current_user) -> None:
    service_context.units.members[(1, "superadmin-1")] = UnitMember(
        id_unit=1,
        id_user="superadmin-1",
        id_assigned_by_user="superadmin-1",
        is_active=True,
    )

    with pytest.raises(Forbidden, match="Суперадмина нельзя привязывать"):
        await service_context.service.remove_member(
            current_user=make_current_user(
                user_id="admin-1",
                role_id=settings.admin_role_id,
                permissions={"units.create", "units.read", "units.update", "units.members.manage"},
            ),
            unit_id=1,
            user_id="superadmin-1",
        )


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
    assert tree[0].members[0].id_parent_user is None
    assert tree[0].children[0].name == "Проект"
    assert tree[0].children[0].members[0].user_id == "econ-1"
    assert tree[0].children[0].members[0].id_parent_user is None


@pytest.mark.asyncio
async def test_get_tree_for_user_hierarchy_returns_all_assigned_department_roots(
    service_context,
    make_current_user,
) -> None:
    service_context.units.members[(1, "pm-1")] = UnitMember(
        id_unit=1,
        id_user="pm-1",
        id_assigned_by_user="superadmin-1",
        is_active=True,
    )
    service_context.units.units[4] = Unit(
        id=4,
        name="Департамент B",
        id_parent=None,
        is_active=True,
        id_created_by_user="superadmin-1",
    )
    service_context.units.units[5] = Unit(
        id=5,
        name="Проект B",
        id_parent=4,
        is_active=True,
        id_created_by_user="superadmin-1",
    )
    service_context.units.members[(5, "econ-1")] = UnitMember(
        id_unit=5,
        id_user="econ-1",
        id_assigned_by_user="admin-1",
        is_active=True,
    )

    viewer_tree = await service_context.service.get_tree(
        current_user=make_current_user(
            user_id="pm-1",
            role_id=settings.project_manager_role_id,
            permissions={"units.read"},
        ),
    )
    subject_tree = await service_context.service.get_tree_for_user_hierarchy(
        current_user=make_current_user(
            user_id="pm-1",
            role_id=settings.project_manager_role_id,
            permissions={"units.read"},
        ),
        target_user_id="econ-1",
    )

    assert [item.unit_id for item in viewer_tree] == [1]
    assert sorted(item.unit_id for item in subject_tree) == [1, 4]


@pytest.mark.asyncio
async def test_internal_employee_can_view_attached_root_hierarchy(service_context, make_current_user) -> None:
    tree = await service_context.service.get_tree(
        current_user=make_current_user(
            user_id="econ-1",
            role_id=settings.economist_role_id,
            permissions={"units.read"},
        ),
    )

    assert len(tree) == 1
    assert tree[0].unit_id == 1
    assert tree[0].children[0].unit_id == 2


@pytest.mark.asyncio
async def test_get_recommended_tree_returns_current_user_hierarchy(service_context, make_current_user) -> None:
    tree = await service_context.service.get_recommended_tree(
        current_user=make_current_user(
            user_id="superadmin-1",
            role_id=settings.superadmin_role_id,
            permissions={"units.read"},
        ),
    )

    assert [node.user_id for node in tree] == ["admin-1", "pm-1", "lead-1", "econ-1", "econ-2"]
    assert all(node.children == [] for node in tree)


def _flatten_recommended_ids(nodes) -> list[str]:
    flattened: list[str] = []
    for node in nodes:
        flattened.append(node.user_id)
        flattened.extend(_flatten_recommended_ids(node.children))
    return flattened


@pytest.mark.asyncio
async def test_get_recommended_tree_scopes_admin_to_responsibility_zone(service_context, make_current_user) -> None:
    # A user without a unit no longer inherits visibility through legacy parent chains.
    service_context.users.users["econ-3"] = User(
        id="econ-3",
        id_role=settings.economist_role_id,
        id_parent="econ-1",
        status="active",
    )
    service_context.units.profiles["econ-3"] = Profile(id="econ-3", full_name="Экономист 3", phone=None, mail=None)

    tree = await service_context.service.get_recommended_tree(
        current_user=make_current_user(
            user_id="admin-1",
            role_id=settings.admin_role_id,
            permissions={"units.read"},
        ),
    )

    visible_ids = _flatten_recommended_ids(tree)
    assert sorted(visible_ids) == ["admin-1", "econ-1"]
    assert "pm-1" not in visible_ids
    assert "lead-1" not in visible_ids
    assert "econ-2" not in visible_ids
    assert "econ-3" not in visible_ids
    assert all(node.children == [] for node in tree)


@pytest.mark.asyncio
async def test_assign_to_module_does_not_inherit_manager_root_unit(service_context, make_current_user) -> None:
    # Subordinate of admin-1 (who is a member of the root department "Департамент").
    service_context.users.users["sub-1"] = User(
        id="sub-1",
        id_role=settings.economist_role_id,
        id_parent="admin-1",
        status="active",
    )
    service_context.units.profiles["sub-1"] = Profile(id="sub-1", full_name="Подчиненный", phone=None, mail=None)

    await service_context.service.add_member(
        current_user=make_current_user(
            user_id="admin-1",
            role_id=settings.admin_role_id,
            permissions={"units.create", "units.read", "units.update", "units.members.manage"},
        ),
        unit_id=2,  # "Проект" — a sub-unit whose root is "Департамент" (id=1)
        user_id="sub-1",
    )

    assert service_context.units.members[(2, "sub-1")].is_active is True
    assert (1, "sub-1") not in service_context.units.members


@pytest.mark.asyncio
async def test_assign_to_module_skips_inheritance_without_manager_unit(service_context, make_current_user) -> None:
    # Subordinate of lead-1, who is not a member of any unit.
    service_context.users.users["sub-2"] = User(
        id="sub-2",
        id_role=settings.economist_role_id,
        id_parent="lead-1",
        status="active",
    )
    service_context.units.profiles["sub-2"] = Profile(id="sub-2", full_name="Подчиненный 2", phone=None, mail=None)

    await service_context.service.add_member(
        current_user=make_current_user(
            user_id="admin-1",
            role_id=settings.admin_role_id,
            permissions={"units.create", "units.read", "units.update", "units.members.manage"},
        ),
        unit_id=2,
        user_id="sub-2",
    )

    assert service_context.units.members[(2, "sub-2")].is_active is True
    assert (1, "sub-2") not in service_context.units.members


@pytest.mark.asyncio
async def test_update_unit_can_reparent_within_same_department(service_context, make_current_user) -> None:
    service_context.units.units[4] = Unit(
        id=4,
        name="Отдел",
        id_parent=1,
        is_active=True,
        id_created_by_user="superadmin-1",
    )

    updated = await service_context.service.update_unit(
        current_user=make_current_user(
            user_id="admin-1",
            role_id=settings.admin_role_id,
            permissions={"units.read", "units.update"},
        ),
        unit_id=3,
        id_parent=4,
    )

    assert updated.id_parent == 4
    assert service_context.units.units[3].id_parent == 4


@pytest.mark.asyncio
async def test_delete_unit_requires_confirmation_when_members_or_children_exist(service_context, make_current_user) -> None:
    with pytest.raises(Conflict, match="Подтвердите перенос"):
        await service_context.service.delete_unit(
            current_user=make_current_user(
                user_id="admin-1",
                role_id=settings.admin_role_id,
                permissions={"units.read", "units.update", "units.members.manage"},
            ),
            unit_id=2,
            confirm_reassign=False,
        )


@pytest.mark.asyncio
async def test_delete_unit_reassigns_direct_members_and_children_to_parent(service_context, make_current_user) -> None:
    service_context.units.members[(3, "econ-2")] = UnitMember(
        id_unit=3,
        id_user="econ-2",
        id_assigned_by_user="admin-1",
        is_active=True,
    )

    await service_context.service.delete_unit(
        current_user=make_current_user(
            user_id="admin-1",
            role_id=settings.admin_role_id,
            permissions={"units.read", "units.update", "units.members.manage"},
        ),
        unit_id=2,
        confirm_reassign=True,
    )

    assert service_context.units.units[2].is_active is False
    assert service_context.units.units[2].name.endswith("[archived:2]")
    assert service_context.units.units[3].id_parent == 1
    assert service_context.units.members[(2, "econ-1")].is_active is False
    assert service_context.units.members[(1, "econ-1")].is_active is True
    assert service_context.units.members[(3, "econ-2")].is_active is True


@pytest.mark.asyncio
async def test_lead_economist_can_manage_own_subtree(service_context, make_current_user) -> None:
    service_context.units.members[(2, "lead-1")] = UnitMember(
        id_unit=2,
        id_user="lead-1",
        id_assigned_by_user="admin-1",
        is_active=True,
    )
    lead_user = make_current_user(
        user_id="lead-1",
        role_id=settings.lead_economist_role_id,
        permissions={"units.read", "units.create", "units.update", "units.members.manage"},
    )

    created = await service_context.service.create_unit(
        current_user=lead_user,
        name="Подгруппа",
        id_parent=2,
    )
    assert created.name == "Подгруппа"

    tree = await service_context.service.get_tree(current_user=lead_user)
    project_node = next(node for node in tree[0].children if node.unit_id == 2)
    module_node = next(child for child in project_node.children if child.unit_id == 3)
    assert project_node.actions.can_manage_members is True
    assert module_node.actions.can_manage_members is True
    assert tree[0].actions.can_manage_members is False


@pytest.mark.asyncio
async def test_lead_economist_cannot_manage_outside_subtree(service_context, make_current_user) -> None:
    service_context.units.members[(2, "lead-1")] = UnitMember(
        id_unit=2,
        id_user="lead-1",
        id_assigned_by_user="admin-1",
        is_active=True,
    )
    lead_user = make_current_user(
        user_id="lead-1",
        role_id=settings.lead_economist_role_id,
        permissions={"units.read", "units.create", "units.update", "units.members.manage"},
    )

    with pytest.raises(Forbidden):
        await service_context.service.create_unit(
            current_user=lead_user,
            name="Чужая ветка",
            id_parent=1,
        )
