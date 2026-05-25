"""Unit tests for backend action builders.

Focus:
- action flags are derived from permissions + business conditions;
- contractor users do not receive internal-only actions;
- subordinate-management actions are exposed only when policy allows.
"""

from app.core.config import settings
from app.api.action_flags import ChatActionBuilder, OfferActionBuilder, RequestActionBuilder, UserActionBuilder
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
        can_create_offer=False,
        deleted_alert_count=2,
    )

    assert actions.can_view_details is True
    assert actions.can_view_amounts is True
    assert actions.can_open_contractor_view is True
    assert actions.can_upload_files is True
    assert actions.can_delete_files is True
    assert actions.can_send_email_notifications is True
    assert actions.can_mark_deleted_alert_viewed is True


def test_offer_action_builder_contractor_does_not_get_internal_accept_reject(make_current_user):
    contractor = make_current_user(
        user_id="c-1",
        role_id=settings.contractor_role_id,
        permissions={
            PermissionCodes.OFFERS_WORKSPACE_READ,
            PermissionCodes.OFFERS_CONTRACTOR_INFO_READ,
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
    )

    assert actions.can_view_messages is True
    assert actions.can_send_message is True
    assert actions.can_attach_files is True
    assert actions.can_mark_messages_received is True
    assert actions.can_mark_messages_read is True


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
        offer_is_manual=True,
    )

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
    assert actions.can_update_manager is True
    assert actions.can_manage_subordinate_unavailability is True
