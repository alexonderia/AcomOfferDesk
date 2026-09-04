"""Unit tests for critical policy branches.

Focus:
- owner vs non-owner request access;
- contractor vs internal offer access constraints;
- permission prerequisites and role-specific denials.
"""

from app.core.config import settings
from app.domain.permissions import PermissionCodes
from app.domain.policies import OfferPolicy, RequestPolicy, UserPolicy


def test_request_policy_edit_owner_vs_not_owner_for_economist(make_current_user):
    economist = make_current_user(
        user_id="econ-1",
        role_id=settings.economist_role_id,
        permissions={
            PermissionCodes.REQUESTS_UPDATE,
            PermissionCodes.REQUESTS_PRICING_UPDATE,
            PermissionCodes.REQUESTS_DEADLINE_UPDATE,
            PermissionCodes.REQUESTS_STATUS_UPDATE,
        },
    )

    assert RequestPolicy.can_edit(economist, request_owner_user_id="econ-1") is True
    assert RequestPolicy.can_edit(economist, request_owner_user_id="econ-2") is False


def test_request_policy_requires_permissions(make_current_user):
    no_permissions = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions={PermissionCodes.REQUESTS_READ},
    )

    assert RequestPolicy.can_edit(no_permissions, request_owner_user_id="other") is False


def test_offer_policy_contractor_can_manage_only_own_offer(make_current_user):
    contractor = make_current_user(
        user_id="contractor-1",
        role_id=settings.contractor_role_id,
        permissions={PermissionCodes.OFFERS_WORKSPACE_READ},
    )

    assert OfferPolicy.can_access_contractor_offer(contractor, offer_owner_user_id="contractor-1") is True
    assert OfferPolicy.can_access_contractor_offer(contractor, offer_owner_user_id="contractor-2") is False


def test_offer_policy_manual_offer_files_rejected_for_non_manual_offer(make_current_user):
    lead = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions={PermissionCodes.OFFERS_MANUAL_CREATE, PermissionCodes.REQUESTS_UPDATE},
    )

    assert (
        OfferPolicy.can_manage_manual_offer_files(
            lead,
            request_owner_user_id="req-owner",
            offer_is_manual=False,
        )
        is False
    )


def test_user_policy_manage_requests_forbidden_without_permissions(make_current_user):
    user = make_current_user(role_id=settings.project_manager_role_id, permissions={PermissionCodes.USERS_READ})

    assert UserPolicy.can_manage_requests(user) is False


def test_user_policy_manage_requests_forbidden_for_operator_even_with_permissions(make_current_user):
    operator = make_current_user(
        role_id=settings.operator_role_id,
        permissions={
            PermissionCodes.REQUESTS_UPDATE,
            PermissionCodes.REQUESTS_PRICING_UPDATE,
            PermissionCodes.REQUESTS_DEADLINE_UPDATE,
            PermissionCodes.REQUESTS_STATUS_UPDATE,
        },
    )

    assert UserPolicy.can_manage_requests(operator) is False


def test_user_policy_manage_requests_allowed_for_lead_with_permissions(make_current_user):
    lead = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions={
            PermissionCodes.REQUESTS_UPDATE,
            PermissionCodes.REQUESTS_PRICING_UPDATE,
            PermissionCodes.REQUESTS_DEADLINE_UPDATE,
            PermissionCodes.REQUESTS_STATUS_UPDATE,
        },
    )

    assert UserPolicy.can_manage_requests(lead) is True


def test_user_policy_contractor_status_denied_without_iam_permission(make_current_user):
    lead = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions=set(),
    )

    assert UserPolicy.can_update_contractor_profile_status(lead) is False


def test_user_policy_contractor_status_via_explicit_iam_permission(make_current_user):
    pm = make_current_user(
        role_id=settings.project_manager_role_id,
        permissions={
            PermissionCodes.CONTRACTORS_READ,
            PermissionCodes.CONTRACTORS_PROFILE_READ,
            PermissionCodes.CONTRACTORS_PROFILE_STATUS_UPDATE,
        },
    )

    assert UserPolicy.can_update_contractor_profile_status(pm) is True


def test_user_policy_contractor_status_via_admin_users_status_update(make_current_user):
    admin = make_current_user(
        role_id=settings.admin_role_id,
        permissions={PermissionCodes.USERS_STATUS_UPDATE},
    )

    assert UserPolicy.can_update_contractor_profile_status(admin) is True


def test_user_policy_contractor_status_denied_for_economist_users_status_update(make_current_user):
    economist = make_current_user(
        role_id=settings.economist_role_id,
        permissions={PermissionCodes.USERS_STATUS_UPDATE},
    )

    assert UserPolicy.can_update_contractor_profile_status(economist) is False
