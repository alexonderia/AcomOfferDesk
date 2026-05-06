from __future__ import annotations

from fastapi import Depends, Header

from app.core.uow import UnitOfWork
from app.domain.auth_context import CurrentUser, build_current_user_from_keycloak
from app.domain.exceptions import Forbidden, Unauthorized
from app.services.identity_sync import IdentitySyncService
from app.services.keycloak_oidc import decode_keycloak_access_token


def build_current_user_from_keycloak_claims(
    *,
    user_id: str,
    role_id: int,
    status: str,
    keycloak_api_roles: frozenset[str],
) -> CurrentUser:
    return build_current_user_from_keycloak(
        user_id=user_id,
        role_id=role_id,
        status=status,
        api_roles=keycloak_api_roles,
    )


async def get_uow() -> UnitOfWork:
    return UnitOfWork()


async def _get_current_user_from_keycloak_token(token: str, *, uow: UnitOfWork) -> CurrentUser:
    claims = await decode_keycloak_access_token(token)
    sync_service = IdentitySyncService(
        users=uow.users,
        user_auth_accounts=uow.user_auth_accounts,
        user_contact_channels=uow.user_contact_channels,
        profiles=uow.profiles,
    )
    synced = await sync_service.sync_keycloak_identity(claims, allow_user_creation=False)
    return build_current_user_from_keycloak_claims(
        user_id=synced.user.id,
        role_id=synced.user.id_role,
        status=synced.user.status,
        keycloak_api_roles=claims.api_roles,
    )


async def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    uow: UnitOfWork = Depends(get_uow),
) -> CurrentUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise Unauthorized("Missing credentials")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise Unauthorized("Missing credentials")

    async with uow:
        return await _get_current_user_from_keycloak_token(token, uow=uow)


def require_permission(permission: str):
    async def _dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.status != "active":
            raise Forbidden("User is not active")
        if not current_user.has_permission(permission):
            raise Forbidden("Insufficient permissions")
        return current_user

    return _dependency
