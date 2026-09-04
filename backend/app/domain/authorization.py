from __future__ import annotations

from collections.abc import Iterable

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.exceptions import Forbidden
from app.domain.permissions import PermissionCodes


REVIEW_ALLOWED_PERMISSIONS = frozenset(
    {
        PermissionCodes.PROFILE_MANAGE_OWN,
        PermissionCodes.COMPANY_CONTACTS_MANAGE_OWN,
    }
)
FIRST_LOGIN_ALLOWED_PERMISSIONS = REVIEW_ALLOWED_PERMISSIONS


def has_permission(current_user: CurrentUser, permission_code: str) -> bool:
    if not current_user.has_permission(permission_code):
        return False
    if current_user.status == "active":
        if current_user.onboarding_state == "first_login":
            return permission_code in FIRST_LOGIN_ALLOWED_PERMISSIONS
        return True
    if current_user.status == "review":
        return (
            current_user.role_id == settings.contractor_role_id
            and permission_code in REVIEW_ALLOWED_PERMISSIONS
        )
    return False


def require_permission(
    current_user: CurrentUser,
    permission_code: str,
    *,
    message: str = "Insufficient permissions",
) -> None:
    if not has_permission(current_user, permission_code):
        raise Forbidden(message)


def require_any_permission(
    current_user: CurrentUser,
    permission_codes: Iterable[str],
    *,
    message: str = "Insufficient permissions",
) -> None:
    if not any(has_permission(current_user, permission_code) for permission_code in permission_codes):
        raise Forbidden(message)
