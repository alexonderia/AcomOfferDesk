from __future__ import annotations

import logging
from dataclasses import dataclass

from app.domain.permissions import get_known_permissions, get_permissions_for_role
from app.services.keycloak_app_roles import role_mapping_by_local_role_id

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CurrentUser:
    user_id: str
    role_id: int
    status: str
    permissions: frozenset[str]
    keycloak_roles: frozenset[str] = frozenset()
    app_roles: frozenset[str] = frozenset()
    delegation_roles: frozenset[str] = frozenset()

    def has_permission(self, permission: str) -> bool:
        normalized_permission = permission.strip()
        return bool(normalized_permission and normalized_permission in self.permissions)


def build_current_user(*, user_id: str, role_id: int, status: str) -> CurrentUser:
    return CurrentUser(
        user_id=user_id,
        role_id=role_id,
        status=status,
        permissions=get_permissions_for_role(role_id),
    )


def build_current_user_from_keycloak(
    *,
    user_id: str,
    role_id: int,
    status: str,
    api_roles: frozenset[str],
) -> CurrentUser:
    normalized_roles = frozenset(
        role.strip()
        for role in api_roles
        if isinstance(role, str) and role.strip()
    )
    known_permissions = get_known_permissions()
    permissions = frozenset(role for role in normalized_roles if role in known_permissions)
    role_ceiling = get_permissions_for_role(role_id)
    if role_ceiling:
        permissions = permissions & role_ceiling
    app_roles = frozenset(role for role in normalized_roles if role.startswith("app."))
    if not permissions and role_ceiling:
        expected_app_role = role_mapping_by_local_role_id().get(role_id)
        if expected_app_role and expected_app_role in app_roles:
            permissions = role_ceiling
    delegation_roles = frozenset(role for role in normalized_roles if role.startswith("delegation."))
    if (app_roles or delegation_roles) and not permissions:
        logger.warning(
            "keycloak_user_without_atomic_permissions user_id=%s app_roles=%s delegation_roles=%s keycloak_roles_count=%s",
            user_id,
            sorted(app_roles),
            sorted(delegation_roles),
            len(normalized_roles),
        )
    return CurrentUser(
        user_id=user_id,
        role_id=role_id,
        status=status,
        permissions=permissions,
        keycloak_roles=normalized_roles,
        app_roles=app_roles,
        delegation_roles=delegation_roles,
    )
