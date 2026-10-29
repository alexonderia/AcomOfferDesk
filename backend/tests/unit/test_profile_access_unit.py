from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.permissions import PermissionCodes
from app.services.users import UserQueryService


def _current_user(*, user_id: str, role_id: int) -> CurrentUser:
    return CurrentUser(
        user_id=user_id,
        iam_account_id="00000000-0000-4000-8000-000000000001",
        iam_session_id="00000000-0000-4000-8000-000000000002",
        system_role="admin",
        role_id=role_id,
        status="active",
        permissions=frozenset({PermissionCodes.USERS_READ}),
        required_actions=frozenset(),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("manager_role_id", [settings.superadmin_role_id, settings.admin_role_id])
async def test_admin_roles_can_read_subordinate_profile_without_legacy_hierarchy(manager_role_id: int) -> None:
    subordinate = SimpleNamespace(id="target-user", id_role=settings.economist_role_id, id_parent=None, status="active")
    profile = SimpleNamespace(full_name="Target User", phone="+79990000000", mail="target@example.com")
    users = AsyncMock()
    users.get_by_id = AsyncMock(return_value=subordinate)
    users.list_by_role_ids_with_profiles_and_roles = AsyncMock(return_value=[(subordinate, profile, None)])
    periods = AsyncMock()
    periods.get_active_for_user = AsyncMock(return_value=None)
    periods.list_for_user = AsyncMock(return_value=[])

    result = await UserQueryService(users, periods).get_subordinate_profile(
        current_user=_current_user(user_id="manager", role_id=manager_role_id),
        subordinate_user_id="target-user",
    )

    assert result.user_id == "target-user"
    assert result.full_name == "Target User"
