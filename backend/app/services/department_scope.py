from __future__ import annotations

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.repositories.users import UserRepository
from app.services.unit_hierarchy import UnitHierarchyService


class DepartmentScopeService:
    """Resolves unit-based department and subtree visibility scopes."""

    def __init__(self, users: UserRepository):
        self._hierarchy = UnitHierarchyService(users)

    async def user_has_active_unit_membership(self, *, user_id: str) -> bool:
        return await self._hierarchy.user_has_active_unit_membership(user_id=user_id)

    async def resolve_department_owner_ids_for_current_user(
        self,
        *,
        current_user: CurrentUser,
    ) -> list[str]:
        return await self._hierarchy.get_department_user_ids(user_id=current_user.user_id)

    async def resolve_unit_scope_owner_ids_for_user(self, *, user_id: str) -> list[str]:
        return await self._hierarchy.get_unit_scope_user_ids(user_id=user_id)

    async def resolve_descendant_unit_scope_owner_ids_for_user(self, *, user_id: str) -> list[str]:
        return await self._hierarchy.get_subordinate_user_ids(user_id=user_id)

    async def resolve_subtree_owner_ids(self, *, root_user_id: str) -> list[str]:
        owner_ids = {root_user_id}
        owner_ids.update(await self._hierarchy.get_subordinate_user_ids(user_id=root_user_id))
        return sorted(owner_ids)

    async def resolve_department_root_user_id_for_user(
        self,
        *,
        user_id: str,
        role_id: int,
    ) -> str | None:
        if role_id == settings.project_manager_role_id:
            return user_id
        manager = await self._hierarchy.get_primary_manager(
            user_id=user_id,
            preferred_role_ids={settings.project_manager_role_id},
        )
        if manager is not None:
            return manager.user_id
        if await self._hierarchy.user_has_active_unit_membership(user_id=user_id):
            return user_id
        return None

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
