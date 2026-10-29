from __future__ import annotations

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.authorization import has_permission
from app.domain.permissions import PermissionCodes
from app.repositories.users import UserRepository
from app.services.department_scope import DepartmentScopeService
from app.services.unit_hierarchy import UnitHierarchyService


class StaffAccessScopeService:
    """Business scope for internal staff based on unit membership."""

    def __init__(self, users: UserRepository):
        self._users = users
        self._department_scope = DepartmentScopeService(users)
        self._hierarchy = UnitHierarchyService(users)

    async def resolve_module_root_user_id(self, *, user_id: str, role_id: int) -> str:
        if role_id not in {settings.lead_economist_role_id, settings.economist_role_id}:
            return user_id

        managers = await self._hierarchy.get_user_managers(user_id=user_id)
        for manager in managers:
            if manager.role_id == settings.lead_economist_role_id:
                return manager.user_id
        return user_id

    async def resolve_module_owner_ids(self, *, current_user: CurrentUser) -> list[str]:
        if current_user.role_id not in {
            settings.project_manager_role_id,
            settings.lead_economist_role_id,
            settings.economist_role_id,
        }:
            return []
        return await self._hierarchy.get_module_scope_user_ids(user_id=current_user.user_id)

    async def resolve_unit_management_owner_ids(self, *, current_user: CurrentUser) -> list[str]:
        if current_user.role_id not in {
            settings.project_manager_role_id,
            settings.lead_economist_role_id,
            settings.economist_role_id,
        }:
            return []
        return await self._hierarchy.get_subordinate_user_ids(user_id=current_user.user_id)

    async def can_view_request_owner(
        self,
        *,
        current_user: CurrentUser,
        request_owner_user_id: str,
    ) -> bool:
        if current_user.role_id == settings.superadmin_role_id:
            return True
        if current_user.role_id not in {
            settings.project_manager_role_id,
            settings.lead_economist_role_id,
            settings.economist_role_id,
        }:
            return False
        if request_owner_user_id == current_user.user_id:
            return True
        if await self._department_scope.is_user_in_current_user_department(
            current_user=current_user,
            target_user_id=request_owner_user_id,
        ):
            return True
        visible_user_ids = await self._hierarchy.get_visible_user_ids(current_user=current_user)
        if visible_user_ids is None:
            return True
        return request_owner_user_id in visible_user_ids

    async def can_manage_request_owner(
        self,
        *,
        current_user: CurrentUser,
        request_owner_user_id: str,
    ) -> bool:
        manageable_owner_ids = await self.resolve_manageable_owner_ids(
            current_user=current_user,
            candidate_owner_ids={request_owner_user_id},
        )
        return request_owner_user_id in manageable_owner_ids

    async def resolve_manageable_owner_ids(
        self,
        *,
        current_user: CurrentUser,
        candidate_owner_ids: set[str],
    ) -> set[str]:
        if not candidate_owner_ids:
            return set()

        if current_user.role_id == settings.superadmin_role_id:
            return set(candidate_owner_ids)

        manageable_owner_ids: set[str] = set()
        if current_user.user_id in candidate_owner_ids:
            manageable_owner_ids.add(current_user.user_id)

        if has_permission(current_user, PermissionCodes.DEPARTMENT_REQUESTS_UPDATE):
            department_owner_ids = await self._department_scope.resolve_department_owner_ids_for_current_user(
                current_user=current_user,
            )
            manageable_owner_ids.update(candidate_owner_ids & set(department_owner_ids))

        if current_user.role_id in {
            settings.project_manager_role_id,
            settings.lead_economist_role_id,
            settings.economist_role_id,
        }:
            subordinate_owner_ids = await self.resolve_unit_management_owner_ids(current_user=current_user)
            manageable_owner_ids.update(candidate_owner_ids & set(subordinate_owner_ids))

        return manageable_owner_ids

    async def is_hierarchy_manager_of(
        self,
        *,
        current_user: CurrentUser,
        request_owner_user_id: str,
    ) -> bool:
        if request_owner_user_id == current_user.user_id:
            return True
        if current_user.role_id == settings.superadmin_role_id:
            return True
        if current_user.role_id not in {
            settings.project_manager_role_id,
            settings.lead_economist_role_id,
            settings.economist_role_id,
        }:
            return False
        return await self._hierarchy.is_manager_of(
            manager_user_id=current_user.user_id,
            subordinate_user_id=request_owner_user_id,
        )

    async def can_view_chat_for_request(
        self,
        *,
        current_user: CurrentUser,
        request_owner_user_id: str,
    ) -> bool:
        if has_permission(current_user, PermissionCodes.DEPARTMENT_CHATS_READ):
            if await self._department_scope.is_user_in_current_user_department(
                current_user=current_user,
                target_user_id=request_owner_user_id,
            ):
                return True
        return await self.can_view_request_owner(
            current_user=current_user,
            request_owner_user_id=request_owner_user_id,
        )

    async def can_send_chat_for_request(
        self,
        *,
        current_user: CurrentUser,
        request_owner_user_id: str,
    ) -> bool:
        return await self.is_hierarchy_manager_of(
            current_user=current_user,
            request_owner_user_id=request_owner_user_id,
        )
