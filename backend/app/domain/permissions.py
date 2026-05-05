from __future__ import annotations

from functools import lru_cache

from app.core.config import settings


class PermissionCodes:
    USERS_READ = "users.read"
    USERS_CREATE = "users.create"
    USERS_STATUS_UPDATE = "users.status.update"
    USERS_ROLE_UPDATE = "users.role.update"
    USERS_MANAGER_UPDATE = "users.manager.update"
    PROFILE_MANAGE_OWN = "profile.manage_own"
    COMPANY_CONTACTS_MANAGE_OWN = "company_contacts.manage_own"
    REQUESTS_READ = "requests.read"
    REQUESTS_AMOUNTS_READ = "requests.amounts.read"
    REQUESTS_CREATE = "requests.create"
    REQUESTS_UPDATE = "requests.update"
    REQUESTS_OWNER_CHANGE = "requests.owner.change"
    REQUESTS_FILES_UPLOAD = "requests.files.upload"
    REQUESTS_FILES_DELETE = "requests.files.delete"
    REQUESTS_OPEN_READ = "requests.open.read"
    REQUESTS_OFFERED_READ = "requests.offered.read"
    REQUESTS_CONTRACTOR_VIEW_READ = "requests.contractor_view.read"
    REQUESTS_EMAIL_NOTIFICATIONS_SEND = "requests.email_notifications.send"
    REQUESTS_DELETED_ALERTS_MARK_VIEWED = "requests.deleted_alerts.mark_viewed"
    OFFERS_CREATE = "offers.create"
    OFFERS_MANUAL_CREATE = "offers.manual.create"
    OFFERS_WORKSPACE_READ = "offers.workspace.read"
    OFFERS_UPDATE = "offers.update"
    OFFERS_STATUS_UPDATE = "offers.status.update"
    OFFERS_FILES_UPLOAD = "offers.files.upload"
    OFFERS_FILES_DELETE = "offers.files.delete"
    OFFERS_CONTRACTOR_INFO_READ = "offers.contractor_info.read"
    CHAT_READ = "chat.read"
    CHAT_MESSAGE_SEND = "chat.message.send"
    CHAT_MESSAGE_ATTACH = "chat.message.attach"
    CHAT_RECEIPTS_MARK_RECEIVED = "chat.receipts.mark_received"
    CHAT_RECEIPTS_MARK_READ = "chat.receipts.mark_read"
    FEEDBACK_READ = "feedback.read"
    FEEDBACK_CREATE = "feedback.create"
    DASHBOARD_RESPONSIBILITY_READ = "dashboard.responsibility.read"
    NORMATIVE_FILES_MANAGE = "normative_files.manage"
    FILES_DOWNLOAD = "files.download"
    UNAVAILABILITY_MANAGE_OWN = "unavailability.manage_own"
    UNAVAILABILITY_MANAGE_SUBORDINATE = "unavailability.manage_subordinate"
    CONTRACTORS_MANUAL_MANAGE = "contractors.manual.manage"


@lru_cache(maxsize=1)
def get_role_permissions_map() -> dict[int, frozenset[str]]:
    all_permissions = frozenset(
        value
        for name, value in vars(PermissionCodes).items()
        if name.isupper() and isinstance(value, str)
    )

    internal_request_read_permissions = {
        PermissionCodes.REQUESTS_READ,
        PermissionCodes.OFFERS_WORKSPACE_READ,
        PermissionCodes.OFFERS_CONTRACTOR_INFO_READ,
        PermissionCodes.CHAT_READ,
        PermissionCodes.FILES_DOWNLOAD,
    }
    internal_request_manage_permissions = {
        PermissionCodes.REQUESTS_CREATE,
        PermissionCodes.REQUESTS_UPDATE,
        PermissionCodes.REQUESTS_AMOUNTS_READ,
        PermissionCodes.REQUESTS_FILES_UPLOAD,
        PermissionCodes.REQUESTS_FILES_DELETE,
        PermissionCodes.REQUESTS_EMAIL_NOTIFICATIONS_SEND,
        PermissionCodes.REQUESTS_DELETED_ALERTS_MARK_VIEWED,
        PermissionCodes.OFFERS_UPDATE,
        PermissionCodes.OFFERS_STATUS_UPDATE,
        PermissionCodes.CHAT_MESSAGE_SEND,
        PermissionCodes.CHAT_MESSAGE_ATTACH,
        PermissionCodes.CHAT_RECEIPTS_MARK_RECEIVED,
        PermissionCodes.CHAT_RECEIPTS_MARK_READ,
    }
    management_permissions = {
        PermissionCodes.USERS_READ,
        PermissionCodes.USERS_CREATE,
        PermissionCodes.USERS_STATUS_UPDATE,
        PermissionCodes.USERS_MANAGER_UPDATE,
        PermissionCodes.REQUESTS_OWNER_CHANGE,
        PermissionCodes.DASHBOARD_RESPONSIBILITY_READ,
        PermissionCodes.UNAVAILABILITY_MANAGE_SUBORDINATE,
    }
    contractor_permissions = {
        PermissionCodes.PROFILE_MANAGE_OWN,
        PermissionCodes.COMPANY_CONTACTS_MANAGE_OWN,
        PermissionCodes.REQUESTS_OPEN_READ,
        PermissionCodes.REQUESTS_OFFERED_READ,
        PermissionCodes.REQUESTS_CONTRACTOR_VIEW_READ,
        PermissionCodes.OFFERS_CREATE,
        PermissionCodes.OFFERS_WORKSPACE_READ,
        PermissionCodes.OFFERS_UPDATE,
        PermissionCodes.OFFERS_STATUS_UPDATE,
        PermissionCodes.OFFERS_FILES_UPLOAD,
        PermissionCodes.OFFERS_FILES_DELETE,
        PermissionCodes.OFFERS_CONTRACTOR_INFO_READ,
        PermissionCodes.CHAT_READ,
        PermissionCodes.CHAT_MESSAGE_SEND,
        PermissionCodes.CHAT_MESSAGE_ATTACH,
        PermissionCodes.CHAT_RECEIPTS_MARK_RECEIVED,
        PermissionCodes.CHAT_RECEIPTS_MARK_READ,
        PermissionCodes.FILES_DOWNLOAD,
    }
    common_permissions = {
        PermissionCodes.PROFILE_MANAGE_OWN,
        PermissionCodes.FEEDBACK_CREATE,
    }

    return {
        settings.superadmin_role_id: all_permissions,
        settings.admin_role_id: frozenset(
            common_permissions
            | {
                PermissionCodes.USERS_READ,
                PermissionCodes.USERS_CREATE,
                PermissionCodes.USERS_STATUS_UPDATE,
                PermissionCodes.USERS_ROLE_UPDATE,
                PermissionCodes.CONTRACTORS_MANUAL_MANAGE,
            }
        ),
        settings.contractor_role_id: frozenset(common_permissions | contractor_permissions),
        settings.project_manager_role_id: frozenset(
            common_permissions
            | internal_request_read_permissions
            | {
                PermissionCodes.USERS_READ,
                PermissionCodes.USERS_STATUS_UPDATE,
                PermissionCodes.USERS_MANAGER_UPDATE,
                PermissionCodes.REQUESTS_OWNER_CHANGE,
                PermissionCodes.REQUESTS_AMOUNTS_READ,
                PermissionCodes.DASHBOARD_RESPONSIBILITY_READ,
                PermissionCodes.UNAVAILABILITY_MANAGE_SUBORDINATE,
            }
            | {PermissionCodes.UNAVAILABILITY_MANAGE_OWN}
        ),
        settings.lead_economist_role_id: frozenset(
            common_permissions
            | internal_request_read_permissions
            | internal_request_manage_permissions
            | management_permissions
            | {
                PermissionCodes.NORMATIVE_FILES_MANAGE,
                PermissionCodes.UNAVAILABILITY_MANAGE_OWN,
                PermissionCodes.OFFERS_MANUAL_CREATE,
            }
        ),
        settings.economist_role_id: frozenset(
            common_permissions
            | internal_request_read_permissions
            | internal_request_manage_permissions
            | {
                PermissionCodes.USERS_READ,
                PermissionCodes.USERS_STATUS_UPDATE,
                PermissionCodes.USERS_MANAGER_UPDATE,
                PermissionCodes.UNAVAILABILITY_MANAGE_OWN,
                PermissionCodes.UNAVAILABILITY_MANAGE_SUBORDINATE,
                PermissionCodes.OFFERS_MANUAL_CREATE,
            }
        ),
        settings.operator_role_id: frozenset(
            common_permissions
            | {
                PermissionCodes.PROFILE_MANAGE_OWN,
                PermissionCodes.REQUESTS_READ,
                PermissionCodes.REQUESTS_CREATE,
                PermissionCodes.REQUESTS_UPDATE,
                PermissionCodes.REQUESTS_AMOUNTS_READ,
            }
        ),
    }


def get_permissions_for_role(role_id: int) -> frozenset[str]:
    return get_role_permissions_map().get(role_id, frozenset())
