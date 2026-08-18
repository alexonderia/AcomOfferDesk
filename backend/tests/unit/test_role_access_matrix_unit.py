"""Unit tests for backend permission source-of-truth map.

These tests intentionally validate `domain.permissions` instead of parsing
markdown docs, to keep checks deterministic and non-brittle.
"""

from __future__ import annotations

import pytest

from app.core.config import settings
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
        settings.security_officer_role_id,
    }


def test_superadmin_has_all_known_permissions() -> None:
    role_map = get_role_permissions_map()
    assert role_map[settings.superadmin_role_id] == get_known_permissions()


def test_role_map_contains_only_atomic_permissions() -> None:
    role_map = get_role_permissions_map()
    flattened = {permission for permissions in role_map.values() for permission in permissions}

    assert all(not permission.startswith("app.") for permission in flattened)
    assert all(not permission.startswith("delegation.") for permission in flattened)


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


def test_economist_role_includes_module_dashboard_permissions() -> None:
    role_map = get_role_permissions_map()
    economist_permissions = role_map[settings.economist_role_id]

    assert PermissionCodes.DASHBOARD_PROCESS_READ in economist_permissions
    assert PermissionCodes.DASHBOARD_SAVINGS_READ in economist_permissions


def test_operator_role_can_read_offers_on_request_without_workspace() -> None:
    role_map = get_role_permissions_map()
    operator_permissions = role_map[settings.operator_role_id]

    assert PermissionCodes.REQUESTS_READ in operator_permissions
    assert PermissionCodes.OFFERS_CONTRACTOR_INFO_READ in operator_permissions
    assert PermissionCodes.OFFERS_WORKSPACE_READ not in operator_permissions
    assert PermissionCodes.CHAT_READ not in operator_permissions


def test_project_manager_role_is_read_only_for_requests_offers_and_chats() -> None:
    role_map = get_role_permissions_map()
    pm_permissions = role_map[settings.project_manager_role_id]

    assert PermissionCodes.REQUESTS_READ in pm_permissions
    assert PermissionCodes.OFFERS_WORKSPACE_READ in pm_permissions
    assert PermissionCodes.CHAT_READ in pm_permissions
    assert PermissionCodes.REQUESTS_OWNER_CHANGE in pm_permissions
    assert PermissionCodes.REQUESTS_UPDATE not in pm_permissions
    assert PermissionCodes.OFFERS_STATUS_UPDATE not in pm_permissions
    assert PermissionCodes.CHAT_MESSAGE_SEND not in pm_permissions


def test_staff_roles_can_read_contractors_without_status_update_rights() -> None:
    role_map = get_role_permissions_map()

    for role_id in (
        settings.project_manager_role_id,
        settings.lead_economist_role_id,
        settings.economist_role_id,
    ):
        permissions = role_map[role_id]
        assert PermissionCodes.CONTRACTORS_READ in permissions
        assert PermissionCodes.CONTRACTORS_PROFILE_READ in permissions
        assert PermissionCodes.CONTRACTORS_PROFILE_STATUS_UPDATE not in permissions


def test_security_officer_role_has_only_expected_permissions() -> None:
    role_map = get_role_permissions_map()

    assert role_map[settings.security_officer_role_id] == frozenset(
        {
            PermissionCodes.PROFILE_MANAGE_OWN,
            PermissionCodes.FEEDBACK_CREATE,
            PermissionCodes.UNITS_READ,
            PermissionCodes.CONTRACTORS_READ,
            PermissionCodes.CONTRACTORS_PROFILE_READ,
            PermissionCodes.CONTRACTORS_PROFILE_STATUS_UPDATE,
            PermissionCodes.USERS_REGISTRATION_INVITE,
            PermissionCodes.USERS_REGISTRATION_APPROVE,
        }
    )


def test_units_permissions_are_granted_to_hierarchy_roles_for_subtree_management() -> None:
    role_map = get_role_permissions_map()
    unit_permissions = {
        PermissionCodes.UNITS_READ,
        PermissionCodes.UNITS_CREATE,
        PermissionCodes.UNITS_UPDATE,
        PermissionCodes.UNITS_MEMBERS_MANAGE,
    }

    assert unit_permissions.issubset(role_map[settings.superadmin_role_id])
    assert unit_permissions.issubset(role_map[settings.admin_role_id])

    for role_id in (
        settings.project_manager_role_id,
        settings.lead_economist_role_id,
        settings.economist_role_id,
    ):
        assert unit_permissions.issubset(role_map[role_id])

    assert {PermissionCodes.UNITS_READ}.issubset(role_map[settings.operator_role_id])
    assert unit_permissions.isdisjoint(role_map[settings.operator_role_id] - {PermissionCodes.UNITS_READ})
    assert unit_permissions.isdisjoint(role_map[settings.contractor_role_id])

    assert role_map[settings.security_officer_role_id] == {
        PermissionCodes.UNITS_READ,
    } | {
        PermissionCodes.PROFILE_MANAGE_OWN,
        PermissionCodes.FEEDBACK_CREATE,
        PermissionCodes.CONTRACTORS_READ,
        PermissionCodes.CONTRACTORS_PROFILE_READ,
        PermissionCodes.CONTRACTORS_PROFILE_STATUS_UPDATE,
        PermissionCodes.USERS_REGISTRATION_INVITE,
        PermissionCodes.USERS_REGISTRATION_APPROVE,
    }
