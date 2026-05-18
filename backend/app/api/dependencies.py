from __future__ import annotations

import logging

from fastapi import Depends, Header

from app.core.config import settings
from app.core.uow import UnitOfWork
from app.domain.auth_context import CurrentUser, build_current_user_from_keycloak
from app.domain.authorization import require_permission as enforce_permission
from app.domain.exceptions import Unauthorized
from app.services.identity_sync import IdentitySyncService
from app.services.keycloak_oidc import decode_keycloak_access_token

logger = logging.getLogger(__name__)


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
    current_user = build_current_user_from_keycloak_claims(
        user_id=synced.user.id,
        role_id=synced.user.id_role,
        status=synced.user.status,
        keycloak_api_roles=claims.api_roles,
    )
    if not claims.api_roles:
        logger.warning(
            "keycloak_api_roles_empty user_id=%s keycloak_subject=%s keycloak_api_client_id=%s",
            synced.user.id,
            claims.subject,
            settings.keycloak_api_client_id,
        )
    logger.debug(
        "current_user_from_keycloak user_id=%s keycloak_subject=%s keycloak_api_roles_count=%s app_roles=%s delegation_roles=%s",
        current_user.user_id,
        claims.subject,
        len(claims.api_roles),
        sorted(current_user.app_roles),
        sorted(current_user.delegation_roles),
    )
    return current_user


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
        enforce_permission(current_user, permission)
        return current_user

    return _dependency
