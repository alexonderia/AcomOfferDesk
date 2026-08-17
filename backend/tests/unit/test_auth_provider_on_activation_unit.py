from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.permissions import PermissionCodes
from app.services.users import UserStatusService


@pytest.mark.asyncio
async def test_contractor_activation_updates_local_status_without_auth_provider() -> None:
    user = SimpleNamespace(id="contractor-1", id_role=settings.contractor_role_id, status="review")
    users = AsyncMock()
    users.get_by_id = AsyncMock(return_value=user)

    async def update_status(target, next_status: str) -> None:
        target.status = next_status

    users.update_status = AsyncMock(side_effect=update_status)
    profiles = AsyncMock()
    profiles.get_by_id = AsyncMock(return_value=SimpleNamespace(mail=None))
    service = UserStatusService(users=users, profiles=profiles, user_auth_accounts=AsyncMock())

    result = await service.update_statuses(
        current_user=CurrentUser(
            user_id="admin-1",
            iam_account_id="00000000-0000-4000-8000-000000000001",
            iam_session_id="00000000-0000-4000-8000-000000000002",
            system_role="admin",
            role_id=settings.admin_role_id,
            status="active",
            permissions=frozenset({PermissionCodes.USERS_STATUS_UPDATE}),
        ),
        user_id=user.id,
        user_status="active",
    )

    assert result.user_status == "active"
    users.update_status.assert_awaited_once()
