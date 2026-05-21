"""Unit tests for backend permission source-of-truth map.

These tests intentionally validate `domain.permissions` instead of parsing
markdown docs, to keep checks deterministic and non-brittle.
"""

from __future__ import annotations

import pytest

from app.core.config import settings
from app.domain.auth_context import build_current_user_from_keycloak
from app.domain.authorization import REVIEW_ALLOWED_PERMISSIONS, has_permission
from app.domain.permissions import PermissionCodes, get_known_permissions, get_role_permissions_map


def test_role_permissions_map_covers_all_known_permissions() -> None:
    known = get_known_permissions()
    role_map = get_role_permissions_map()
    flattened = {permission for permissions in role_map.values() for permission in permissions}

    assert flattened == known


def test_role_permissions_map_has_no_unknown_permissions() -> None:
    known = get_known_permissions()
    role_map = get_role_permissions_map()

    unknown = {
        permission
        for permissions in role_map.values()
        for permission in permissions
        if permission not in known
    }
    assert unknown == set()


def test_get_role_permissions_map_contains_expected_role_ids() -> None:
    role_map = get_role_permissions_map()

    assert set(role_map) == {
        settings.superadmin_role_id,
        settings.admin_role_id,
        settings.contractor_role_id,
        settings.project_manager_role_id,
        settings.lead_economist_role_id,
        settings.economist_role_id,
        settings.operator_role_id,
    }


def test_superadmin_has_all_known_permissions() -> None:
    role_map = get_role_permissions_map()
    assert role_map[settings.superadmin_role_id] == get_known_permissions()


def test_role_map_contains_only_atomic_permissions() -> None:
    role_map = get_role_permissions_map()
    flattened = {permission for permissions in role_map.values() for permission in permissions}

    assert all(not permission.startswith("app.") for permission in flattened)
    assert all(not permission.startswith("delegation.") for permission in flattened)


def test_app_roles_do_not_grant_atomic_permissions_by_themselves() -> None:
    current_user = build_current_user_from_keycloak(
        user_id="user-app-only",
        role_id=settings.superadmin_role_id,
        status="active",
        api_roles=frozenset({"app.superadmin", "app.admin"}),
    )

    assert current_user.permissions == frozenset()
    assert current_user.app_roles == frozenset({"app.superadmin", "app.admin"})


def test_delegation_roles_do_not_grant_atomic_permissions_by_themselves() -> None:
    current_user = build_current_user_from_keycloak(
        user_id="user-delegation-only",
        role_id=settings.project_manager_role_id,
        status="active",
        api_roles=frozenset({"delegation.request-reader", "delegation.offer-reader"}),
    )

    assert current_user.permissions == frozenset()
    assert current_user.delegation_roles == frozenset(
        {"delegation.request-reader", "delegation.offer-reader"}
    )


@pytest.mark.parametrize("permission", sorted(get_known_permissions()))
def test_review_contractor_has_only_onboarding_safe_permissions(
    make_current_user,
    permission: str,
) -> None:
    review_user = make_current_user(
        role_id=settings.contractor_role_id,
        status="review",
        permissions=set(get_known_permissions()),
    )

    assert has_permission(review_user, permission) is (permission in REVIEW_ALLOWED_PERMISSIONS)


@pytest.mark.parametrize("status", ["inactive", "blacklist"])
def test_inactive_and_blacklist_never_pass_protected_checks(make_current_user, status: str) -> None:
    blocked_user = make_current_user(
        role_id=settings.lead_economist_role_id,
        status=status,
        permissions={PermissionCodes.REQUESTS_READ, PermissionCodes.OFFERS_STATUS_UPDATE},
    )

    assert has_permission(blocked_user, PermissionCodes.REQUESTS_READ) is False
    assert has_permission(blocked_user, PermissionCodes.OFFERS_STATUS_UPDATE) is False


def test_economist_role_includes_plan_dashboard_permission() -> None:
    role_map = get_role_permissions_map()

    assert PermissionCodes.DASHBOARD_PLANS_READ in role_map[settings.economist_role_id]
