from __future__ import annotations

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.authorization import has_permission
from app.domain.permissions import PermissionCodes
from app.repositories.users import UserRepository
from app.services.department_scope import DepartmentScopeService


class StaffAccessScopeService:
    """Business scope for internal staff: department visibility vs hierarchy management."""

    def __init__(self, users: UserRepository):
        self._users = users
        self._department_scope = DepartmentScopeService(users)

    async def resolve_module_root_user_id(self, *, user_id: str, role_id: int) -> str:
        if role_id in {settings.lead_economist_role_id, settings.economist_role_id}:
            cursor_id: str | None = user_id
            visited: set[str] = set()
            fallback_lead_id: str | None = None
            while cursor_id is not None and cursor_id not in visited:
                visited.add(cursor_id)
                cursor_user = await self._users.get_by_id(cursor_id)
                if cursor_user is None:
                    break
                if cursor_user.id_role == settings.lead_economist_role_id:
                    fallback_lead_id = cursor_user.id
                    parent_user = await self._users.get_by_id(cursor_user.id_parent) if cursor_user.id_parent else None
                    if parent_user is not None and parent_user.id_role == settings.project_manager_role_id:
                        return cursor_user.id
                cursor_id = cursor_user.id_parent
            if fallback_lead_id is not None:
                return fallback_lead_id
            return user_id

        return user_id

    async def resolve_module_owner_ids(self, *, current_user: CurrentUser) -> list[str]:
        if current_user.role_id not in {
            settings.project_manager_role_id,
            settings.lead_economist_role_id,
            settings.economist_role_id,
        }:
            return []
        module_root_user_id = await self.resolve_module_root_user_id(
            user_id=current_user.user_id,
            role_id=current_user.role_id,
        )
        return await self._department_scope.resolve_subtree_owner_ids(root_user_id=module_root_user_id)

    async def resolve_unit_management_owner_ids(self, *, current_user: CurrentUser) -> list[str]:
        if current_user.role_id not in {
            settings.project_manager_role_id,
            settings.lead_economist_role_id,
            settings.economist_role_id,
        }:
            return []
        return await self._department_scope.resolve_descendant_unit_scope_owner_ids_for_user(
            user_id=current_user.user_id,
        )

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
        return await self._is_inside_hierarchy_management_scope(
            current_user=current_user,
            request_owner_user_id=request_owner_user_id,
        )

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
            if callable(getattr(self._users, "list_active_user_parent_pairs", None)):
                hierarchy_owner_ids = await self._department_scope.resolve_subtree_owner_ids(
                    root_user_id=current_user.user_id,
                )
                manageable_owner_ids.update(candidate_owner_ids & set(hierarchy_owner_ids))
            else:
                for owner_user_id in candidate_owner_ids:
                    if await self._is_inside_hierarchy_management_scope(
                        current_user=current_user,
                        request_owner_user_id=owner_user_id,
                    ):
                        manageable_owner_ids.add(owner_user_id)

            unit_scope_owner_ids = await self.resolve_unit_management_owner_ids(current_user=current_user)
            manageable_owner_ids.update(candidate_owner_ids & set(unit_scope_owner_ids))

        return manageable_owner_ids

    async def is_hierarchy_manager_of(
        self,
        *,
        current_user: CurrentUser,
        request_owner_user_id: str,
    ) -> bool:
        return await self._is_inside_hierarchy_management_scope(
            current_user=current_user,
            request_owner_user_id=request_owner_user_id,
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
        return await self._is_inside_hierarchy_management_scope(
            current_user=current_user,
            request_owner_user_id=request_owner_user_id,
        )

    async def _is_inside_hierarchy_management_scope(
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
        if await self._is_descendant(
            ancestor_user_id=current_user.user_id,
            target_user_id=request_owner_user_id,
        ):
            return True
        unit_scope_owner_ids = await self.resolve_unit_management_owner_ids(current_user=current_user)
        return request_owner_user_id in set(unit_scope_owner_ids)

    async def _is_descendant(
        self,
        *,
        ancestor_user_id: str,
        target_user_id: str,
    ) -> bool:
        cursor_id: str | None = target_user_id
        visited: set[str] = set()
        while cursor_id is not None and cursor_id not in visited:
            if cursor_id == ancestor_user_id:
                return True
            visited.add(cursor_id)
            cursor_user = await self._users.get_by_id(cursor_id)
            if cursor_user is None:
                return False
            cursor_id = cursor_user.id_parent
        return False
