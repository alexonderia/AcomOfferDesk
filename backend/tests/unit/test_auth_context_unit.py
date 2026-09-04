from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.permissions import PermissionCodes


def test_current_user_permissions_are_explicit_iam_context() -> None:
    current_user = CurrentUser(
        user_id="admin-1",
        iam_account_id="00000000-0000-4000-8000-000000000001",
        iam_session_id="00000000-0000-4000-8000-000000000002",
        system_role="admin",
        role_id=settings.admin_role_id,
        status="active",
        permissions=frozenset({PermissionCodes.USERS_READ}),
    )

    assert PermissionCodes.USERS_READ in current_user.permissions
    assert current_user.system_role == "admin"
    assert not hasattr(current_user, "identity_roles")
    assert not hasattr(current_user, "app_roles")
    assert not hasattr(current_user, "delegation_roles")


def test_current_user_does_not_require_provider_specific_claims() -> None:
    current_user = CurrentUser(
        user_id="u-1",
        iam_account_id="00000000-0000-4000-8000-000000000001",
        iam_session_id="00000000-0000-4000-8000-000000000002",
        system_role="economist",
        role_id=settings.economist_role_id,
        status="active",
        permissions=frozenset({PermissionCodes.REQUESTS_READ}),
    )

    assert current_user.has_permission(PermissionCodes.REQUESTS_READ)
