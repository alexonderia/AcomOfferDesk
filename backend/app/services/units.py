from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.exceptions import Conflict, Forbidden, NotFound
from app.domain.policies import UserPolicy
from app.models.orm_models import Unit, UnitMember, User
from app.repositories.units import UnitRepository
from app.repositories.users import UserRepository
from app.services.unit_hierarchy import UnitHierarchyService


_HIERARCHY_MANAGE_ROLE_IDS = frozenset(
    {
        settings.project_manager_role_id,
        settings.lead_economist_role_id,
        settings.economist_role_id,
    }
)


def _utcnow_naive() -> datetime:
    return datetime.utcnow()


def _archived_unit_name(name: str, unit_id: int) -> str:
    suffix = f" [archived:{unit_id}]"
    trimmed_name = name[: max(1, 255 - len(suffix))].rstrip()
    return f"{trimmed_name}{suffix}"


@dataclass(frozen=True, slots=True)
class UnitActionsState:
    can_create_child: bool
    can_update: bool
    can_delete: bool
    can_manage_members: bool


@dataclass(frozen=True, slots=True)
class UnitMemberState:
    user_id: str
    full_name: str | None
    role_id: int
    role_name: str
    status: str
    id_parent_user: str | None


@dataclass(frozen=True, slots=True)
class AvailableUnitUserState:
    user_id: str
    full_name: str | None
    role_id: int
    role_name: str
    status: str


@dataclass(frozen=True, slots=True)
class UnitNodeState:
    unit_id: int
    name: str
    id_parent: int | None
    is_active: bool
    members: list[UnitMemberState]
    children: list["UnitNodeState"]
    actions: UnitActionsState


@dataclass(frozen=True, slots=True)
class RecommendedHierarchyNodeState:
    user_id: str
    full_name: str | None
    role_id: int
    role_name: str
    status: str
    id_parent_user: str | None
    children: list["RecommendedHierarchyNodeState"]


class UnitService:
    def __init__(self, units: UnitRepository, users: UserRepository):
        self._units = units
        self._users = users

    def _is_superadmin(self, current_user: CurrentUser) -> bool:
        return current_user.role_id == settings.superadmin_role_id

    async def _list_manageable_root_ids(self, *, current_user: CurrentUser) -> set[int]:
        if self._is_superadmin(current_user):
            roots = await self._units.list_units(active_only=True)
            return {int(unit.id) for unit in roots if unit.id_parent is None}
        if current_user.role_id != settings.admin_role_id:
            return set()
        return set(await self._units.list_user_root_unit_ids(user_id=current_user.user_id))

    def _uses_hierarchy_scoped_management(self, current_user: CurrentUser) -> bool:
        return current_user.role_id in _HIERARCHY_MANAGE_ROLE_IDS

    async def _get_hierarchy_manageable_unit_ids(self, *, current_user: CurrentUser) -> set[int]:
        if not self._uses_hierarchy_scoped_management(current_user):
            return set()
        return await UnitHierarchyService(self._users).get_registration_assignable_unit_ids(
            user_id=current_user.user_id,
        )

    async def _can_manage_unit_for_user(self, *, current_user: CurrentUser, unit: Unit) -> bool:
        if not unit.is_active:
            return False
        if self._is_superadmin(current_user):
            return True
        if current_user.role_id == settings.admin_role_id:
            manageable_root_ids = await self._list_manageable_root_ids(current_user=current_user)
            root_unit_id = await self._resolve_root_unit_id(unit=unit)
            return root_unit_id in manageable_root_ids
        if self._uses_hierarchy_scoped_management(current_user):
            manageable_unit_ids = await self._get_hierarchy_manageable_unit_ids(current_user=current_user)
            return int(unit.id) in manageable_unit_ids
        return False

    async def _ensure_member_assignable_by_current_user(
        self,
        *,
        current_user: CurrentUser,
        user_id: str,
    ) -> None:
        if self._is_superadmin(current_user) or current_user.role_id == settings.admin_role_id:
            return
        if not self._uses_hierarchy_scoped_management(current_user):
            return
        visible_user_ids = await UnitHierarchyService(self._users).get_visible_user_ids(
            current_user=current_user,
        )
        if visible_user_ids is not None and user_id not in visible_user_ids:
            raise Forbidden("Недостаточно прав для управления этим сотрудником")

    async def _resolve_root_unit_id(self, *, unit: Unit) -> int:
        cursor = unit
        visited: set[int] = set()
        while cursor.id_parent is not None:
            cursor_id = int(cursor.id)
            if cursor_id in visited:
                raise Conflict("Обнаружен цикл в иерархии юнитов")
            visited.add(cursor_id)
            parent = await self._units.get_by_id(int(cursor.id_parent))
            if parent is None:
                raise Conflict("У юнита отсутствует родительский узел")
            cursor = parent
        return int(cursor.id)

    async def _get_unit_depth(self, *, unit: Unit) -> int:
        depth = 0
        cursor = unit
        visited: set[int] = set()
        while cursor.id_parent is not None:
            cursor_id = int(cursor.id)
            if cursor_id in visited:
                raise Conflict("Обнаружен цикл в иерархии юнитов")
            visited.add(cursor_id)
            parent = await self._units.get_by_id(int(cursor.id_parent))
            if parent is None:
                raise Conflict("У юнита отсутствует родительский узел")
            depth += 1
            cursor = parent
        return depth

    async def _ensure_read_access(self, *, current_user: CurrentUser) -> set[int]:
        UserPolicy.ensure_can_read_units(current_user)
        if self._is_superadmin(current_user):
            return await self._list_manageable_root_ids(current_user=current_user)
        if current_user.role_id == settings.admin_role_id:
            return await self._list_manageable_root_ids(current_user=current_user)
        return set(await self._units.list_user_root_unit_ids(user_id=current_user.user_id))

    async def _ensure_read_scope_for_unit(self, *, current_user: CurrentUser, unit: Unit) -> set[int]:
        readable_root_ids = await self._ensure_read_access(current_user=current_user)
        if self._is_superadmin(current_user):
            return readable_root_ids
        root_unit_id = await self._resolve_root_unit_id(unit=unit)
        if root_unit_id not in readable_root_ids:
            raise Forbidden("Недостаточно прав для просмотра этого подразделения")
        return readable_root_ids

    async def _ensure_manage_access(self, *, current_user: CurrentUser, unit: Unit) -> None:
        if await self._can_manage_unit_for_user(current_user=current_user, unit=unit):
            return
        raise Forbidden("Недостаточно прав для управления этим подразделением")

    async def _ensure_unique_name(
        self,
        *,
        id_parent: int | None,
        name: str,
        exclude_unit_id: int | None = None,
    ) -> None:
        sibling = await self._units.find_sibling_by_name(id_parent=id_parent, name=name)
        if sibling is None:
            return
        if exclude_unit_id is not None and int(sibling.id) == exclude_unit_id:
            return
        raise Conflict("Юнит с таким названием уже существует на этом уровне")

    def _build_member_state(self, *, user, profile, role, manager_user_id: str | None = None) -> UnitMemberState:
        return UnitMemberState(
            user_id=user.id,
            full_name=profile.full_name if profile is not None else None,
            role_id=int(role.id),
            role_name=role.role,
            status=user.status,
            id_parent_user=manager_user_id,
        )

    def _build_available_user_state(self, *, user, profile, role) -> AvailableUnitUserState:
        return AvailableUnitUserState(
            user_id=user.id,
            full_name=profile.full_name if profile is not None else None,
            role_id=int(role.id),
            role_name=role.role,
            status=user.status,
        )

    async def _filter_available_internal_rows_for_current_user(
        self,
        *,
        current_user: CurrentUser,
        rows: list[tuple],
    ) -> list[tuple]:
        if self._is_superadmin(current_user):
            return rows

        if current_user.role_id == settings.admin_role_id:
            # Admins manage units only inside their department, but may assign any
            # internal employee to those units, including staff from other roots.
            return [
                row
                for row in rows
                if row[0].id_role not in {
                    settings.contractor_role_id,
                    settings.superadmin_role_id,
                }
            ]

        visible_user_ids = await UnitHierarchyService(self._users).get_visible_user_ids(
            current_user=current_user,
        )
        return [
            row
            for row in rows
            if row[0].id in visible_user_ids
            and row[0].id_role not in {
                settings.contractor_role_id,
                settings.superadmin_role_id,
            }
        ]

    def _ensure_non_superadmin_binding_target(self, *, current_user: CurrentUser, user: User) -> None:
        if self._is_superadmin(current_user):
            return
        if user.id_role == settings.superadmin_role_id:
            raise Forbidden("Суперадмина нельзя привязывать к юнитам или убирать из них")

    def _build_recommended_hierarchy_node_state(
        self,
        *,
        user,
        profile,
        role,
        manager_user_id: str | None,
        children,
    ) -> RecommendedHierarchyNodeState:
        return RecommendedHierarchyNodeState(
            user_id=user.id,
            full_name=profile.full_name if profile is not None else None,
            role_id=int(role.id),
            role_name=role.role,
            status=user.status,
            id_parent_user=manager_user_id,
            children=children,
        )

    async def _build_member_states(self, *, rows: list[tuple[UnitMember, User, object | None, object]]) -> list[UnitMemberState]:
        if not rows:
            return []

        hierarchy = UnitHierarchyService(self._users)
        visible_user_ids = {user.id for _member, user, _profile, _role in rows}
        parent_by_user_id: dict[str, str | None] = {}
        for user_id in visible_user_ids:
            manager = await hierarchy.get_primary_manager(
                user_id=user_id,
                visible_user_ids=visible_user_ids,
            )
            parent_by_user_id[user_id] = manager.user_id if manager is not None else None

        return [
            self._build_member_state(
                user=user,
                profile=profile,
                role=role,
                manager_user_id=parent_by_user_id.get(user.id),
            )
            for _member, user, profile, role in rows
        ]

    def _collect_visible_unit_ids(
        self,
        *,
        units: list[Unit],
        visible_root_ids: set[int],
    ) -> set[int]:
        by_parent: dict[int | None, list[Unit]] = {}
        by_id = {int(unit.id): unit for unit in units}
        for unit in units:
            parent_id = int(unit.id_parent) if unit.id_parent is not None else None
            by_parent.setdefault(parent_id, []).append(unit)

        visible_ids: set[int] = set()

        def _collect(unit_id: int) -> None:
            if unit_id in visible_ids:
                return
            visible_ids.add(unit_id)
            for child in by_parent.get(unit_id, []):
                _collect(int(child.id))

        for root_id in sorted(visible_root_ids):
            if root_id in by_id:
                _collect(root_id)
        return visible_ids

    async def _build_single_unit_state(
        self,
        *,
        unit: Unit,
        can_manage: bool,
    ) -> UnitNodeState:
        member_rows = await self._units.list_members(unit_id=int(unit.id))
        members = await self._build_member_states(rows=member_rows)
        children = await self._units.list_children(unit_id=int(unit.id), active_only=True)
        can_delete = can_manage and (
            unit.id_parent is not None
            or (len(children) == 0 and len(members) == 0)
        )
        return UnitNodeState(
            unit_id=int(unit.id),
            name=unit.name,
            id_parent=int(unit.id_parent) if unit.id_parent is not None else None,
            is_active=bool(unit.is_active),
            members=members,
            children=[],
            actions=UnitActionsState(
                can_create_child=can_manage and bool(unit.is_active),
                can_update=can_manage and bool(unit.is_active),
                can_delete=can_delete and bool(unit.is_active),
                can_manage_members=can_manage and bool(unit.is_active),
            ),
        )

    async def _build_tree_nodes(
        self,
        *,
        current_user: CurrentUser,
        visible_root_ids: set[int],
    ) -> list[UnitNodeState]:
        units = await self._units.list_units(active_only=True)
        if not units:
            return []

        by_parent: dict[int | None, list[Unit]] = {}
        by_id = {int(unit.id): unit for unit in units}
        for unit in units:
            parent_id = int(unit.id_parent) if unit.id_parent is not None else None
            by_parent.setdefault(parent_id, []).append(unit)

        visible_ids = self._collect_visible_unit_ids(units=units, visible_root_ids=visible_root_ids)
        visible_units = [unit for unit in units if int(unit.id) in visible_ids]
        member_rows_by_unit: dict[int, list[tuple[UnitMember, User, object | None, object]]] = {
            int(unit.id): []
            for unit in visible_units
        }
        for member, user, profile, role in await self._units.list_members_for_units(unit_ids=sorted(visible_ids)):
            member_rows_by_unit.setdefault(int(member.id_unit), []).append((member, user, profile, role))

        members_by_unit: dict[int, list[UnitMemberState]] = {}
        for unit_id, unit_rows in member_rows_by_unit.items():
            members_by_unit[unit_id] = await self._build_member_states(rows=unit_rows)

        async def _can_manage_unit(unit: Unit) -> bool:
            return await self._can_manage_unit_for_user(current_user=current_user, unit=unit)

        async def _build_node(unit: Unit) -> UnitNodeState:
            unit_id = int(unit.id)
            children = [
                await _build_node(child)
                for child in by_parent.get(unit_id, [])
                if int(child.id) in visible_ids
            ]
            can_manage = await _can_manage_unit(unit)
            can_delete = can_manage and (
                unit.id_parent is not None
                or (len(children) == 0 and len(members_by_unit.get(unit_id, [])) == 0)
            )
            return UnitNodeState(
                unit_id=unit_id,
                name=unit.name,
                id_parent=int(unit.id_parent) if unit.id_parent is not None else None,
                is_active=bool(unit.is_active),
                members=members_by_unit.get(unit_id, []),
                children=children,
                actions=UnitActionsState(
                    can_create_child=can_manage,
                    can_update=can_manage,
                    can_delete=can_delete,
                    can_manage_members=can_manage,
                ),
            )

        root_units = [by_id[root_id] for root_id in sorted(visible_root_ids) if root_id in by_id]
        return [await _build_node(unit) for unit in root_units]

    async def get_tree(self, *, current_user: CurrentUser) -> list[UnitNodeState]:
        readable_root_ids = await self._ensure_read_access(current_user=current_user)
        if self._is_superadmin(current_user):
            units = await self._units.list_units(active_only=True)
            visible_root_ids = {int(unit.id) for unit in units if unit.id_parent is None}
        else:
            visible_root_ids = readable_root_ids
        return await self._build_tree_nodes(
            current_user=current_user,
            visible_root_ids=visible_root_ids,
        )

    async def get_tree_for_user_hierarchy(
        self,
        *,
        current_user: CurrentUser,
        target_user_id: str,
    ) -> list[UnitNodeState]:
        hierarchy = UnitHierarchyService(self._users)
        graph = await hierarchy._get_graph()
        if graph is None:
            return []

        visible_root_ids = graph.root_unit_ids_for_user(target_user_id)
        if not visible_root_ids:
            return []

        return await self._build_tree_nodes(
            current_user=current_user,
            visible_root_ids=visible_root_ids,
        )

    async def _scope_recommended_rows_to_responsibility(
        self,
        *,
        readable_root_ids: set[int],
        active_rows: list[tuple],
    ) -> list[tuple]:
        units = await self._units.list_units(active_only=True)
        visible_ids = self._collect_visible_unit_ids(units=units, visible_root_ids=readable_root_ids)
        all_unit_ids = [int(unit.id) for unit in units]

        anchored_user_ids: set[str] = set()
        for member, _user, _profile, _role in await self._units.list_members_for_units(unit_ids=all_unit_ids):
            if int(member.id_unit) in visible_ids:
                anchored_user_ids.add(member.id_user)

        by_id = {row[0].id: row for row in active_rows}
        anchored_user_ids &= set(by_id.keys())
        return [row for row in active_rows if row[0].id in anchored_user_ids]

    async def get_recommended_tree(self, *, current_user: CurrentUser) -> list[RecommendedHierarchyNodeState]:
        readable_root_ids = await self._ensure_read_access(current_user=current_user)
        role_ids = [
            settings.admin_role_id,
            settings.security_officer_role_id,
            settings.project_manager_role_id,
            settings.lead_economist_role_id,
            settings.economist_role_id,
            settings.operator_role_id,
        ]
        rows = await self._users.list_by_role_ids_with_profiles_and_roles(role_ids=role_ids)
        active_rows = [row for row in rows if row[0].status == "active"]
        if not active_rows:
            return []

        if not self._is_superadmin(current_user):
            active_rows = await self._scope_recommended_rows_to_responsibility(
                readable_root_ids=readable_root_ids,
                active_rows=active_rows,
            )
            if not active_rows:
                return []

        hierarchy = UnitHierarchyService(self._users)
        by_id = {user.id: (user, profile, role) for user, profile, role in active_rows}
        visible_user_ids = set(by_id.keys())
        children_by_parent: dict[str | None, list[str]] = {}
        sort_keys: dict[str, tuple[int, str, str]] = {}
        parent_by_user_id: dict[str, str | None] = {}

        for user, profile, role in active_rows:
            sort_keys[user.id] = (
                int(role.id),
                (profile.full_name or "").casefold(),
                user.id.casefold(),
            )
            manager = await hierarchy.get_primary_manager(
                user_id=user.id,
                visible_user_ids=visible_user_ids,
            )
            parent_id = (
                manager.user_id
                if manager is not None and manager.user_id in by_id and manager.user_id != user.id
                else None
            )
            parent_by_user_id[user.id] = parent_id
            children_by_parent.setdefault(parent_id, []).append(user.id)

        for child_ids in children_by_parent.values():
            child_ids.sort(key=lambda item: sort_keys[item])

        async def _build_node(user_id: str, path: set[str]) -> RecommendedHierarchyNodeState:
            if user_id in path:
                raise Conflict("Обнаружен цикл в текущей иерархии пользователей")
            user, profile, role = by_id[user_id]
            next_path = set(path)
            next_path.add(user_id)
            children = [
                await _build_node(child_id, next_path)
                for child_id in children_by_parent.get(user_id, [])
            ]
            return self._build_recommended_hierarchy_node_state(
                user=user,
                profile=profile,
                role=role,
                manager_user_id=parent_by_user_id.get(user.id),
                children=children,
            )

        root_ids = children_by_parent.get(None, [])
        return [await _build_node(user_id, set()) for user_id in root_ids]

    async def create_unit(
        self,
        *,
        current_user: CurrentUser,
        name: str,
        id_parent: int | None,
    ) -> UnitNodeState:
        UserPolicy.ensure_can_create_units(current_user)
        normalized_name = name.strip()
        if not normalized_name:
            raise Conflict("Название юнита обязательно")

        if id_parent is None:
            if not self._is_superadmin(current_user):
                raise Forbidden("Только суперадминистратор может создавать подразделения верхнего уровня")
        else:
            parent_unit = await self._units.get_by_id(id_parent)
            if parent_unit is None:
                raise NotFound("Родительский юнит не найден")
            if not parent_unit.is_active:
                raise Conflict("Нельзя создавать дочерний юнит внутри неактивного узла")
            await self._ensure_manage_access(current_user=current_user, unit=parent_unit)

        await self._ensure_unique_name(id_parent=id_parent, name=normalized_name)

        unit = Unit(
            name=normalized_name,
            id_parent=id_parent,
            is_active=True,
            id_created_by_user=current_user.user_id,
        )
        await self._units.add(unit)
        await self._units.flush()

        return await self._build_single_unit_state(unit=unit, can_manage=True)

    async def _ensure_parent_reassignment_allowed(
        self,
        *,
        current_user: CurrentUser,
        unit: Unit,
        new_parent_id: int,
    ) -> None:
        if unit.id_parent is None:
            raise Conflict("Подразделение верхнего уровня нельзя переносить внутрь другого юнита")
        new_parent = await self._units.get_by_id(new_parent_id)
        if new_parent is None:
            raise NotFound("Новый родительский юнит не найден")
        if not new_parent.is_active:
            raise Conflict("Нельзя переносить юнит в неактивный родительский узел")
        await self._ensure_manage_access(current_user=current_user, unit=new_parent)

        if int(new_parent.id) == int(unit.id):
            raise Conflict("Юнит не может быть родителем самому себе")

        current_root_id = await self._resolve_root_unit_id(unit=unit)
        new_parent_root_id = await self._resolve_root_unit_id(unit=new_parent)
        if current_root_id != new_parent_root_id:
            raise Conflict("Переносить юнит между разными подразделениями нельзя")

        cursor = new_parent
        visited: set[int] = set()
        while True:
            cursor_id = int(cursor.id)
            if cursor_id == int(unit.id):
                raise Conflict("Нельзя перенести юнит внутрь собственного поддерева")
            if cursor_id in visited or cursor.id_parent is None:
                break
            visited.add(cursor_id)
            parent = await self._units.get_by_id(int(cursor.id_parent))
            if parent is None:
                break
            cursor = parent

    async def update_unit(
        self,
        *,
        current_user: CurrentUser,
        unit_id: int,
        name: str | None = None,
        id_parent: int | None = None,
    ) -> UnitNodeState:
        UserPolicy.ensure_can_update_units(current_user)
        unit = await self._units.get_by_id(unit_id)
        if unit is None:
            raise NotFound("Юнит не найден")
        await self._ensure_manage_access(current_user=current_user, unit=unit)

        if name is None and id_parent is None:
            raise Conflict("Нет данных для обновления юнита")

        if name is not None:
            normalized_name = name.strip()
            if not normalized_name:
                raise Conflict("Название юнита обязательно")
            await self._ensure_unique_name(
                id_parent=int(unit.id_parent) if unit.id_parent is not None else None,
                name=normalized_name,
                exclude_unit_id=int(unit.id),
            )
            unit.name = normalized_name

        if id_parent is not None and id_parent != unit.id_parent:
            await self._ensure_parent_reassignment_allowed(
                current_user=current_user,
                unit=unit,
                new_parent_id=id_parent,
            )
            await self._ensure_unique_name(
                id_parent=id_parent,
                name=unit.name,
                exclude_unit_id=int(unit.id),
            )
            unit.id_parent = id_parent

        unit.updated_at = _utcnow_naive()
        return await self._build_single_unit_state(unit=unit, can_manage=True)

    async def _ensure_active_membership(
        self,
        *,
        unit_id: int,
        user_id: str,
        assigned_by_user_id: str,
    ) -> None:
        membership = await self._units.get_member(unit_id=unit_id, user_id=user_id)
        if membership is not None and membership.is_active:
            return
        if membership is None:
            membership = UnitMember(
                id_unit=unit_id,
                id_user=user_id,
                id_assigned_by_user=assigned_by_user_id,
                is_active=True,
            )
            await self._units.add_member(membership)
        else:
            membership.is_active = True
            membership.id_assigned_by_user = assigned_by_user_id
            membership.updated_at = _utcnow_naive()

    async def _registration_assignable_unit_ids(self, *, current_user: CurrentUser) -> set[int]:
        return await UnitHierarchyService(self._users).get_registration_assignable_unit_ids(
            user_id=current_user.user_id,
        )

    async def add_member_on_registration(
        self,
        *,
        current_user: CurrentUser,
        unit_id: int,
        user_id: str,
    ) -> None:
        UserPolicy.ensure_can_register_user(current_user)
        unit = await self._units.get_by_id(unit_id)
        if unit is None:
            raise NotFound("Юнит не найден")
        if not unit.is_active:
            raise Conflict("Нельзя добавлять сотрудников в неактивный юнит")

        allowed_unit_ids = await self._registration_assignable_unit_ids(current_user=current_user)
        if int(unit_id) not in allowed_unit_ids:
            raise Forbidden("Нельзя назначить пользователя в выбранное объединение")

        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFound("Пользователь не найден")
        self._ensure_non_superadmin_binding_target(current_user=current_user, user=user)
        if user.id_role == settings.contractor_role_id:
            raise Conflict("Контрагентов нельзя назначать в юниты через создание сотрудника")

        await self._ensure_active_membership(
            unit_id=unit_id,
            user_id=user_id,
            assigned_by_user_id=current_user.user_id,
        )
        await self._units.flush()

    async def add_member(
        self,
        *,
        current_user: CurrentUser,
        unit_id: int,
        user_id: str,
    ) -> UnitMemberState:
        UserPolicy.ensure_can_manage_unit_members(current_user)
        unit = await self._units.get_by_id(unit_id)
        if unit is None:
            raise NotFound("Юнит не найден")
        if not unit.is_active:
            raise Conflict("Нельзя добавлять сотрудников в неактивный юнит")
        await self._ensure_manage_access(current_user=current_user, unit=unit)

        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFound("Пользователь не найден")
        self._ensure_non_superadmin_binding_target(current_user=current_user, user=user)
        if user.id_role == settings.contractor_role_id:
            raise Conflict("Контрагентов нельзя назначать в юниты через редактор сотрудников")
        await self._ensure_member_assignable_by_current_user(current_user=current_user, user_id=user_id)

        membership = await self._units.get_member(unit_id=unit_id, user_id=user_id)
        if membership is not None and membership.is_active:
            raise Conflict("Пользователь уже добавлен в этот юнит")

        if membership is None:
            membership = UnitMember(
                id_unit=unit_id,
                id_user=user_id,
                id_assigned_by_user=current_user.user_id,
                is_active=True,
            )
            await self._units.add_member(membership)
        else:
            membership.is_active = True
            membership.id_assigned_by_user = current_user.user_id
            membership.updated_at = _utcnow_naive()

        await self._units.flush()

        rows = await self._units.list_members(unit_id=unit_id, active_only=True)
        member_states = await self._build_member_states(rows=rows)
        for member_state in member_states:
            if member_state.user_id == user_id:
                return member_state

        raise Conflict("Не удалось добавить пользователя в юнит")

    async def remove_member(
        self,
        *,
        current_user: CurrentUser,
        unit_id: int,
        user_id: str,
    ) -> None:
        UserPolicy.ensure_can_manage_unit_members(current_user)
        unit = await self._units.get_by_id(unit_id)
        if unit is None:
            raise NotFound("Юнит не найден")
        await self._ensure_manage_access(current_user=current_user, unit=unit)

        membership = await self._units.get_member(unit_id=unit_id, user_id=user_id)
        if membership is None or not membership.is_active:
            raise NotFound("Участник юнита не найден")

        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFound("Пользователь не найден")
        self._ensure_non_superadmin_binding_target(current_user=current_user, user=user)
        await self._ensure_member_assignable_by_current_user(current_user=current_user, user_id=user_id)

        membership.is_active = False
        membership.updated_at = _utcnow_naive()

    async def delete_unit(
        self,
        *,
        current_user: CurrentUser,
        unit_id: int,
        confirm_reassign: bool = False,
    ) -> None:
        UserPolicy.ensure_can_update_units(current_user)
        unit = await self._units.get_by_id(unit_id)
        if unit is None:
            raise NotFound("Юнит не найден")
        await self._ensure_manage_access(current_user=current_user, unit=unit)

        if not unit.is_active:
            raise Conflict("Юнит уже удален")

        active_children = await self._units.list_children(unit_id=int(unit.id), active_only=True)
        direct_members = await self._units.list_members(unit_id=int(unit.id), active_only=True)

        if unit.id_parent is None:
            if active_children or direct_members:
                raise Conflict("Удалить подразделение верхнего уровня можно только после очистки его структуры")
        elif (active_children or direct_members) and not confirm_reassign:
            raise Conflict("Удаление изменит иерархию. Подтвердите перенос сотрудников и дочерних юнитов.")

        if unit.id_parent is not None:
            parent_id = int(unit.id_parent)
            for member, _user, _profile, _role in direct_members:
                await self._ensure_active_membership(
                    unit_id=parent_id,
                    user_id=member.id_user,
                    assigned_by_user_id=current_user.user_id,
                )
                member.is_active = False
                member.updated_at = _utcnow_naive()

            for child in active_children:
                child.id_parent = parent_id
                child.updated_at = _utcnow_naive()

        unit.is_active = False
        unit.name = _archived_unit_name(unit.name, int(unit.id))
        unit.updated_at = _utcnow_naive()

    async def list_members(
        self,
        *,
        current_user: CurrentUser,
        unit_id: int,
    ) -> list[UnitMemberState]:
        unit = await self._units.get_by_id(unit_id)
        if unit is None:
            raise NotFound("Юнит не найден")
        await self._ensure_read_scope_for_unit(current_user=current_user, unit=unit)
        rows = await self._units.list_members(unit_id=unit_id, active_only=True)
        return await self._build_member_states(rows=rows)

    async def list_available_users_for_unit(
        self,
        *,
        current_user: CurrentUser,
        unit_id: int | None = None,
        search: str | None = None,
    ) -> list[AvailableUnitUserState]:
        UserPolicy.ensure_can_manage_unit_members(current_user)
        if unit_id is None:
            if not self._is_superadmin(current_user):
                if current_user.role_id == settings.admin_role_id:
                    manageable_root_ids = await self._list_manageable_root_ids(current_user=current_user)
                    if not manageable_root_ids:
                        raise Forbidden("Недостаточно прав для подбора сотрудников")
                elif self._uses_hierarchy_scoped_management(current_user):
                    manageable_unit_ids = await self._get_hierarchy_manageable_unit_ids(
                        current_user=current_user,
                    )
                    if not manageable_unit_ids:
                        raise Forbidden("Недостаточно прав для подбора сотрудников")
                else:
                    raise Forbidden("Недостаточно прав для подбора сотрудников")
            rows = await self._units.list_available_users_for_unit(unit_id=None, search=search)
            rows = await self._filter_available_internal_rows_for_current_user(
                current_user=current_user,
                rows=rows,
            )
            return [
                self._build_available_user_state(user=user, profile=profile, role=role)
                for user, profile, role in rows
                if user.id_role != settings.contractor_role_id
            ]
        unit = await self._units.get_by_id(unit_id)
        if unit is None:
            raise NotFound("Юнит не найден")
        if not unit.is_active:
            raise Conflict("Для неактивного юнита нельзя подбирать сотрудников")
        await self._ensure_manage_access(current_user=current_user, unit=unit)
        rows = await self._units.list_available_users_for_unit(unit_id=unit_id, search=search)
        rows = await self._filter_available_internal_rows_for_current_user(
            current_user=current_user,
            rows=rows,
        )
        return [
            self._build_available_user_state(user=user, profile=profile, role=role)
            for user, profile, role in rows
            if user.id_role != settings.contractor_role_id
        ]

    async def list_unassigned_users(
        self,
        *,
        current_user: CurrentUser,
        search: str | None = None,
    ) -> list[AvailableUnitUserState]:
        await self._ensure_read_access(current_user=current_user)
        rows = await self._units.list_unassigned_users(
            contractor_role_id=settings.contractor_role_id,
            search=search,
        )
        rows = await self._filter_available_internal_rows_for_current_user(
            current_user=current_user,
            rows=rows,
        )
        return [
            self._build_available_user_state(user=user, profile=profile, role=role)
            for user, profile, role in rows
        ]

    async def list_available_contractors_for_unit(
        self,
        *,
        current_user: CurrentUser,
        unit_id: int,
        search: str | None = None,
    ) -> list[AvailableUnitUserState]:
        UserPolicy.ensure_can_manage_unit_members(current_user)
        unit = await self._units.get_by_id(unit_id)
        if unit is None:
            raise NotFound("Подразделение не найдено")
        if unit.id_parent is not None:
            raise Conflict("Контрагентов можно привязывать только к подразделению верхнего уровня")
        if not unit.is_active:
            raise Conflict("Для неактивного подразделения нельзя подбирать контрагентов")
        await self._ensure_manage_access(current_user=current_user, unit=unit)
        rows = await self._units.list_available_contractors_for_unit(
            unit_id=unit_id,
            contractor_role_id=settings.contractor_role_id,
            search=search,
        )
        return [
            self._build_available_user_state(user=user, profile=profile, role=role)
            for user, profile, role in rows
        ]

    async def add_contractor(
        self,
        *,
        current_user: CurrentUser,
        unit_id: int,
        user_id: str,
    ) -> UnitMemberState:
        UserPolicy.ensure_can_manage_unit_members(current_user)
        unit = await self._units.get_by_id(unit_id)
        if unit is None:
            raise NotFound("Подразделение не найдено")
        if unit.id_parent is not None:
            raise Conflict("Контрагентов можно привязывать только к подразделению верхнего уровня")
        if not unit.is_active:
            raise Conflict("Нельзя добавлять контрагентов в неактивное подразделение")
        await self._ensure_manage_access(current_user=current_user, unit=unit)

        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFound("Пользователь не найден")
        if user.id_role != settings.contractor_role_id:
            raise Conflict("В подразделение можно добавить только контрагента")

        membership = await self._units.get_member(unit_id=unit_id, user_id=user_id)
        if membership is not None and membership.is_active:
            raise Conflict("Контрагент уже привязан к этому подразделению")

        if membership is None:
            membership = UnitMember(
                id_unit=unit_id,
                id_user=user_id,
                id_assigned_by_user=current_user.user_id,
                is_active=True,
            )
            await self._units.add_member(membership)
        else:
            membership.is_active = True
            membership.id_assigned_by_user = current_user.user_id
            membership.updated_at = _utcnow_naive()

        await self._units.flush()

        rows = await self._units.list_members(unit_id=unit_id, active_only=True)
        member_states = await self._build_member_states(rows=rows)
        for member_state in member_states:
            if member_state.user_id == user_id:
                return member_state

        raise Conflict("Не удалось добавить контрагента в подразделение")
