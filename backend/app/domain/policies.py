from __future__ import annotations

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.authorization import has_permission, require_permission
from app.domain.exceptions import Forbidden
from app.domain.permissions import PermissionCodes


def _is_allowed(checker) -> bool:
    try:
        checker()
    except Forbidden:
        return False
    return True


class UserPolicy:
    @staticmethod
    def can_manage_normative_files(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.NORMATIVE_FILES_MANAGE)

    @staticmethod
    def ensure_can_manage_normative_files(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.NORMATIVE_FILES_MANAGE,
            message="Only lead economist can manage normative files",
        )

    @staticmethod
    def can_view_feedback(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.FEEDBACK_READ)

    @staticmethod
    def ensure_can_view_feedback(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.FEEDBACK_READ,
            message="Only superadmin can view feedback",
        )

    @staticmethod
    def can_create_feedback(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.FEEDBACK_CREATE)

    @staticmethod
    def ensure_can_create_feedback(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.FEEDBACK_CREATE,
            message="Insufficient permissions to create feedback",
        )

    @staticmethod
    def can_manage_economist_users(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.USERS_CREATE)

    @staticmethod
    def ensure_can_manage_economist_users(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.USERS_CREATE,
            message="Only admin, superadmin and lead economist can manage economist users",
        )

    @staticmethod
    def can_register_user(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.USERS_CREATE)

    @staticmethod
    def ensure_can_register_user(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.USERS_CREATE,
            message="Only admin, superadmin and lead economist can manage economist users",
        )

    @staticmethod
    def can_login(status: str) -> bool:
        return status == "active"

    @staticmethod
    def ensure_can_login(status: str) -> None:
        if not UserPolicy.can_login(status):
            raise Forbidden("User is not active")

    @staticmethod
    def can_list_users(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.USERS_READ)

    @staticmethod
    def ensure_can_list_users(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.USERS_READ,
            message="Insufficient permissions to view users",
        )

    @staticmethod
    def can_update_user_status(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.USERS_STATUS_UPDATE)

    @staticmethod
    def ensure_can_update_user_status(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.USERS_STATUS_UPDATE,
            message="Only admin, superadmin, project manager, lead economist and economist can update user status",
        )

    @staticmethod
    def can_update_user_role(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.USERS_ROLE_UPDATE)

    @staticmethod
    def ensure_can_update_user_role(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.USERS_ROLE_UPDATE,
            message="Only admin and superadmin can update user roles",
        )

    @staticmethod
    def can_update_user_manager(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.USERS_MANAGER_UPDATE)

    @staticmethod
    def ensure_can_update_user_manager(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.USERS_MANAGER_UPDATE,
            message="Only project manager, lead economist and economist can update user manager",
        )

    @staticmethod
    def can_manage_manual_contractors(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.CONTRACTORS_MANUAL_MANAGE)

    @staticmethod
    def ensure_can_manage_manual_contractors(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.CONTRACTORS_MANUAL_MANAGE,
            message="Only admin and superadmin can manage manually created contractors",
        )

    @staticmethod
    def can_manage_own_profile(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.PROFILE_MANAGE_OWN)

    @staticmethod
    def ensure_can_manage_own_profile(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.PROFILE_MANAGE_OWN,
            message="Insufficient permissions to access own profile",
        )

    @staticmethod
    def can_manage_own_unavailability(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.UNAVAILABILITY_MANAGE_OWN)

    @staticmethod
    def ensure_can_manage_own_unavailability(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.UNAVAILABILITY_MANAGE_OWN,
            message="Only project manager, lead economist and economist can manage unavailable period",
        )

    @staticmethod
    def can_manage_subordinate_unavailability(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.UNAVAILABILITY_MANAGE_SUBORDINATE)

    @staticmethod
    def ensure_can_manage_subordinate_unavailability(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.UNAVAILABILITY_MANAGE_SUBORDINATE,
            message="Only project manager, lead economist and economist can manage subordinate unavailable period",
        )

    @staticmethod
    def can_manage_own_company_contacts(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.COMPANY_CONTACTS_MANAGE_OWN)

    @staticmethod
    def ensure_can_manage_own_company_contacts(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.COMPANY_CONTACTS_MANAGE_OWN,
            message="Only contractor can manage company contacts",
        )

    @staticmethod
    def can_manage_requests(current_user: CurrentUser) -> bool:
        return _is_allowed(lambda: UserPolicy.ensure_can_manage_requests(current_user))

    @staticmethod
    def ensure_can_manage_requests(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.REQUESTS_UPDATE,
            message="Insufficient permissions for request management",
        )
        if current_user.role_id == settings.operator_role_id:
            raise Forbidden("Insufficient permissions for request management")

    @staticmethod
    def can_view_requests(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.REQUESTS_READ)

    @staticmethod
    def ensure_can_view_requests(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.REQUESTS_READ,
            message="Insufficient permissions for request view",
        )

    @staticmethod
    def can_view_request_amounts(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.REQUESTS_AMOUNTS_READ)

    @staticmethod
    def ensure_can_view_request_amounts(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.REQUESTS_AMOUNTS_READ,
            message="Insufficient permissions to view request amounts",
        )

    @staticmethod
    def can_create_request(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.REQUESTS_CREATE)

    @staticmethod
    def ensure_can_create_request(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.REQUESTS_CREATE,
            message="Insufficient permissions for request creation",
        )

    @staticmethod
    def can_view_open_requests(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.REQUESTS_OPEN_READ)

    @staticmethod
    def ensure_can_view_open_requests(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.REQUESTS_OPEN_READ,
            message="Insufficient permissions for open requests",
        )

    @staticmethod
    def can_create_offer(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.OFFERS_CREATE)

    @staticmethod
    def ensure_can_create_offer(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.OFFERS_CREATE,
            message="Only contractor can create offers",
        )

    @staticmethod
    def can_view_offered_requests(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.REQUESTS_OFFERED_READ)

    @staticmethod
    def ensure_can_view_offered_requests(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.REQUESTS_OFFERED_READ,
            message="Only contractor can view offered requests",
        )

    @staticmethod
    def can_view_responsibility_dashboard(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.DASHBOARD_RESPONSIBILITY_READ)

    @staticmethod
    def ensure_can_view_responsibility_dashboard(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.DASHBOARD_RESPONSIBILITY_READ,
            message="Only superadmin, lead economist and project manager can view responsibility dashboard",
        )

    @staticmethod
    def can_view_plan(current_user: CurrentUser) -> bool:
        return current_user.role_id in {
            settings.superadmin_role_id,
            settings.project_manager_role_id,
            settings.lead_economist_role_id,
            settings.economist_role_id,
        }

    @staticmethod
    def ensure_can_view_plan(current_user: CurrentUser) -> None:
        if not UserPolicy.can_view_plan(current_user):
            raise Forbidden("Only superadmin, project manager, lead economist and economist can view plan")


class RequestPolicy:
    @staticmethod
    def can_edit(current_user: CurrentUser, *, request_owner_user_id: str) -> bool:
        return _is_allowed(
            lambda: RequestPolicy.ensure_can_edit(
                current_user,
                request_owner_user_id=request_owner_user_id,
            )
        )

    @staticmethod
    def ensure_can_edit(current_user: CurrentUser, *, request_owner_user_id: str) -> None:
        require_permission(
            current_user,
            PermissionCodes.REQUESTS_UPDATE,
            message="Insufficient permissions to edit request",
        )
        if current_user.role_id == settings.operator_role_id:
            raise Forbidden("Insufficient permissions to edit request")
        if current_user.role_id == settings.economist_role_id and current_user.user_id != request_owner_user_id:
            raise Forbidden("Economist can edit only own requests")

    @staticmethod
    def can_edit_owned_unassigned(current_user: CurrentUser, *, request_owner_user_id: str) -> bool:
        return _is_allowed(
            lambda: RequestPolicy.ensure_can_edit_owned_unassigned(
                current_user,
                request_owner_user_id=request_owner_user_id,
            )
        )

    @staticmethod
    def ensure_can_edit_owned_unassigned(current_user: CurrentUser, *, request_owner_user_id: str) -> None:
        require_permission(
            current_user,
            PermissionCodes.REQUESTS_UPDATE,
            message="Insufficient permissions to edit request",
        )
        if current_user.role_id == settings.operator_role_id:
            if current_user.user_id != request_owner_user_id:
                raise Forbidden("Operator can edit only own unassigned requests")
            return

        RequestPolicy.ensure_can_edit(current_user, request_owner_user_id=request_owner_user_id)

    @staticmethod
    def can_change_owner(current_user: CurrentUser, *, request_owner_user_id: str) -> bool:
        return _is_allowed(
            lambda: RequestPolicy.ensure_can_change_owner(
                current_user,
                request_owner_user_id=request_owner_user_id,
            )
        )

    @staticmethod
    def ensure_can_change_owner(current_user: CurrentUser, *, request_owner_user_id: str) -> None:
        require_permission(
            current_user,
            PermissionCodes.REQUESTS_OWNER_CHANGE,
            message="Only lead economist, project manager and superadmin can change request owner",
        )
        require_permission(
            current_user,
            PermissionCodes.REQUESTS_READ,
            message="Insufficient permissions to change request owner",
        )

    @staticmethod
    def can_create_manual_offer(current_user: CurrentUser, *, request_owner_user_id: str) -> bool:
        return _is_allowed(
            lambda: RequestPolicy.ensure_can_create_manual_offer(
                current_user,
                request_owner_user_id=request_owner_user_id,
            )
        )

    @staticmethod
    def ensure_can_create_manual_offer(current_user: CurrentUser, *, request_owner_user_id: str) -> None:
        require_permission(
            current_user,
            PermissionCodes.OFFERS_MANUAL_CREATE,
            message="Insufficient permissions to create manual offers",
        )
        if current_user.role_id == settings.economist_role_id and current_user.user_id != request_owner_user_id:
            raise Forbidden("Economist can create manual offers only for own requests")


class OfferPolicy:
    @staticmethod
    def can_view_contractor_info(current_user: CurrentUser, *, contractor_user_id: str) -> bool:
        return _is_allowed(
            lambda: OfferPolicy.ensure_can_view_contractor_info(
                current_user,
                contractor_user_id=contractor_user_id,
            )
        )

    @staticmethod
    def ensure_can_view_contractor_info(current_user: CurrentUser, *, contractor_user_id: str) -> None:
        require_permission(
            current_user,
            PermissionCodes.OFFERS_CONTRACTOR_INFO_READ,
            message="Insufficient permissions to view contractor info",
        )
        if current_user.role_id == settings.contractor_role_id and current_user.user_id != contractor_user_id:
            raise Forbidden("Contractor can view only own profile")

    @staticmethod
    def can_access_contractor_offer(current_user: CurrentUser, *, offer_owner_user_id: str) -> bool:
        return _is_allowed(
            lambda: OfferPolicy.ensure_can_access_contractor_offer(
                current_user,
                offer_owner_user_id=offer_owner_user_id,
            )
        )

    @staticmethod
    def ensure_can_access_contractor_offer(current_user: CurrentUser, *, offer_owner_user_id: str) -> None:
        if current_user.role_id != settings.contractor_role_id:
            raise Forbidden("Only contractor can access own offers")
        if current_user.user_id != offer_owner_user_id:
            raise Forbidden("Contractor can access only own offers")

    @staticmethod
    def can_manage_offer(
        current_user: CurrentUser,
        *,
        offer_owner_user_id: str,
        request_owner_user_id: str,
    ) -> bool:
        return _is_allowed(
            lambda: OfferPolicy.ensure_can_manage_offer(
                current_user,
                offer_owner_user_id=offer_owner_user_id,
                request_owner_user_id=request_owner_user_id,
            )
        )

    @staticmethod
    def ensure_can_manage_offer(
        current_user: CurrentUser,
        *,
        offer_owner_user_id: str,
        request_owner_user_id: str,
    ) -> None:
        if current_user.role_id == settings.contractor_role_id:
            OfferPolicy.ensure_can_access_contractor_offer(current_user, offer_owner_user_id=offer_owner_user_id)
            return

        RequestPolicy.ensure_can_edit(current_user, request_owner_user_id=request_owner_user_id)

    @staticmethod
    def can_manage_manual_offer_files(
        current_user: CurrentUser,
        *,
        request_owner_user_id: str,
        offer_is_manual: bool,
    ) -> bool:
        return _is_allowed(
            lambda: OfferPolicy.ensure_can_manage_manual_offer_files(
                current_user,
                request_owner_user_id=request_owner_user_id,
                offer_is_manual=offer_is_manual,
            )
        )

    @staticmethod
    def ensure_can_manage_manual_offer_files(
        current_user: CurrentUser,
        *,
        request_owner_user_id: str,
        offer_is_manual: bool,
    ) -> None:
        require_permission(
            current_user,
            PermissionCodes.OFFERS_MANUAL_CREATE,
            message="Insufficient permissions to edit manual offer files",
        )
        RequestPolicy.ensure_can_edit(current_user, request_owner_user_id=request_owner_user_id)
        if not offer_is_manual:
            raise Forbidden("Manual offer files can be edited only for manually created offers")

    @staticmethod
    def can_access_offer_workspace(
        current_user: CurrentUser,
        *,
        offer_owner_user_id: str,
    ) -> bool:
        return _is_allowed(
            lambda: OfferPolicy.ensure_can_access_offer_workspace(
                current_user,
                offer_owner_user_id=offer_owner_user_id,
            )
        )

    @staticmethod
    def ensure_can_access_offer_workspace(
        current_user: CurrentUser,
        *,
        offer_owner_user_id: str,
    ) -> None:
        require_permission(
            current_user,
            PermissionCodes.OFFERS_WORKSPACE_READ,
            message="Insufficient permissions to view offer workspace",
        )
        if current_user.role_id == settings.contractor_role_id:
            OfferPolicy.ensure_can_access_contractor_offer(current_user, offer_owner_user_id=offer_owner_user_id)

    @staticmethod
    def can_view_chat(
        current_user: CurrentUser,
        *,
        offer_owner_user_id: str,
    ) -> bool:
        return _is_allowed(
            lambda: OfferPolicy.ensure_can_view_chat(
                current_user,
                offer_owner_user_id=offer_owner_user_id,
            )
        )

    @staticmethod
    def ensure_can_view_chat(
        current_user: CurrentUser,
        *,
        offer_owner_user_id: str,
    ) -> None:
        require_permission(
            current_user,
            PermissionCodes.CHAT_READ,
            message="Insufficient permissions to view chat",
        )
        if current_user.role_id == settings.contractor_role_id and current_user.user_id != offer_owner_user_id:
            raise Forbidden("Insufficient permissions to view chat")

    @staticmethod
    def can_send_chat_message(
        current_user: CurrentUser,
        *,
        offer_owner_user_id: str,
        request_owner_user_id: str,
    ) -> bool:
        return _is_allowed(
            lambda: OfferPolicy.ensure_can_send_chat_message(
                current_user,
                offer_owner_user_id=offer_owner_user_id,
                request_owner_user_id=request_owner_user_id,
            )
        )

    @staticmethod
    def ensure_can_send_chat_message(
        current_user: CurrentUser,
        *,
        offer_owner_user_id: str,
        request_owner_user_id: str,
    ) -> None:
        require_permission(
            current_user,
            PermissionCodes.CHAT_MESSAGE_SEND,
            message="Insufficient permissions to send chat message",
        )
        if current_user.role_id == settings.contractor_role_id and current_user.user_id == offer_owner_user_id:
            return

        if current_user.role_id in {
            settings.superadmin_role_id,
            settings.lead_economist_role_id,
        }:
            return

        if current_user.role_id == settings.economist_role_id and current_user.user_id == request_owner_user_id:
            return

        raise Forbidden("Insufficient permissions to send chat message")
