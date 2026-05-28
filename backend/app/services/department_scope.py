from __future__ import annotations

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.repositories.users import UserRepository


class DepartmentScopeService:
    def __init__(self, users: UserRepository):
        self._users = users

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

    async def resolve_department_owner_ids_for_current_user(
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

    async def is_user_in_current_user_department(
        self,
        *,
        current_user: CurrentUser,
        target_user_id: str,
    ) -> bool:
        department_owner_ids = await self.resolve_department_owner_ids_for_current_user(current_user=current_user)
        return target_user_id in set(department_owner_ids)
