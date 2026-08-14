from __future__ import annotations

from fastapi import Depends

from app.core.uow import UnitOfWork
from app.domain.authentication import reject_unavailable_authentication
from app.domain.auth_context import CurrentUser
from app.domain.authorization import require_permission as enforce_permission


async def get_uow() -> UnitOfWork:
    return UnitOfWork()


async def get_current_user() -> CurrentUser:
    """Reject every protected request until the new IAM adapter is connected."""

    reject_unavailable_authentication()


def require_permission(permission: str):
    async def _dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        enforce_permission(current_user, permission)
        return current_user

    return _dependency
