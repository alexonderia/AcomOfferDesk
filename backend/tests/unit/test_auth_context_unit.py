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


def test_build_current_user_from_keycloak_app_role_only_uses_local_role_ceiling():
    """JWT may carry only app.* composite role without leaf permission codes."""
    current_user = build_current_user_from_keycloak(
        user_id="admin-vvv",
        role_id=settings.admin_role_id,
        status="active",
        api_roles=frozenset({"app.admin"}),
    )

    assert PermissionCodes.USERS_READ in current_user.permissions
    assert PermissionCodes.USERS_CREATE in current_user.permissions
    assert PermissionCodes.REQUESTS_READ not in current_user.permissions
    assert current_user.app_roles == frozenset({"app.admin"})


def test_build_current_user_from_keycloak_app_superadmin_only_uses_local_role_ceiling():
    current_user = build_current_user_from_keycloak(
        user_id="u-3",
        role_id=settings.superadmin_role_id,
        status="active",
        api_roles=frozenset({"app.superadmin"}),
    )

    assert PermissionCodes.USERS_READ in current_user.permissions
    assert PermissionCodes.REQUESTS_CREATE in current_user.permissions
    assert current_user.app_roles == frozenset({"app.superadmin"})


def test_build_current_user_from_keycloak_app_project_manager_uses_contractor_read_ceiling():
    current_user = build_current_user_from_keycloak(
        user_id="pm-1",
        role_id=settings.project_manager_role_id,
        status="active",
        api_roles=frozenset({"app.project_manager"}),
    )

    assert PermissionCodes.CONTRACTORS_READ in current_user.permissions
    assert PermissionCodes.CONTRACTORS_PROFILE_READ in current_user.permissions
    assert PermissionCodes.CONTRACTORS_PROFILE_STATUS_UPDATE not in current_user.permissions
    assert current_user.app_roles == frozenset({"app.project_manager"})


def test_build_current_user_from_keycloak_mismatched_app_role_does_not_use_ceiling_fallback():
    current_user = build_current_user_from_keycloak(
        user_id="u-mismatch",
        role_id=settings.admin_role_id,
        status="active",
        api_roles=frozenset({"app.contractor"}),
    )

    assert current_user.permissions == frozenset()
    assert current_user.app_roles == frozenset({"app.contractor"})


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


def test_build_current_user_from_keycloak_grants_department_permission_via_delegation_role():
    current_user = build_current_user_from_keycloak(
        user_id="u-dept-1",
        role_id=settings.economist_role_id,
        status="active",
        api_roles=frozenset(
            {
                PermissionCodes.REQUESTS_READ,
                "delegation.department.requests.read",
            }
        ),
    )

    assert PermissionCodes.REQUESTS_READ in current_user.permissions
    assert PermissionCodes.DEPARTMENT_REQUESTS_READ in current_user.permissions
    assert "delegation.department.requests.read" in current_user.delegation_roles


def test_build_current_user_from_keycloak_grants_contractor_permissions_via_delegation_role():
    current_user = build_current_user_from_keycloak(
        user_id="u-contractor-delegation",
        role_id=settings.lead_economist_role_id,
        status="active",
        api_roles=frozenset(
            {
                PermissionCodes.REQUESTS_READ,
                "delegation.contractors.profile.status.update",
            }
        ),
    )

    assert PermissionCodes.CONTRACTORS_READ in current_user.permissions
    assert PermissionCodes.CONTRACTORS_PROFILE_READ in current_user.permissions
    assert PermissionCodes.CONTRACTORS_PROFILE_STATUS_UPDATE in current_user.permissions
    assert "delegation.contractors.profile.status.update" in current_user.delegation_roles


def test_build_current_user_from_keycloak_ignores_contractor_permission_without_delegation_role():
    current_user = build_current_user_from_keycloak(
        user_id="u-contractor-raw-atomic",
        role_id=settings.lead_economist_role_id,
        status="active",
        api_roles=frozenset(
            {
                PermissionCodes.REQUESTS_READ,
                PermissionCodes.CONTRACTORS_READ,
                PermissionCodes.CONTRACTORS_PROFILE_STATUS_UPDATE,
            }
        ),
    )

    assert PermissionCodes.REQUESTS_READ in current_user.permissions
    assert PermissionCodes.CONTRACTORS_READ not in current_user.permissions
    assert PermissionCodes.CONTRACTORS_PROFILE_STATUS_UPDATE not in current_user.permissions


def test_build_current_user_from_keycloak_ignores_department_permission_without_delegation_role():
    current_user = build_current_user_from_keycloak(
        user_id="u-dept-raw-atomic",
        role_id=settings.economist_role_id,
        status="active",
        api_roles=frozenset(
            {
                PermissionCodes.REQUESTS_READ,
                PermissionCodes.DEPARTMENT_REQUESTS_READ,
            }
        ),
    )

    assert PermissionCodes.REQUESTS_READ in current_user.permissions
    assert PermissionCodes.DEPARTMENT_REQUESTS_READ not in current_user.permissions


def test_build_current_user_from_keycloak_does_not_infer_department_permission_from_regular_permission():
    current_user = build_current_user_from_keycloak(
        user_id="u-dept-2",
        role_id=settings.economist_role_id,
        status="active",
        api_roles=frozenset({PermissionCodes.REQUESTS_READ}),
    )

    assert PermissionCodes.REQUESTS_READ in current_user.permissions
    assert PermissionCodes.DEPARTMENT_REQUESTS_READ not in current_user.permissions
