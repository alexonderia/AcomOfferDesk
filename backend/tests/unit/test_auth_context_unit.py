"""Unit tests for CurrentUser construction from Keycloak roles.

Focus:
- known permission codes are preserved;
- app/delegation role namespaces are split correctly;
- unknown roles are ignored as atomic permissions.
"""

from app.core.config import settings
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


def test_build_current_user_from_keycloak_app_superadmin_without_atomic_permissions_has_no_permissions():
    current_user = build_current_user_from_keycloak(
        user_id="u-3",
        role_id=1,
        status="active",
        api_roles=frozenset({"app.superadmin"}),
    )

    assert current_user.permissions == frozenset()
    assert current_user.app_roles == frozenset({"app.superadmin"})
    assert "app.superadmin" not in current_user.permissions


def test_build_current_user_from_keycloak_caps_jwt_permissions_to_local_role_ceiling():
    current_user = build_current_user_from_keycloak(
        user_id="contractor-1",
        role_id=settings.contractor_role_id,
        status="active",
        api_roles=frozenset(
            {
                PermissionCodes.REQUESTS_OPEN_READ,
                PermissionCodes.NORMATIVE_FILES_CREATE,
                PermissionCodes.REQUESTS_CREATE,
                PermissionCodes.USERS_READ,
            }
        ),
    )

    assert PermissionCodes.REQUESTS_OPEN_READ in current_user.permissions
    assert PermissionCodes.NORMATIVE_FILES_CREATE not in current_user.permissions
    assert PermissionCodes.REQUESTS_CREATE not in current_user.permissions
    assert PermissionCodes.USERS_READ not in current_user.permissions


def test_build_current_user_from_keycloak_delegation_roles_do_not_become_permissions():
    current_user = build_current_user_from_keycloak(
        user_id="u-4",
        role_id=3,
        status="active",
        api_roles=frozenset({"delegation.request-reader", "delegation.offer-reader"}),
    )

    assert current_user.permissions == frozenset()
    assert current_user.delegation_roles == frozenset(
        {"delegation.request-reader", "delegation.offer-reader"}
    )
