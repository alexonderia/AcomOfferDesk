from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.authorization import has_permission
from app.domain.department_delegations import get_department_permission_codes
from app.domain.permissions import PermissionCodes
from app.domain.policies import UserPolicy
from app.repositories.users import UserRepository

LEGACY_HIERARCHY_NOTE = (
    "Легаси-иерархия отображается только справочно. "
    "Бизнес-доступы рассчитываются через юниты."
)

_INTERNAL_ROLE_IDS = (
    settings.superadmin_role_id,
    settings.admin_role_id,
    settings.project_manager_role_id,
    settings.lead_economist_role_id,
    settings.economist_role_id,
    settings.operator_role_id,
    settings.security_officer_role_id,
)

_ROLE_PRIORITY = {
    settings.project_manager_role_id: 4,
    settings.lead_economist_role_id: 3,
    settings.economist_role_id: 2,
    settings.operator_role_id: 1,
}

_ROLE_LABELS = {
    settings.superadmin_role_id: "Суперадмин",
    settings.admin_role_id: "Администратор",
    settings.project_manager_role_id: "Руководитель проекта",
    settings.lead_economist_role_id: "Ведущий экономист",
    settings.economist_role_id: "Экономист",
    settings.operator_role_id: "Оператор",
    settings.contractor_role_id: "Контрагент",
    settings.security_officer_role_id: "Служба безопасности",
}


def _role_priority(role_id: int) -> int:
    return _ROLE_PRIORITY.get(int(role_id), 0)


def _role_label(role_id: int) -> str:
    return _ROLE_LABELS.get(int(role_id), f"Роль {role_id}")


@dataclass(frozen=True, slots=True)
class HierarchyUserBrief:
    user_id: str
    full_name: str | None
    role_id: int
    role_name: str
    status: str


@dataclass(frozen=True, slots=True)
class HierarchyUnitBrief:
    unit_id: int
    name: str
    id_parent: int | None


@dataclass(frozen=True, slots=True)
class HierarchyRelationBrief:
    user_id: str
    full_name: str | None
    role_id: int
    role_name: str
    status: str
    source_unit_id: int
    source_unit_name: str


@dataclass(frozen=True, slots=True)
class LegacyHierarchyState:
    legacy_manager: HierarchyUserBrief | None
    legacy_subordinates: list[HierarchyUserBrief]
    is_business_source: bool
    note: str


@dataclass(frozen=True, slots=True)
class UserHierarchyProfileState:
    user: HierarchyUserBrief
    units: list[HierarchyUnitBrief]
    managers: list[HierarchyRelationBrief]
    subordinates: list[HierarchyRelationBrief]
    legacy_hierarchy: LegacyHierarchyState


@dataclass(frozen=True, slots=True)
class HierarchyCounts:
    units_count: int
    managers_count: int
    subordinates_count: int


@dataclass(slots=True)
class _HierarchyGraph:
    parent_by_unit: dict[int, int | None]
    unit_name_by_id: dict[int, str]
    children_by_unit: dict[int, list[int]]
    units_by_user: dict[str, set[int]]
    members_by_unit: dict[int, set[str]]
    user_briefs_by_id: dict[str, HierarchyUserBrief]

    def user_has_units(self, user_id: str) -> bool:
        return bool(self.units_by_user.get(user_id))

    def ancestor_unit_ids(self, unit_id: int) -> list[int]:
        ancestors: list[int] = []
        cursor = self.parent_by_unit.get(int(unit_id))
        visited: set[int] = set()
        while cursor is not None and cursor not in visited:
            visited.add(cursor)
            ancestors.append(cursor)
            cursor = self.parent_by_unit.get(cursor)
        return ancestors

    def descendant_unit_ids(self, unit_ids: Iterable[int], *, include_self: bool = False) -> set[int]:
        source_unit_ids = {int(unit_id) for unit_id in unit_ids}
        result: set[int] = set(source_unit_ids) if include_self else set()
        visited: set[int] = set(source_unit_ids)
        queue: list[int] = list(source_unit_ids)
        while queue:
            unit_id = queue.pop()
            for child_unit_id in self.children_by_unit.get(unit_id, []):
                if child_unit_id in visited:
                    continue
                visited.add(child_unit_id)
                result.add(child_unit_id)
                queue.append(child_unit_id)
        return result

    def root_unit_ids_for_user(self, user_id: str) -> set[int]:
        roots: set[int] = set()
        for unit_id in self.units_by_user.get(user_id, set()):
            cursor = int(unit_id)
            visited: set[int] = set()
            while True:
                parent_id = self.parent_by_unit.get(cursor)
                if parent_id is None or cursor in visited:
                    roots.add(cursor)
                    break
                visited.add(cursor)
                cursor = parent_id
        return roots

    def subtree_unit_ids_for_user(self, user_id: str) -> set[int]:
        return self.descendant_unit_ids(self.units_by_user.get(user_id, set()), include_self=True)

    def management_seed_unit_ids_for_user(self, user_id: str) -> set[int]:
        """Return the most specific assigned units used for management scope.

        If a user is assigned both to an ancestor unit and to a deeper descendant,
        the ancestor assignment does not expand management to sibling branches.
        """
        direct_unit_ids = {int(unit_id) for unit_id in self.units_by_user.get(user_id, set())}
        if len(direct_unit_ids) <= 1:
            return direct_unit_ids

        effective_unit_ids: set[int] = set()
        for candidate_unit_id in direct_unit_ids:
            has_assigned_descendant = False
            for assigned_unit_id in direct_unit_ids:
                if assigned_unit_id == candidate_unit_id:
                    continue
                if candidate_unit_id in self.ancestor_unit_ids(assigned_unit_id):
                    has_assigned_descendant = True
                    break
            if not has_assigned_descendant:
                effective_unit_ids.add(candidate_unit_id)
        return effective_unit_ids

    def module_scope_unit_ids_for_user(self, user_id: str) -> set[int]:
        direct_unit_ids = self.units_by_user.get(user_id, set())
        if not direct_unit_ids:
            return set()
        visible_unit_ids = self.descendant_unit_ids(direct_unit_ids, include_self=True)
        for unit_id in direct_unit_ids:
            visible_unit_ids.update(self.ancestor_unit_ids(unit_id))
        return visible_unit_ids

    def department_scope_unit_ids_for_user(self, user_id: str) -> set[int]:
        root_unit_ids = self.root_unit_ids_for_user(user_id)
        if not root_unit_ids:
            return set()
        return self.descendant_unit_ids(root_unit_ids, include_self=True)

    def users_for_units(self, unit_ids: Iterable[int]) -> set[str]:
        user_ids: set[str] = set()
        for unit_id in unit_ids:
            user_ids.update(self.members_by_unit.get(int(unit_id), set()))
        return user_ids


class UnitHierarchyService:
    def __init__(self, users: UserRepository):
        self._users = users
        self._graph_loaded = False
        self._graph_cache: _HierarchyGraph | None = None

    async def user_has_active_unit_membership(self, *, user_id: str) -> bool:
        graph = await self._get_graph()
        if graph is None:
            return False
        return graph.user_has_units(user_id)

    async def get_department_user_ids(self, *, user_id: str) -> list[str]:
        graph = await self._get_graph()
        if graph is None:
            return []
        return sorted(graph.users_for_units(graph.department_scope_unit_ids_for_user(user_id)))

    async def get_unit_scope_user_ids(self, *, user_id: str) -> list[str]:
        graph = await self._get_graph()
        if graph is None:
            return []
        return sorted(graph.users_for_units(graph.subtree_unit_ids_for_user(user_id)))

    async def get_module_scope_user_ids(self, *, user_id: str) -> list[str]:
        graph = await self._get_graph()
        if graph is None:
            return []
        return sorted(graph.users_for_units(graph.module_scope_unit_ids_for_user(user_id)))

    async def get_management_seed_unit_ids(self, *, user_id: str) -> set[int]:
        graph = await self._get_graph()
        if graph is None:
            return set()
        return graph.management_seed_unit_ids_for_user(user_id)

    async def get_registration_assignable_unit_ids(self, *, user_id: str) -> set[int]:
        graph = await self._get_graph()
        if graph is None:
            return set()
        allowed_unit_ids: set[int] = set()
        for seed_unit_id in graph.management_seed_unit_ids_for_user(user_id):
            allowed_unit_ids.update(
                graph.descendant_unit_ids([seed_unit_id], include_self=True),
            )
        return allowed_unit_ids

    async def get_manager_user_ids(self, *, user_id: str) -> list[str]:
        relations = await self.get_user_managers(user_id=user_id)
        return [item.user_id for item in relations]

    async def get_subordinate_user_ids(self, *, user_id: str) -> list[str]:
        relations = await self.get_user_subordinates(user_id=user_id)
        return [item.user_id for item in relations]

    async def get_primary_manager(
        self,
        *,
        user_id: str,
        visible_user_ids: set[str] | None = None,
        preferred_role_ids: set[int] | None = None,
    ) -> HierarchyRelationBrief | None:
        managers = await self.get_user_managers(
            user_id=user_id,
            visible_user_ids=visible_user_ids,
        )
        if preferred_role_ids:
            for manager in managers:
                if manager.role_id in preferred_role_ids:
                    return manager
        return managers[0] if managers else None

    async def share_unit(self, *, user_a_id: str, user_b_id: str) -> bool:
        graph = await self._get_graph()
        if graph is None:
            return False
        return bool(graph.units_by_user.get(user_a_id, set()) & graph.units_by_user.get(user_b_id, set()))

    async def is_manager_of(self, *, manager_user_id: str, subordinate_user_id: str) -> bool:
        subordinate_ids = await self.get_subordinate_user_ids(user_id=manager_user_id)
        return subordinate_user_id in set(subordinate_ids)

    async def get_visible_user_ids(self, *, current_user: CurrentUser) -> set[str] | None:
        if current_user.role_id == settings.superadmin_role_id:
            return None

        if current_user.role_id == settings.admin_role_id:
            graph = await self._get_graph()
            visible_ids: set[str] = {current_user.user_id}
            if graph is not None:
                department_user_ids = graph.users_for_units(
                    graph.department_scope_unit_ids_for_user(current_user.user_id)
                )
                for user_id in department_user_ids:
                    brief = await self._ensure_user_brief(user_id=user_id, graph=graph)
                    if brief is None or brief.role_id == settings.superadmin_role_id:
                        continue
                    visible_ids.add(user_id)
            visible_ids.update(
                await self._list_active_user_ids_by_role_ids(
                    role_ids={settings.contractor_role_id},
                )
            )
            return visible_ids

        visible_ids: set[str] = {current_user.user_id}
        if current_user.role_id == settings.project_manager_role_id:
            visible_ids.update(await self.get_department_user_ids(user_id=current_user.user_id))
            return visible_ids

        if current_user.role_id in {
            settings.lead_economist_role_id,
            settings.economist_role_id,
        }:
            if current_user.permissions & get_department_permission_codes():
                visible_ids.update(await self.get_department_user_ids(user_id=current_user.user_id))
            else:
                visible_ids.update(await self.get_module_scope_user_ids(user_id=current_user.user_id))
            return visible_ids

        return visible_ids

    async def can_view_user(self, *, current_user: CurrentUser, target_user_id: str) -> bool:
        if target_user_id == current_user.user_id:
            return True
        visible_ids = await self.get_visible_user_ids(current_user=current_user)
        if visible_ids is None:
            return True
        return target_user_id in visible_ids

    async def _list_active_user_ids_by_role_ids(self, *, role_ids: set[int]) -> set[str]:
        normalized_role_ids = sorted({int(role_id) for role_id in role_ids})
        if not normalized_role_ids:
            return set()

        list_by_role_ids = getattr(self._users, "list_by_role_ids_with_profiles_and_roles", None)
        if callable(list_by_role_ids):
            rows = await list_by_role_ids(role_ids=normalized_role_ids)
            return {
                str(user.id)
                for user, _profile, _role in rows
                if getattr(user, "status", "active") == "active"
            }

        list_users_with_profiles = getattr(self._users, "list_users_with_profiles", None)
        if callable(list_users_with_profiles):
            user_ids: set[str] = set()
            for role_id in normalized_role_ids:
                rows = await list_users_with_profiles(role_id=role_id)
                user_ids.update(
                    str(user.id)
                    for user, _profile in rows
                    if getattr(user, "status", "active") == "active"
                )
            return user_ids

        return set()

    async def get_user_units(self, *, user_id: str) -> list[HierarchyUnitBrief]:
        graph = await self._get_graph()
        if graph is None:
            return []
        unit_ids = graph.units_by_user.get(user_id, set())
        items = [
            HierarchyUnitBrief(
                unit_id=int(unit_id),
                name=graph.unit_name_by_id.get(int(unit_id), f"Юнит {unit_id}"),
                id_parent=graph.parent_by_unit.get(int(unit_id)),
            )
            for unit_id in unit_ids
        ]
        return sorted(items, key=lambda item: (item.id_parent is not None, item.name.lower(), item.unit_id))

    async def get_user_managers(
        self,
        *,
        user_id: str,
        visible_user_ids: set[str] | None = None,
    ) -> list[HierarchyRelationBrief]:
        graph = await self._get_graph()
        if graph is None:
            return []
        target = await self._ensure_user_brief(user_id=user_id, graph=graph)
        if target is None:
            return []

        relations: dict[str, tuple[int, HierarchyRelationBrief]] = {}
        for unit_id in graph.units_by_user.get(user_id, set()):
            for manager_user_id in graph.members_by_unit.get(unit_id, set()):
                if manager_user_id == user_id:
                    continue
                manager_brief = await self._ensure_user_brief(user_id=manager_user_id, graph=graph)
                if manager_brief is None:
                    continue
                if not self._can_manage(
                    manager_role_id=manager_brief.role_id,
                    target_role_id=target.role_id,
                    same_unit=True,
                ):
                    continue
                self._upsert_relation(
                    relations=relations,
                    related_user=manager_brief,
                    source_unit_id=unit_id,
                    source_unit_name=graph.unit_name_by_id.get(unit_id, f"Юнит {unit_id}"),
                    distance=0,
                )

            for distance, ancestor_unit_id in enumerate(graph.ancestor_unit_ids(unit_id), start=1):
                for manager_user_id in graph.members_by_unit.get(ancestor_unit_id, set()):
                    if manager_user_id == user_id:
                        continue
                    manager_brief = await self._ensure_user_brief(user_id=manager_user_id, graph=graph)
                    if manager_brief is None:
                        continue
                    if not self._can_manage(
                        manager_role_id=manager_brief.role_id,
                        target_role_id=target.role_id,
                        same_unit=False,
                    ):
                        continue
                    self._upsert_relation(
                        relations=relations,
                        related_user=manager_brief,
                        source_unit_id=ancestor_unit_id,
                        source_unit_name=graph.unit_name_by_id.get(
                            ancestor_unit_id,
                            f"Юнит {ancestor_unit_id}",
                        ),
                        distance=distance,
                    )

        return self._sorted_relations(relations=relations, visible_user_ids=visible_user_ids)

    async def get_user_subordinates(
        self,
        *,
        user_id: str,
        visible_user_ids: set[str] | None = None,
    ) -> list[HierarchyRelationBrief]:
        graph = await self._get_graph()
        if graph is None:
            return []
        manager = await self._ensure_user_brief(user_id=user_id, graph=graph)
        if manager is None:
            return []

        relations: dict[str, tuple[int, HierarchyRelationBrief]] = {}
        for unit_id in graph.management_seed_unit_ids_for_user(user_id):
            for subordinate_user_id in graph.members_by_unit.get(unit_id, set()):
                if subordinate_user_id == user_id:
                    continue
                subordinate_brief = await self._ensure_user_brief(user_id=subordinate_user_id, graph=graph)
                if subordinate_brief is None:
                    continue
                if not self._can_manage(
                    manager_role_id=manager.role_id,
                    target_role_id=subordinate_brief.role_id,
                    same_unit=True,
                ):
                    continue
                self._upsert_relation(
                    relations=relations,
                    related_user=subordinate_brief,
                    source_unit_id=unit_id,
                    source_unit_name=graph.unit_name_by_id.get(unit_id, f"Юнит {unit_id}"),
                    distance=0,
                )

            descendant_unit_ids = graph.descendant_unit_ids({unit_id}, include_self=False)
            for distance, descendant_unit_id in enumerate(sorted(descendant_unit_ids), start=1):
                for subordinate_user_id in graph.members_by_unit.get(descendant_unit_id, set()):
                    if subordinate_user_id == user_id:
                        continue
                    subordinate_brief = await self._ensure_user_brief(user_id=subordinate_user_id, graph=graph)
                    if subordinate_brief is None:
                        continue
                    if not self._can_manage(
                        manager_role_id=manager.role_id,
                        target_role_id=subordinate_brief.role_id,
                        same_unit=False,
                    ):
                        continue
                    self._upsert_relation(
                        relations=relations,
                        related_user=subordinate_brief,
                        source_unit_id=descendant_unit_id,
                        source_unit_name=graph.unit_name_by_id.get(
                            descendant_unit_id,
                            f"Юнит {descendant_unit_id}",
                        ),
                        distance=distance,
                    )

        return self._sorted_relations(relations=relations, visible_user_ids=visible_user_ids)

    async def get_hierarchy_counts_by_user_ids(self, *, user_ids: Iterable[str]) -> dict[str, HierarchyCounts]:
        graph = await self._get_graph()
        result: dict[str, HierarchyCounts] = {}
        if graph is None:
            for user_id in user_ids:
                result[str(user_id)] = HierarchyCounts(0, 0, 0)
            return result

        for user_id in {str(item) for item in user_ids}:
            units_count = len(graph.units_by_user.get(user_id, set()))
            managers_count = len(await self.get_manager_user_ids(user_id=user_id))
            subordinates_count = len(await self.get_subordinate_user_ids(user_id=user_id))
            result[user_id] = HierarchyCounts(
                units_count=units_count,
                managers_count=managers_count,
                subordinates_count=subordinates_count,
            )
        return result

    async def get_user_hierarchy_profile(
        self,
        *,
        user_id: str,
        visible_user_ids: set[str] | None = None,
    ) -> UserHierarchyProfileState | None:
        graph = await self._get_graph()
        if graph is None:
            return None
        user = await self._ensure_user_brief(user_id=user_id, graph=graph)
        if user is None:
            return None
        return UserHierarchyProfileState(
            user=user,
            units=await self.get_user_units(user_id=user_id),
            managers=await self.get_user_managers(user_id=user_id, visible_user_ids=visible_user_ids),
            subordinates=await self.get_user_subordinates(user_id=user_id, visible_user_ids=visible_user_ids),
            legacy_hierarchy=await self._build_legacy_hierarchy(user_id=user_id, graph=graph),
        )

    async def _build_legacy_hierarchy(
        self,
        *,
        user_id: str,
        graph: _HierarchyGraph,
    ) -> LegacyHierarchyState:
        user = await self._users.get_by_id(user_id)
        if user is None:
            return LegacyHierarchyState(
                legacy_manager=None,
                legacy_subordinates=[],
                is_business_source=False,
                note=LEGACY_HIERARCHY_NOTE,
            )

        manager_brief: HierarchyUserBrief | None = None
        # legacy only: users.id_parent is not used for business access checks
        manager_user_id = getattr(user, "id_parent", None)
        if manager_user_id:
            manager_brief = await self._ensure_user_brief(user_id=manager_user_id, graph=graph)

        subordinate_ids: list[str] = []
        # legacy only: users.id_parent is not used for business access checks
        list_subordinates = getattr(self._users, "list_subordinates_with_profiles", None)
        if callable(list_subordinates):
            subordinate_ids = [item.id for item, _profile in await list_subordinates(manager_user_id=user_id)]
        else:
            pairs = getattr(self._users, "list_active_user_parent_pairs", None)
            if callable(pairs):
                subordinate_ids = [
                    candidate_user_id
                    for candidate_user_id, parent_user_id in await pairs()
                    if parent_user_id == user_id
                ]

        legacy_subordinates = [
            brief
            for brief in [
                await self._ensure_user_brief(user_id=subordinate_user_id, graph=graph)
                for subordinate_user_id in subordinate_ids
            ]
            if brief is not None
        ]
        legacy_subordinates.sort(key=self._user_sort_key)

        return LegacyHierarchyState(
            legacy_manager=manager_brief,
            legacy_subordinates=legacy_subordinates,
            is_business_source=False,
            note=LEGACY_HIERARCHY_NOTE,
        )

    async def _get_graph(self) -> _HierarchyGraph | None:
        if self._graph_loaded:
            return self._graph_cache

        list_units = getattr(self._users, "list_active_units", None)
        list_memberships = getattr(self._users, "list_active_unit_memberships", None)
        if not callable(list_units) or not callable(list_memberships):
            self._graph_loaded = True
            self._graph_cache = None
            return None

        unit_details_loader = getattr(self._users, "list_active_unit_details", None)
        if callable(unit_details_loader):
            detail_rows = await unit_details_loader()
        else:
            detail_rows = [
                (int(unit_id), f"Юнит {unit_id}", int(parent_id) if parent_id is not None else None)
                for unit_id, parent_id in await list_units()
            ]

        memberships = await list_memberships()
        parent_by_unit: dict[int, int | None] = {}
        unit_name_by_id: dict[int, str] = {}
        children_by_unit: dict[int, list[int]] = {}
        for unit_id, unit_name, parent_id in detail_rows:
            parent_by_unit[int(unit_id)] = int(parent_id) if parent_id is not None else None
            unit_name_by_id[int(unit_id)] = str(unit_name)
            if parent_id is not None:
                children_by_unit.setdefault(int(parent_id), []).append(int(unit_id))

        units_by_user: dict[str, set[int]] = {}
        members_by_unit: dict[int, set[str]] = {}
        membership_user_ids: set[str] = set()
        for user_id, unit_id in memberships:
            normalized_unit_id = int(unit_id)
            if normalized_unit_id not in parent_by_unit:
                continue
            normalized_user_id = str(user_id)
            units_by_user.setdefault(normalized_user_id, set()).add(normalized_unit_id)
            members_by_unit.setdefault(normalized_unit_id, set()).add(normalized_user_id)
            membership_user_ids.add(normalized_user_id)

        user_briefs_by_id = await self._load_user_briefs(user_ids=membership_user_ids)
        self._graph_loaded = True
        self._graph_cache = _HierarchyGraph(
            parent_by_unit=parent_by_unit,
            unit_name_by_id=unit_name_by_id,
            children_by_unit=children_by_unit,
            units_by_user=units_by_user,
            members_by_unit=members_by_unit,
            user_briefs_by_id=user_briefs_by_id,
        )
        return self._graph_cache

    async def _load_user_briefs(self, *, user_ids: set[str]) -> dict[str, HierarchyUserBrief]:
        if not user_ids:
            return {}

        briefs: dict[str, HierarchyUserBrief] = {}
        list_by_ids = getattr(self._users, "list_by_ids_with_profiles_and_roles", None)
        if callable(list_by_ids):
            rows = await list_by_ids(user_ids=sorted(user_ids))
            for user, profile, role in rows:
                briefs[str(user.id)] = self._build_user_brief(
                    user=user,
                    full_name=profile.full_name if profile is not None else None,
                    role_name=role.role if role is not None else None,
                )
        else:
            list_by_role_ids = getattr(self._users, "list_by_role_ids_with_profiles_and_roles", None)
            if callable(list_by_role_ids):
                rows = await list_by_role_ids(role_ids=list(_INTERNAL_ROLE_IDS))
                for user, profile, role in rows:
                    if str(user.id) not in user_ids:
                        continue
                    briefs[str(user.id)] = self._build_user_brief(
                        user=user,
                        full_name=profile.full_name if profile is not None else None,
                        role_name=role.role if role is not None else None,
                    )

        missing_user_ids = sorted(user_ids - set(briefs))
        for missing_user_id in missing_user_ids:
            user = await self._users.get_by_id(missing_user_id)
            if user is None:
                continue
            full_name = getattr(user, "full_name", None)
            briefs[missing_user_id] = self._build_user_brief(
                user=user,
                full_name=full_name,
                role_name=None,
            )

        return briefs

    async def _ensure_user_brief(
        self,
        *,
        user_id: str,
        graph: _HierarchyGraph,
    ) -> HierarchyUserBrief | None:
        brief = graph.user_briefs_by_id.get(user_id)
        if brief is not None:
            return brief
        loaded = await self._load_user_briefs(user_ids={user_id})
        if not loaded:
            return None
        graph.user_briefs_by_id.update(loaded)
        return graph.user_briefs_by_id.get(user_id)

    @staticmethod
    def _build_user_brief(*, user, full_name: str | None, role_name: str | None) -> HierarchyUserBrief:
        return HierarchyUserBrief(
            user_id=str(user.id),
            full_name=full_name,
            role_id=int(user.id_role),
            role_name=role_name or _role_label(int(user.id_role)),
            status=str(getattr(user, "status", "review")),
        )

    @staticmethod
    def _can_manage(*, manager_role_id: int, target_role_id: int, same_unit: bool) -> bool:
        if not UserPolicy.can_manage_subordinate_role(
            current_role_id=manager_role_id,
            target_role_id=target_role_id,
        ):
            return False
        if same_unit:
            return _role_priority(manager_role_id) > _role_priority(target_role_id)
        return True

    @staticmethod
    def _upsert_relation(
        *,
        relations: dict[str, tuple[int, HierarchyRelationBrief]],
        related_user: HierarchyUserBrief,
        source_unit_id: int,
        source_unit_name: str,
        distance: int,
    ) -> None:
        relation = HierarchyRelationBrief(
            user_id=related_user.user_id,
            full_name=related_user.full_name,
            role_id=related_user.role_id,
            role_name=related_user.role_name,
            status=related_user.status,
            source_unit_id=int(source_unit_id),
            source_unit_name=source_unit_name,
        )
        current = relations.get(related_user.user_id)
        if current is None or distance < current[0]:
            relations[related_user.user_id] = (distance, relation)

    def _sorted_relations(
        self,
        *,
        relations: dict[str, tuple[int, HierarchyRelationBrief]],
        visible_user_ids: set[str] | None,
    ) -> list[HierarchyRelationBrief]:
        items = [
            relation
            for _distance, relation in relations.values()
            if visible_user_ids is None or relation.user_id in visible_user_ids
        ]
        return sorted(items, key=self._relation_sort_key)

    @staticmethod
    def _user_sort_key(item: HierarchyUserBrief) -> tuple[int, str, str]:
        return (item.role_id, (item.full_name or item.user_id).lower(), item.user_id)

    @staticmethod
    def _relation_sort_key(item: HierarchyRelationBrief) -> tuple[int, str, str, int]:
        return (item.role_id, (item.full_name or item.user_id).lower(), item.user_id, item.source_unit_id)
