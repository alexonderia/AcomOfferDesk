from __future__ import annotations

from dataclasses import dataclass

from app.domain.permissions import get_known_permissions, get_permissions_for_role


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
    app_roles = frozenset(role for role in normalized_roles if role.startswith("app."))
    delegation_roles = frozenset(role for role in normalized_roles if role.startswith("delegation."))
    return CurrentUser(
        user_id=user_id,
        role_id=role_id,
        status=status,
        permissions=permissions,
        keycloak_roles=normalized_roles,
        app_roles=app_roles,
        delegation_roles=delegation_roles,
    )
