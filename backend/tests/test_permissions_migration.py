import inspect

import pytest

from app.api.dependencies import require_permission
from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.exceptions import Forbidden
from app.domain.permissions import PermissionCodes


def _dependency_callable(permission: str):
    dependency = require_permission(permission)
    assert inspect.iscoroutinefunction(dependency)
    return dependency


@pytest.mark.asyncio
async def test_permission_dependency_accepts_neutral_current_user() -> None:
    current_user = CurrentUser(
        user_id="u-1",
        role_id=settings.economist_role_id,
        status="active",
        permissions=frozenset({PermissionCodes.REQUESTS_READ}),
    )

    resolved = await _dependency_callable(PermissionCodes.REQUESTS_READ)(current_user)

    assert resolved is current_user


@pytest.mark.asyncio
async def test_permission_dependency_rejects_missing_permission() -> None:
    current_user = CurrentUser(
        user_id="u-1",
        role_id=settings.economist_role_id,
        status="active",
        permissions=frozenset(),
    )

    with pytest.raises(Forbidden):
        await _dependency_callable(PermissionCodes.REQUESTS_READ)(current_user)
