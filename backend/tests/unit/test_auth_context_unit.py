"""Unit tests for CurrentUser construction from Keycloak roles.

Focus:
- known permission codes are preserved;
- app/delegation role namespaces are split correctly;
- unknown roles are ignored as atomic permissions.
"""

from app.domain.auth_context import build_current_user_from_keycloak
from app.domain.permissions import PermissionCodes


def test_build_current_user_from_keycloak_splits_known_permission_and_role_prefixes():
    current_user = build_current_user_from_keycloak(
        user_id="u-1",
        role_id=10,
        status="active",
        api_roles=frozenset(
            {
                PermissionCodes.REQUESTS_READ,
                PermissionCodes.OFFERS_WORKSPACE_READ,
                "app.admin",
                "delegation.request-reader",
                "unknown.atomic.permission",
                "",
                "  ",
            }
        ),
    )

    assert current_user.permissions == frozenset(
        {
            PermissionCodes.REQUESTS_READ,
            PermissionCodes.OFFERS_WORKSPACE_READ,
        }
    )
    assert current_user.app_roles == frozenset({"app.admin"})
    assert current_user.delegation_roles == frozenset({"delegation.request-reader"})
    assert "app.admin" not in current_user.permissions
    assert "delegation.request-reader" not in current_user.permissions
    assert "unknown.atomic.permission" not in current_user.permissions


def test_build_current_user_from_keycloak_empty_api_roles_produces_empty_sets():
    current_user = build_current_user_from_keycloak(
        user_id="u-2",
        role_id=3,
        status="active",
        api_roles=frozenset(),
    )

    assert current_user.permissions == frozenset()
    assert current_user.app_roles == frozenset()
    assert current_user.delegation_roles == frozenset()
    assert current_user.keycloak_roles == frozenset()
