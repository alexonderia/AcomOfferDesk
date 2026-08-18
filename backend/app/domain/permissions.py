from __future__ import annotations

from functools import lru_cache

from app.core.config import settings


class PermissionCodes:
    USERS_READ = "users.read"
    USERS_CREATE = "users.create"
    USERS_REGISTRATION_INVITE = "users.registration.invite"
    USERS_REGISTRATION_APPROVE = "users.registration.approve"
    USERS_STATUS_UPDATE = "users.status.update"
    USERS_ROLE_UPDATE_ANY = "users.role.update_any"
    USERS_ROLE_UPDATE_ECONOMY = "users.role.update_economy"
    USERS_LOGIN_UPDATE = "users.login.update"
    USERS_PASSWORD_UPDATE = "users.password.update"
    USERS_MANAGER_UPDATE = "users.manager.update"
    UNITS_READ = "units.read"
    UNITS_CREATE = "units.create"
    UNITS_UPDATE = "units.update"
    UNITS_MEMBERS_MANAGE = "units.members.manage"
    PROFILE_MANAGE_OWN = "profile.manage_own"
    PROFILE_MANAGE_ANY = "profile.manage_any"
    COMPANY_CONTACTS_MANAGE_OWN = "company_contacts.manage_own"
    COMPANY_CONTACTS_MANAGE_ANY = "company_contacts.manage_any"
    REQUESTS_READ = "requests.read"
    REQUESTS_AMOUNTS_READ = "requests.amounts.read"
    REQUESTS_CREATE = "requests.create"
    REQUESTS_UPDATE = "requests.update"
    REQUESTS_PRICING_UPDATE = "requests.pricing.update"
    REQUESTS_DEADLINE_UPDATE = "requests.deadline.update"
    REQUESTS_STATUS_UPDATE = "requests.status.update"
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
    OFFERS_AMOUNT_UPDATE = "offers.amount.update"
    OFFERS_DETAILS_UPDATE = "offers.details.update"
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
    DASHBOARD_PROCESS_READ = "dashboard.process.read"
    DASHBOARD_SAVINGS_READ = "dashboard.savings.read"
    DASHBOARD_PLANS_READ = "dashboard.plans.read"
    NORMATIVE_FILES_READ = "normative_files.read"
    NORMATIVE_FILES_CREATE = "normative_files.create"
    NORMATIVE_FILES_MANAGE = "normative_files.manage"
    NORMATIVE_FILES_STATUS_UPDATE = "normative_files.status.update"
    FILES_DOWNLOAD = "files.download"
    UNAVAILABILITY_MANAGE_ALL = "unavailability.manage_all"
    UNAVAILABILITY_MANAGE_OWN = "unavailability.manage_own"
    UNAVAILABILITY_MANAGE_SUBORDINATE = "unavailability.manage_subordinate"
    CONTRACTORS_READ = "contractors.read"
    CONTRACTORS_PROFILE_READ = "contractors.profile.read"
    CONTRACTORS_PROFILE_STATUS_UPDATE = "contractors.profile.status.update"
    CONTRACTORS_MANUAL_CREATE = "contractors.manual.create"
    CONTRACTORS_MANUAL_MANAGE = "contractors.manual.manage"
    DEPARTMENT_REQUESTS_READ = "department.requests.read"
    DEPARTMENT_REQUESTS_UPDATE = "department.requests.update"
    DEPARTMENT_REQUESTS_STATUS_UPDATE = "department.requests.status_update"
    DEPARTMENT_REQUESTS_ASSIGN = "department.requests.assign"
    DEPARTMENT_OFFERS_UPDATE = "department.offers.update"
    DEPARTMENT_OFFERS_ACCEPT = "department.offers.accept"
    DEPARTMENT_OFFERS_REJECT = "department.offers.reject"
    DEPARTMENT_CHATS_READ = "department.chats.read"
    DEPARTMENT_CHATS_SEND_MESSAGE = "department.chats.send_message"
    DEPARTMENT_FILES_READ = "department.files.read"
    DEPARTMENT_FILES_UPLOAD = "department.files.upload"
    DEPARTMENT_FILES_DELETE = "department.files.delete"
    DEPARTMENT_DASHBOARD_READ = "department.dashboard.read"
    DEPARTMENT_PLANS_READ = "department.plans.read"
    DEPARTMENT_PLANS_MANAGE = "department.plans.manage"


@lru_cache(maxsize=1)
def get_known_permissions() -> frozenset[str]:
    return frozenset(
        value
        for name, value in vars(PermissionCodes).items()
        if name.isupper() and isinstance(value, str)
    )


@lru_cache(maxsize=1)
def get_role_permissions_map() -> dict[int, frozenset[str]]:
    all_permissions = get_known_permissions()

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
        PermissionCodes.REQUESTS_PRICING_UPDATE,
        PermissionCodes.REQUESTS_DEADLINE_UPDATE,
        PermissionCodes.REQUESTS_STATUS_UPDATE,
        PermissionCodes.REQUESTS_AMOUNTS_READ,
        PermissionCodes.REQUESTS_FILES_UPLOAD,
        PermissionCodes.REQUESTS_FILES_DELETE,
        PermissionCodes.REQUESTS_EMAIL_NOTIFICATIONS_SEND,
        PermissionCodes.REQUESTS_DELETED_ALERTS_MARK_VIEWED,
        PermissionCodes.OFFERS_UPDATE,
        PermissionCodes.OFFERS_AMOUNT_UPDATE,
        PermissionCodes.OFFERS_DETAILS_UPDATE,
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
        PermissionCodes.USERS_ROLE_UPDATE_ECONOMY,
        PermissionCodes.USERS_MANAGER_UPDATE,
        PermissionCodes.REQUESTS_OWNER_CHANGE,
        PermissionCodes.NORMATIVE_FILES_READ,
        PermissionCodes.DASHBOARD_PROCESS_READ,
        PermissionCodes.DASHBOARD_SAVINGS_READ,
        PermissionCodes.DASHBOARD_PLANS_READ,
        PermissionCodes.UNAVAILABILITY_MANAGE_SUBORDINATE,
    }
    subtree_units_manage_permissions = {
        PermissionCodes.UNITS_CREATE,
        PermissionCodes.UNITS_UPDATE,
        PermissionCodes.UNITS_MEMBERS_MANAGE,
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
        PermissionCodes.OFFERS_AMOUNT_UPDATE,
        PermissionCodes.OFFERS_DETAILS_UPDATE,
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
                PermissionCodes.USERS_REGISTRATION_INVITE,
                PermissionCodes.USERS_REGISTRATION_APPROVE,
                PermissionCodes.USERS_STATUS_UPDATE,
                PermissionCodes.USERS_ROLE_UPDATE_ANY,
                PermissionCodes.USERS_LOGIN_UPDATE,
                PermissionCodes.USERS_PASSWORD_UPDATE,
                PermissionCodes.UNITS_READ,
                PermissionCodes.UNITS_CREATE,
                PermissionCodes.UNITS_UPDATE,
                PermissionCodes.UNITS_MEMBERS_MANAGE,
                PermissionCodes.PROFILE_MANAGE_ANY,
                PermissionCodes.COMPANY_CONTACTS_MANAGE_ANY,
                PermissionCodes.CONTRACTORS_MANUAL_CREATE,
                PermissionCodes.CONTRACTORS_MANUAL_MANAGE,
            }
        ),
        settings.contractor_role_id: frozenset(common_permissions | contractor_permissions),
        settings.project_manager_role_id: frozenset(
            common_permissions
            | internal_request_read_permissions
            | {
                PermissionCodes.UNITS_READ,
                PermissionCodes.USERS_READ,
                PermissionCodes.CONTRACTORS_READ,
                PermissionCodes.CONTRACTORS_PROFILE_READ,
                PermissionCodes.USERS_STATUS_UPDATE,
                PermissionCodes.USERS_ROLE_UPDATE_ECONOMY,
                PermissionCodes.USERS_MANAGER_UPDATE,
                PermissionCodes.REQUESTS_OWNER_CHANGE,
                PermissionCodes.REQUESTS_AMOUNTS_READ,
                PermissionCodes.NORMATIVE_FILES_READ,
                PermissionCodes.DASHBOARD_PROCESS_READ,
                PermissionCodes.DASHBOARD_SAVINGS_READ,
                PermissionCodes.DASHBOARD_PLANS_READ,
                PermissionCodes.CONTRACTORS_MANUAL_CREATE,
                PermissionCodes.CONTRACTORS_MANUAL_MANAGE,
                PermissionCodes.UNAVAILABILITY_MANAGE_SUBORDINATE,
            }
            | subtree_units_manage_permissions
            | {PermissionCodes.UNAVAILABILITY_MANAGE_OWN}
        ),
        settings.lead_economist_role_id: frozenset(
            common_permissions
            | internal_request_read_permissions
            | internal_request_manage_permissions
            | management_permissions
            | subtree_units_manage_permissions
            | {
                PermissionCodes.UNITS_READ,
                PermissionCodes.CONTRACTORS_READ,
                PermissionCodes.CONTRACTORS_PROFILE_READ,
                PermissionCodes.NORMATIVE_FILES_MANAGE,
                PermissionCodes.NORMATIVE_FILES_CREATE,
                PermissionCodes.NORMATIVE_FILES_READ,
                PermissionCodes.NORMATIVE_FILES_STATUS_UPDATE,
                PermissionCodes.PROFILE_MANAGE_ANY,
                PermissionCodes.COMPANY_CONTACTS_MANAGE_ANY,
                PermissionCodes.USERS_ROLE_UPDATE_ECONOMY,
                PermissionCodes.UNAVAILABILITY_MANAGE_OWN,
                PermissionCodes.OFFERS_MANUAL_CREATE,
                PermissionCodes.CONTRACTORS_MANUAL_CREATE,
                PermissionCodes.CONTRACTORS_MANUAL_MANAGE,
            }
        ),
        settings.economist_role_id: frozenset(
            common_permissions
            | internal_request_read_permissions
            | internal_request_manage_permissions
            | {
                PermissionCodes.UNITS_READ,
                PermissionCodes.USERS_READ,
                PermissionCodes.CONTRACTORS_READ,
                PermissionCodes.CONTRACTORS_PROFILE_READ,
                PermissionCodes.USERS_STATUS_UPDATE,
                PermissionCodes.USERS_MANAGER_UPDATE,
                PermissionCodes.NORMATIVE_FILES_READ,
                PermissionCodes.DASHBOARD_PROCESS_READ,
                PermissionCodes.DASHBOARD_SAVINGS_READ,
                PermissionCodes.DASHBOARD_PLANS_READ,
                PermissionCodes.UNAVAILABILITY_MANAGE_OWN,
                PermissionCodes.UNAVAILABILITY_MANAGE_SUBORDINATE,
                PermissionCodes.OFFERS_MANUAL_CREATE,
                PermissionCodes.CONTRACTORS_MANUAL_CREATE,
                PermissionCodes.CONTRACTORS_MANUAL_MANAGE,
            }
            | subtree_units_manage_permissions
        ),
        settings.security_officer_role_id: frozenset(
            common_permissions
            | {
                PermissionCodes.UNITS_READ,
                PermissionCodes.CONTRACTORS_READ,
                PermissionCodes.CONTRACTORS_PROFILE_READ,
                PermissionCodes.CONTRACTORS_PROFILE_STATUS_UPDATE,
                PermissionCodes.USERS_REGISTRATION_INVITE,
                PermissionCodes.USERS_REGISTRATION_APPROVE,
            }
        ),
        settings.operator_role_id: frozenset(
            common_permissions
            | {
                PermissionCodes.PROFILE_MANAGE_OWN,
                PermissionCodes.UNITS_READ,
                PermissionCodes.REQUESTS_READ,
                PermissionCodes.REQUESTS_CREATE,
                PermissionCodes.REQUESTS_UPDATE,
                PermissionCodes.REQUESTS_PRICING_UPDATE,
                PermissionCodes.REQUESTS_DEADLINE_UPDATE,
                PermissionCodes.REQUESTS_STATUS_UPDATE,
                PermissionCodes.REQUESTS_AMOUNTS_READ,
                PermissionCodes.OFFERS_CONTRACTOR_INFO_READ,
                PermissionCodes.NORMATIVE_FILES_READ,
            }
        ),
    }


get_known_permissions.cache_clear()
get_role_permissions_map.cache_clear()
