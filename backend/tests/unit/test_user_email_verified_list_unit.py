from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.domain.permissions import PermissionCodes
from app.services.users import UserQueryService


class _UsersRepo:
    async def list_users_with_profiles(self, role_id=None):
        _ = role_id
        user = SimpleNamespace(
            id="user-1",
            id_role=settings.economist_role_id,
            id_parent=None,
            status="active",
        )
        profile = SimpleNamespace(full_name="Иван Петров", phone=None, mail="ivan@example.com")
        return [(user, profile)]

    async def map_primary_email_verified(self, *, user_ids: list[str]) -> dict[str, bool]:
        return {user_id: user_id == "user-1" for user_id in user_ids}


class _UserStatusPeriodsRepo:
    async def list_active_for_users(self, *, user_ids):
        _ = user_ids
        return {}


@pytest.mark.asyncio
async def test_list_users_includes_primary_email_verified(make_current_user):
    service = UserQueryService(_UsersRepo(), _UserStatusPeriodsRepo())
    current_user = make_current_user(
        user_id="superadmin-1",
        role_id=settings.superadmin_role_id,
        permissions={PermissionCodes.USERS_READ},
    )

    items = await service.list_users(current_user)

    assert len(items) == 1
    assert items[0].user_id == "user-1"
    assert items[0].email_verified is True
