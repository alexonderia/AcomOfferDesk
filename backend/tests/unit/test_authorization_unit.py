"""Unit tests for `authorization.has_permission(...)`.

Focus:
- active users with permission are allowed;
- missing permission is denied;
- review contractor path is limited to onboarding-safe permissions;
- inactive/blacklist users are denied.
"""

import pytest

from app.core.config import settings
from app.domain.authorization import has_permission
from app.domain.permissions import PermissionCodes


def test_has_permission_active_user_with_permission_returns_true(make_current_user):
    current_user = make_current_user(permissions={PermissionCodes.USERS_READ})

    assert has_permission(current_user, PermissionCodes.USERS_READ) is True


def test_has_permission_active_user_without_permission_returns_false(make_current_user):
    current_user = make_current_user(permissions={PermissionCodes.REQUESTS_READ})

    assert has_permission(current_user, PermissionCodes.USERS_READ) is False


def test_has_permission_review_contractor_allows_only_onboarding_permissions(make_current_user):
    review_contractor = make_current_user(
        role_id=settings.contractor_role_id,
        status="review",
        permissions={
            PermissionCodes.PROFILE_MANAGE_OWN,
            PermissionCodes.COMPANY_CONTACTS_MANAGE_OWN,
            PermissionCodes.REQUESTS_OPEN_READ,
        },
    )

    assert has_permission(review_contractor, PermissionCodes.PROFILE_MANAGE_OWN) is True
    assert has_permission(review_contractor, PermissionCodes.COMPANY_CONTACTS_MANAGE_OWN) is True
    assert has_permission(review_contractor, PermissionCodes.REQUESTS_OPEN_READ) is False


@pytest.mark.parametrize("status", ["inactive", "blacklist"])
def test_has_permission_non_active_blocked_even_if_permission_present(make_current_user, status):
    current_user = make_current_user(
        status=status,
        permissions={PermissionCodes.USERS_READ},
    )

    assert has_permission(current_user, PermissionCodes.USERS_READ) is False


def test_has_permission_review_non_contractor_blocked(make_current_user):
    review_user = make_current_user(
        role_id=settings.economist_role_id,
        status="review",
        permissions={PermissionCodes.PROFILE_MANAGE_OWN},
    )

    assert has_permission(review_user, PermissionCodes.PROFILE_MANAGE_OWN) is False
