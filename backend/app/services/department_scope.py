from __future__ import annotations

from collections.abc import Iterable

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.repositories.users import UserRepository


class _UnitGraph:
    """In-memory view of active units + memberships for org-scope resolution."""

    def __init__(
        self,
        *,
        units: list[tuple[int, int | None]],
        memberships: list[tuple[str, int]],
    ) -> None:
        self.parent_by_unit: dict[int, int | None] = {int(uid): parent for uid, parent in units}
        self.children_by_unit: dict[int, list[int]] = {}
        for unit_id, parent_id in self.parent_by_unit.items():
            if parent_id is not None:
                self.children_by_unit.setdefault(parent_id, []).append(unit_id)

        self.units_by_user: dict[str, set[int]] = {}
        self.members_by_unit: dict[int, set[str]] = {}
        for user_id, unit_id in memberships:
            unit_id = int(unit_id)
            # Ignore memberships pointing at inactive/unknown units.
            if unit_id not in self.parent_by_unit:
                continue
            self.units_by_user.setdefault(user_id, set()).add(unit_id)
            self.members_by_unit.setdefault(unit_id, set()).add(user_id)

    def resolve_root_unit_id(self, unit_id: int) -> int:
        cursor = int(unit_id)
        visited: set[int] = set()
        while True:
            parent = self.parent_by_unit.get(cursor)
            if parent is None or cursor in visited:
                return cursor
            visited.add(cursor)
            cursor = parent

    def collect_subtree_unit_ids(self, unit_ids: Iterable[int]) -> set[int]:
        result: set[int] = set()
        queue: list[int] = [int(uid) for uid in unit_ids]
        while queue:
            unit_id = queue.pop()
            if unit_id in result:
                continue
            result.add(unit_id)
            queue.extend(self.children_by_unit.get(unit_id, []))
        return result

    def members_of_units(self, unit_ids: Iterable[int]) -> set[str]:
        owners: set[str] = set()
        for unit_id in unit_ids:
            owners |= self.members_by_unit.get(int(unit_id), set())
        return owners


class DepartmentScopeService:
    """Resolves the "подразделение" (department) scope for internal staff.

    A department is the root unit (корневой юнит) a user belongs to via ``unit_members``.
    When a user has no active unit membership (or the repository does not expose unit data,
    e.g. in unit tests), the service falls back to the legacy hierarchy-based definition where
    the department is the subtree under the user's project-manager ancestor.
    """

    def __init__(self, users: UserRepository):
        self._users = users

    async def _load_unit_graph(self) -> _UnitGraph | None:
        list_units = getattr(self._users, "list_active_units", None)
        list_memberships = getattr(self._users, "list_active_unit_memberships", None)
        if not callable(list_units) or not callable(list_memberships):
            return None
        units = await list_units()
        memberships = await list_memberships()
        return _UnitGraph(units=units, memberships=memberships)

    async def user_has_active_unit_membership(self, *, user_id: str) -> bool:
        graph = await self._load_unit_graph()
        if graph is None:
            return False
        return bool(graph.units_by_user.get(user_id))

    async def resolve_department_owner_ids_for_current_user(
        self,
        *,
        current_user: CurrentUser,
    ) -> list[str]:
        graph = await self._load_unit_graph()
        if graph is not None:
            user_unit_ids = graph.units_by_user.get(current_user.user_id)
            if user_unit_ids:
                root_unit_ids = {graph.resolve_root_unit_id(unit_id) for unit_id in user_unit_ids}
                subtree_unit_ids = graph.collect_subtree_unit_ids(root_unit_ids)
                return list(graph.members_of_units(subtree_unit_ids))

        # Fallback: legacy hierarchy-based department (rollout safety / no unit data).
        return await self._resolve_department_owner_ids_via_hierarchy(current_user=current_user)

    async def resolve_unit_scope_owner_ids_for_user(self, *, user_id: str) -> list[str]:
        """Members of the subtree of every unit the user *directly* belongs to.

        Used for the narrow ВЭ/Э visibility: their own unit(s) and any nested sub-units,
        as opposed to the whole root-unit department.
        """
        graph = await self._load_unit_graph()
        if graph is None:
            return []
        user_unit_ids = graph.units_by_user.get(user_id)
        if not user_unit_ids:
            return []
        subtree_unit_ids = graph.collect_subtree_unit_ids(user_unit_ids)
        return list(graph.members_of_units(subtree_unit_ids))

    async def is_user_in_current_user_department(
        self,
        *,
        current_user: CurrentUser,
        target_user_id: str,
    ) -> bool:
        department_owner_ids = await self.resolve_department_owner_ids_for_current_user(
            current_user=current_user,
        )
        return target_user_id in set(department_owner_ids)

    # ------------------------------------------------------------------
    # Legacy hierarchy-based helpers (fallback + management/module scopes)
    # ------------------------------------------------------------------

    async def _resolve_department_owner_ids_via_hierarchy(
        self,
        *,
        current_user: CurrentUser,
    ) -> list[str]:
        root_user_id = await self.resolve_department_root_user_id_for_user(
            user_id=current_user.user_id,
            role_id=current_user.role_id,
        )
        if root_user_id is None:
            return []
        return await self.resolve_subtree_owner_ids(root_user_id=root_user_id)

    async def resolve_department_root_user_id_for_user(
        self,
        *,
        user_id: str,
        role_id: int,
    ) -> str | None:
        if role_id == settings.project_manager_role_id:
            return user_id

        cursor_id: str | None = user_id
        visited: set[str] = set()
        while cursor_id is not None and cursor_id not in visited:
            visited.add(cursor_id)
            cursor_user = await self._users.get_by_id(cursor_id)
            if cursor_user is None:
                return None
            if cursor_user.id_role == settings.project_manager_role_id:
                return cursor_user.id
            cursor_id = cursor_user.id_parent
        return None

    async def resolve_subtree_owner_ids(self, *, root_user_id: str) -> list[str]:
        rows = await self._users.list_active_user_parent_pairs()
        children_by_parent: dict[str, list[str]] = {}
        for user_id, parent_id in rows:
            if parent_id is None:
                continue
            children_by_parent.setdefault(parent_id, []).append(user_id)

        visible: set[str] = {root_user_id}
        queue: list[str] = [root_user_id]
        root_user = await self._users.get_by_id(root_user_id)
        root_is_project_manager = bool(
            root_user is not None and root_user.id_role == settings.project_manager_role_id
        )
        while queue:
            manager_id = queue.pop()
            for child_id in children_by_parent.get(manager_id, []):
                if child_id in visible:
                    continue
                if root_is_project_manager:
                    child_user = await self._users.get_by_id(child_id)
                    if (
                        child_user is not None
                        and child_user.id_role == settings.project_manager_role_id
                    ):
                        # Each project manager is a separate subdivision root.
                        continue
                visible.add(child_id)
                queue.append(child_id)
        return list(visible)
