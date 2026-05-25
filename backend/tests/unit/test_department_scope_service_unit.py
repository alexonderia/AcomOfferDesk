from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.services.department_scope import DepartmentScopeService


class _UsersRepo:
    def __init__(self) -> None:
        self._users = {
            "pm-1": SimpleNamespace(id="pm-1", id_role=settings.project_manager_role_id, id_parent=None, status="active"),
            "lead-1": SimpleNamespace(id="lead-1", id_role=settings.lead_economist_role_id, id_parent="pm-1", status="active"),
            "eco-1": SimpleNamespace(id="eco-1", id_role=settings.economist_role_id, id_parent="lead-1", status="active"),
            "eco-2": SimpleNamespace(id="eco-2", id_role=settings.economist_role_id, id_parent="lead-1", status="active"),
            "pm-2": SimpleNamespace(id="pm-2", id_role=settings.project_manager_role_id, id_parent=None, status="active"),
            "lead-2": SimpleNamespace(id="lead-2", id_role=settings.lead_economist_role_id, id_parent="pm-2", status="active"),
        }

    async def get_by_id(self, user_id: str):
        return self._users.get(user_id)

    async def list_active_user_parent_pairs(self):
        return [(item.id, item.id_parent) for item in self._users.values() if item.status == "active"]


def _current_user(*, user_id: str, role_id: int) -> CurrentUser:
    return CurrentUser(
        user_id=user_id,
        role_id=role_id,
        status="active",
        permissions=frozenset(),
    )


@pytest.mark.asyncio
async def test_department_scope_for_economist_resolves_project_manager_subtree():
    service = DepartmentScopeService(_UsersRepo())

    owner_ids = await service.resolve_department_owner_ids_for_current_user(
        current_user=_current_user(user_id="eco-1", role_id=settings.economist_role_id),
    )

    assert set(owner_ids) == {"pm-1", "lead-1", "eco-1", "eco-2"}


@pytest.mark.asyncio
async def test_department_scope_membership_check_is_strict_to_current_department():
    service = DepartmentScopeService(_UsersRepo())

    current_user = _current_user(user_id="lead-1", role_id=settings.lead_economist_role_id)
    assert await service.is_user_in_current_user_department(
        current_user=current_user,
        target_user_id="eco-2",
    )
    assert not await service.is_user_in_current_user_department(
        current_user=current_user,
        target_user_id="lead-2",
    )
