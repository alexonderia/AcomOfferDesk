from __future__ import annotations

from fastapi import Depends, Request

from app.core.config import settings
from app.core.uow import UnitOfWork
from app.domain.authentication import IamAccessClaims, decode_iam_access_token
from app.domain.auth_context import CurrentUser
from app.domain.authorization import require_permission as enforce_permission
from app.domain.exceptions import Unauthorized


async def get_uow() -> UnitOfWork:
    return UnitOfWork()


async def resolve_iam_current_user(claims: IamAccessClaims) -> CurrentUser:
    async with UnitOfWork() as uow:
        binding = await uow.user_auth_accounts.get_by_provider_subject(
            provider="iam",
            subject=claims.account_id,
        )
        if binding is None:
            raise Unauthorized("Invalid IAM binding")
        user = await uow.users.get_by_id(binding.id_user)
        if user is None or user.status not in {"active", "review"}:
            raise Unauthorized("User is not active")
        return CurrentUser(
            user_id=user.id,
            iam_account_id=claims.account_id,
            iam_session_id=claims.session_id,
            system_role=claims.system_role,
            role_id=claims.role_id,
            status=user.status,
            permissions=claims.permissions,
            required_actions=claims.required_actions,
        )


async def get_current_user(request: Request) -> CurrentUser:
    raw_token = request.cookies.get(settings.iam_access_cookie_name, "").strip()
    if not raw_token:
        raise Unauthorized("Missing credentials")
    return await resolve_iam_current_user(decode_iam_access_token(raw_token))


def require_permission(permission: str):
    async def _dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        enforce_permission(current_user, permission)
        return current_user

    return _dependency
