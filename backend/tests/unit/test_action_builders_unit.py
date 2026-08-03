"""Unit tests for backend action builders.

Focus:
- action flags are derived from permissions + business conditions;
- contractor users do not receive internal-only actions;
- subordinate-management actions are exposed only when policy allows.
"""

from app.core.config import settings
from app.api.action_flags import ChatActionBuilder, ContractorActionBuilder, OfferActionBuilder, RequestActionBuilder, UserActionBuilder
from app.domain.permissions import PermissionCodes


def test_request_action_builder_reflects_permissions_and_status(make_current_user):
    current_user = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions={
            PermissionCodes.REQUESTS_READ,
            PermissionCodes.REQUESTS_AMOUNTS_READ,
            PermissionCodes.REQUESTS_CONTRACTOR_VIEW_READ,
            PermissionCodes.REQUESTS_UPDATE,
            PermissionCodes.REQUESTS_PRICING_UPDATE,
            PermissionCodes.REQUESTS_DEADLINE_UPDATE,
            PermissionCodes.REQUESTS_STATUS_UPDATE,
            PermissionCodes.REQUESTS_FILES_UPLOAD,
            PermissionCodes.REQUESTS_FILES_DELETE,
            PermissionCodes.REQUESTS_EMAIL_NOTIFICATIONS_SEND,
            PermissionCodes.REQUESTS_DELETED_ALERTS_MARK_VIEWED,
        },
    )

    actions = RequestActionBuilder.build(
        current_user,
        owner_user_id="owner-1",
        status="open",
        can_manage_in_scope=True,
        can_update_status_in_scope=True,
        can_create_offer=False,
        deleted_alert_count=2,
    )

    assert actions.can_view_details is True
    assert actions.can_view_amounts is True
    assert actions.can_open_contractor_view is True
    assert actions.can_update_status is True
    assert actions.can_upload_files is True
    assert actions.can_delete_files is True
    assert actions.can_send_email_notifications is True
    assert actions.can_mark_deleted_alert_viewed is True


def test_request_action_builder_hides_edit_actions_outside_management_scope(make_current_user):
    current_user = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions={
            PermissionCodes.REQUESTS_READ,
            PermissionCodes.REQUESTS_UPDATE,
            PermissionCodes.REQUESTS_STATUS_UPDATE,
            PermissionCodes.REQUESTS_FILES_UPLOAD,
        },
    )

    actions = RequestActionBuilder.build(
        current_user,
        owner_user_id="peer-owner",
        status="open",
        can_manage_in_scope=False,
        can_update_status_in_scope=False,
    )

    assert actions.can_edit is False
    assert actions.can_update_status is False
    assert actions.can_upload_files is False


def test_offer_action_builder_contractor_does_not_get_internal_accept_reject(make_current_user):
    contractor = make_current_user(
        user_id="c-1",
        role_id=settings.contractor_role_id,
        permissions={
            PermissionCodes.OFFERS_WORKSPACE_READ,
            PermissionCodes.OFFERS_CONTRACTOR_INFO_READ,
            PermissionCodes.OFFERS_UPDATE,
            PermissionCodes.OFFERS_AMOUNT_UPDATE,
            PermissionCodes.OFFERS_STATUS_UPDATE,
            PermissionCodes.OFFERS_FILES_UPLOAD,
            PermissionCodes.OFFERS_FILES_DELETE,
        },
    )

    actions = OfferActionBuilder.build(
        contractor,
        offer_owner_user_id="c-1",
        request_owner_user_id="owner-1",
        contractor_user_id="c-1",
        offer_status="submitted",
        can_manage_in_scope=True,
    )

    assert actions.can_open_workspace is True
    assert actions.can_edit_amount is True
    assert actions.can_upload_files is True
    assert actions.can_delete_files is True
    assert actions.can_accept is False
    assert actions.can_reject is False


def test_chat_action_builder_reflects_chat_permissions(make_current_user):
    user = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions={
            PermissionCodes.CHAT_READ,
            PermissionCodes.CHAT_MESSAGE_SEND,
            PermissionCodes.CHAT_MESSAGE_ATTACH,
            PermissionCodes.CHAT_RECEIPTS_MARK_RECEIVED,
            PermissionCodes.CHAT_RECEIPTS_MARK_READ,
        },
    )

    actions = ChatActionBuilder.build(
        user,
        offer_owner_user_id="contractor-1",
        request_owner_user_id=user.user_id,
        can_acknowledge_messages=True,
        can_view_in_scope=True,
        can_send_in_scope=True,
    )

    assert actions.can_view_messages is True
    assert actions.can_send_message is True
    assert actions.can_attach_files is True
    assert actions.can_mark_messages_received is True
    assert actions.can_mark_messages_read is True


def test_chat_action_builder_department_view_scope_does_not_grant_send_or_attachments(make_current_user):
    user = make_current_user(
        role_id=settings.economist_role_id,
        permissions={PermissionCodes.DEPARTMENT_CHATS_READ},
    )

    actions = ChatActionBuilder.build(
        user,
        offer_owner_user_id="contractor-1",
        request_owner_user_id="owner-1",
        can_acknowledge_messages=False,
        can_view_in_scope=False,
        can_send_in_scope=False,
        has_department_chat_view_scope=True,
        has_department_chat_send_scope=False,
    )

    assert actions.can_view_messages is True
    assert actions.can_send_message is False
    assert actions.can_attach_files is False


def test_offer_action_builder_manual_offer_permission_does_not_grant_file_actions(make_current_user):
    user = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions={
            PermissionCodes.OFFERS_WORKSPACE_READ,
            PermissionCodes.OFFERS_CONTRACTOR_INFO_READ,
            PermissionCodes.OFFERS_MANUAL_CREATE,
            PermissionCodes.REQUESTS_UPDATE,
        },
    )

    actions = OfferActionBuilder.build(
        user,
        offer_owner_user_id="contractor-1",
        request_owner_user_id="owner-1",
        contractor_user_id="contractor-1",
        offer_status="submitted",
        can_manage_in_scope=True,
        offer_is_manual=True,
    )

    assert actions.can_upload_files is False
    assert actions.can_delete_files is False


def test_offer_action_builder_department_offer_update_scope_grants_edit_actions(make_current_user):
    user = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions={
            PermissionCodes.OFFERS_WORKSPACE_READ,
            PermissionCodes.OFFERS_CONTRACTOR_INFO_READ,
        },
    )

    actions = OfferActionBuilder.build(
        user,
        offer_owner_user_id="contractor-1",
        request_owner_user_id="owner-1",
        contractor_user_id="contractor-1",
        offer_status="submitted",
        can_manage_in_scope=False,
        has_department_offer_update_scope=True,
    )

    assert actions.can_edit_amount is True
    assert actions.can_upload_files is True
    assert actions.can_delete_files is True
    assert actions.can_accept is False
    assert actions.can_reject is False


def test_offer_action_builder_requires_offers_update_for_hierarchy_edit_actions(make_current_user):
    user = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions={
            PermissionCodes.OFFERS_WORKSPACE_READ,
            PermissionCodes.OFFERS_CONTRACTOR_INFO_READ,
            PermissionCodes.OFFERS_AMOUNT_UPDATE,
            PermissionCodes.OFFERS_DETAILS_UPDATE,
            PermissionCodes.REQUESTS_UPDATE,
        },
    )

    actions = OfferActionBuilder.build(
        user,
        offer_owner_user_id="contractor-1",
        request_owner_user_id="owner-1",
        contractor_user_id="contractor-1",
        offer_status="submitted",
        can_manage_in_scope=True,
    )

    assert actions.can_edit_amount is False
    assert actions.can_upload_files is False
    assert actions.can_delete_files is False


def test_offer_action_builder_internal_file_actions_require_offers_details_update(make_current_user):
    user = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions={
            PermissionCodes.OFFERS_WORKSPACE_READ,
            PermissionCodes.OFFERS_CONTRACTOR_INFO_READ,
            PermissionCodes.OFFERS_UPDATE,
            PermissionCodes.OFFERS_DETAILS_UPDATE,
            PermissionCodes.REQUESTS_UPDATE,
        },
    )

    actions = OfferActionBuilder.build(
        user,
        offer_owner_user_id="contractor-1",
        request_owner_user_id="owner-1",
        contractor_user_id="contractor-1",
        offer_status="submitted",
        can_manage_in_scope=True,
        has_department_offer_update_scope=False,
    )

    assert actions.can_upload_files is True
    assert actions.can_delete_files is True


def test_offer_action_builder_hides_edit_actions_outside_hierarchy_scope_without_department_delegation(make_current_user):
    user = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions={
            PermissionCodes.OFFERS_WORKSPACE_READ,
            PermissionCodes.OFFERS_CONTRACTOR_INFO_READ,
            PermissionCodes.OFFERS_UPDATE,
            PermissionCodes.OFFERS_AMOUNT_UPDATE,
            PermissionCodes.OFFERS_FILES_UPLOAD,
            PermissionCodes.OFFERS_FILES_DELETE,
            PermissionCodes.REQUESTS_UPDATE,
        },
    )

    actions = OfferActionBuilder.build(
        user,
        offer_owner_user_id="contractor-1",
        request_owner_user_id="peer-lead-owner",
        contractor_user_id="contractor-1",
        offer_status="submitted",
        can_manage_in_scope=False,
        has_department_offer_update_scope=False,
    )

    assert actions.can_edit_amount is False
    assert actions.can_upload_files is False
    assert actions.can_delete_files is False


def test_user_action_builder_contractor_not_given_internal_controls(make_current_user):
    contractor = make_current_user(
        user_id="c-1",
        role_id=settings.contractor_role_id,
        permissions={PermissionCodes.PROFILE_MANAGE_OWN},
    )

    actions = UserActionBuilder.build_list_item(
        contractor,
        target_user_id="lead-1",
        target_role_id=settings.lead_economist_role_id,
        target_tg_user_id=None,
    )

    assert actions.can_update_status is False
    assert actions.can_update_role is False
    assert actions.can_update_manager is False
    assert actions.can_manage_manual_contractor is False


def test_user_action_builder_hierarchy_peer_cannot_manage_status_or_role(make_current_user):
    lead_economist = make_current_user(
        user_id="le-1",
        role_id=settings.lead_economist_role_id,
        permissions={
            PermissionCodes.USERS_STATUS_UPDATE,
            PermissionCodes.USERS_ROLE_UPDATE_ECONOMY,
            PermissionCodes.USERS_MANAGER_UPDATE,
        },
    )

    actions = UserActionBuilder.build_list_item(
        lead_economist,
        target_user_id="eco-peer-1",
        target_role_id=settings.economist_role_id,
        is_hierarchy_subordinate=False,
    )

    assert actions.can_update_status is False
    assert actions.can_update_role is False
    assert actions.can_update_manager is False


def test_user_action_builder_profile_manage_any_does_not_allow_status_for_non_subordinate_economist(
    make_current_user,
):
    lead_economist = make_current_user(
        user_id="le-1",
        role_id=settings.lead_economist_role_id,
        permissions={
            PermissionCodes.USERS_STATUS_UPDATE,
            PermissionCodes.PROFILE_MANAGE_ANY,
        },
    )

    actions = UserActionBuilder.build_list_item(
        lead_economist,
        target_user_id="eco-peer-1",
        target_role_id=settings.economist_role_id,
        is_hierarchy_subordinate=False,
    )

    assert actions.can_update_status is False
    assert actions.can_view_profile is True


def test_user_action_builder_profile_manage_any_does_not_allow_lead_status_for_lead_economist(make_current_user):
    lead_economist = make_current_user(
        user_id="le-1",
        role_id=settings.lead_economist_role_id,
        permissions={
            PermissionCodes.USERS_STATUS_UPDATE,
            PermissionCodes.PROFILE_MANAGE_ANY,
        },
    )

    actions = UserActionBuilder.build_list_item(
        lead_economist,
        target_user_id="le-peer-1",
        target_role_id=settings.lead_economist_role_id,
        is_hierarchy_subordinate=True,
    )

    assert actions.can_update_status is False
    assert actions.can_view_profile is True


def test_user_action_builder_hierarchy_subordinate_can_manage_status_and_role(make_current_user):
    lead_economist = make_current_user(
        user_id="le-1",
        role_id=settings.lead_economist_role_id,
        permissions={
            PermissionCodes.USERS_STATUS_UPDATE,
            PermissionCodes.USERS_ROLE_UPDATE_ECONOMY,
            PermissionCodes.USERS_MANAGER_UPDATE,
        },
    )

    actions = UserActionBuilder.build_list_item(
        lead_economist,
        target_user_id="eco-sub-1",
        target_role_id=settings.economist_role_id,
        is_hierarchy_subordinate=True,
    )

    assert actions.can_update_status is True
    assert actions.can_update_role is True
    assert actions.can_update_manager is False


def test_user_action_builder_admin_can_update_contractor_status_with_users_status_update(make_current_user):
    admin = make_current_user(
        user_id="admin-1",
        role_id=settings.admin_role_id,
        permissions={PermissionCodes.USERS_STATUS_UPDATE},
    )

    actions = UserActionBuilder.build_list_item(
        admin,
        target_user_id="contractor-1",
        target_role_id=settings.contractor_role_id,
    )

    assert actions.can_update_status is True


def test_user_action_builder_economist_cannot_update_contractor_status_with_users_status_update(make_current_user):
    economist = make_current_user(
        user_id="eco-1",
        role_id=settings.economist_role_id,
        permissions={PermissionCodes.USERS_STATUS_UPDATE},
    )

    actions = UserActionBuilder.build_list_item(
        economist,
        target_user_id="contractor-1",
        target_role_id=settings.contractor_role_id,
    )

    assert actions.can_update_status is False


def test_user_action_builder_delegated_lead_can_update_contractor_status(make_current_user):
    lead = make_current_user(
        user_id="lead-1",
        role_id=settings.lead_economist_role_id,
        permissions={
            PermissionCodes.CONTRACTORS_READ,
            PermissionCodes.CONTRACTORS_PROFILE_READ,
            PermissionCodes.CONTRACTORS_PROFILE_STATUS_UPDATE,
        },
        keycloak_roles={"delegation.contractors.profile.status.update"},
    )

    actions = UserActionBuilder.build_list_item(
        lead,
        target_user_id="contractor-1",
        target_role_id=settings.contractor_role_id,
    )

    assert actions.can_update_status is True


def test_contractor_action_builder_allows_status_with_delegation_role_only(make_current_user):
    lead = make_current_user(
        user_id="lead-1",
        role_id=settings.lead_economist_role_id,
        permissions=set(),
        keycloak_roles={"delegation.contractors.profile.status.update"},
    )

    actions = ContractorActionBuilder.build_contractor_actions(lead, is_manual=False)

    assert actions.can_update_status is True


def test_contractor_action_builder_allows_manual_edit_only_for_manual_rows(make_current_user):
    current_user = make_current_user(
        user_id="admin-1",
        role_id=settings.admin_role_id,
        permissions={
            PermissionCodes.CONTRACTORS_READ,
            PermissionCodes.CONTRACTORS_PROFILE_READ,
            PermissionCodes.CONTRACTORS_PROFILE_STATUS_UPDATE,
            PermissionCodes.CONTRACTORS_MANUAL_MANAGE,
        },
    )

    manual_actions = ContractorActionBuilder.build_contractor_actions(current_user, is_manual=True)
    telegram_actions = ContractorActionBuilder.build_contractor_actions(current_user, is_manual=False)

    assert manual_actions.can_view_profile is True
    assert manual_actions.can_update_status is True
    assert manual_actions.can_manage_manual_contractor is True
    assert telegram_actions.can_manage_manual_contractor is False


def test_contractor_action_builder_allows_status_with_delegation_permission(make_current_user):
    current_user = make_current_user(
        user_id="security-1",
        role_id=settings.security_officer_role_id,
        permissions={
            PermissionCodes.CONTRACTORS_READ,
            PermissionCodes.CONTRACTORS_PROFILE_READ,
            PermissionCodes.CONTRACTORS_PROFILE_STATUS_UPDATE,
            PermissionCodes.CONTRACTORS_MANUAL_MANAGE,
        },
    )

    actions = ContractorActionBuilder.build_contractor_actions(current_user, is_manual=True)

    assert actions.can_view_profile is True
    assert actions.can_manage_manual_contractor is True
    assert actions.can_update_status is True


def test_request_action_builder_project_manager_never_gets_edit_even_in_scope(make_current_user):
    current_user = make_current_user(
        user_id="pm-1",
        role_id=settings.project_manager_role_id,
        permissions={
            PermissionCodes.REQUESTS_READ,
            PermissionCodes.REQUESTS_OWNER_CHANGE,
        },
    )

    actions = RequestActionBuilder.build(
        current_user,
        owner_user_id="eco-1",
        status="open",
        can_manage_in_scope=True,
    )

    assert actions.can_edit is False
    assert actions.can_change_owner is True


def test_user_action_builder_internal_manager_can_manage_subordinate(make_current_user):
    manager = make_current_user(
        user_id="pm-1",
        role_id=settings.project_manager_role_id,
        permissions={
            PermissionCodes.USERS_STATUS_UPDATE,
            PermissionCodes.USERS_ROLE_UPDATE_ECONOMY,
            PermissionCodes.USERS_MANAGER_UPDATE,
            PermissionCodes.UNAVAILABILITY_MANAGE_SUBORDINATE,
        },
    )

    actions = UserActionBuilder.build_subordinate_profile(
        manager,
        target_role_id=settings.economist_role_id,
    )

    assert actions.can_view_profile is True
    assert actions.can_update_status is True
    assert actions.can_update_manager is False
    assert actions.can_manage_subordinate_unavailability is True
