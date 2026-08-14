from app.core.config import settings
from app.domain.auth_context import CurrentUser, build_current_user
from app.domain.permissions import PermissionCodes


def test_local_auth_context_uses_application_permission_ceiling() -> None:
    current_user = build_current_user(
        user_id="admin-1",
        role_id=settings.admin_role_id,
        status="active",
    )

    assert PermissionCodes.USERS_READ in current_user.permissions
    assert current_user.identity_roles == frozenset()
    assert current_user.app_roles == frozenset()
    assert current_user.delegation_roles == frozenset()


def test_current_user_does_not_require_provider_specific_claims() -> None:
    current_user = CurrentUser(
        user_id="u-1",
        role_id=settings.economist_role_id,
        status="active",
        permissions=frozenset({PermissionCodes.REQUESTS_READ}),
    )

    assert current_user.has_permission(PermissionCodes.REQUESTS_READ)
