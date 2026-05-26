from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.authorization import has_permission
from app.domain.exceptions import NotFound
from app.domain.permissions import PermissionCodes
from app.domain.policies import OfferPolicy, RequestPolicy, UserPolicy
from app.repositories.chats import ChatRepository
from app.repositories.offers import OfferRepository
from app.repositories.requests import RequestRepository
from app.repositories.users import UserRepository
from app.services.staff_access_scope import StaffAccessScopeService
from app.schemas.actions import (
    ChatActionsSchema,
    OfferActionsSchema,
    RequestActionsSchema,
    UserActionsSchema,
)

ECONOMY_ROLE_IDS = {
    settings.project_manager_role_id,
    settings.lead_economist_role_id,
    settings.economist_role_id,
    settings.operator_role_id,
}

SUBORDINATE_PROFILE_ROLE_IDS = {
    settings.lead_economist_role_id,
    settings.economist_role_id,
    settings.operator_role_id,
}


def serialize_permissions(current_user: CurrentUser) -> list[str]:
    return sorted(current_user.permissions)


def _can_manage_subordinate_target(current_user: CurrentUser, *, target_role_id: int) -> bool:
    if has_permission(current_user, PermissionCodes.PROFILE_MANAGE_ANY):
        return target_role_id in SUBORDINATE_PROFILE_ROLE_IDS
    if current_user.role_id == settings.superadmin_role_id:
        return target_role_id in SUBORDINATE_PROFILE_ROLE_IDS
    if current_user.role_id == settings.project_manager_role_id:
        return target_role_id in {
            settings.lead_economist_role_id,
            settings.economist_role_id,
            settings.operator_role_id,
        }
    if current_user.role_id in {settings.lead_economist_role_id, settings.economist_role_id}:
        return target_role_id in {
            settings.economist_role_id,
            settings.operator_role_id,
        }
    return False


class RequestActionBuilder:
    @staticmethod
    def build(
        current_user: CurrentUser,
        *,
        owner_user_id: str,
        status: str,
        can_manage_in_scope: bool,
        can_create_offer: bool = False,
        deleted_alert_count: int | None = None,
    ) -> RequestActionsSchema:
        can_edit = RequestPolicy.can_edit(current_user, request_owner_user_id=owner_user_id)
        can_edit_owned_unassigned = RequestPolicy.can_edit_owned_unassigned(
            current_user,
            request_owner_user_id=owner_user_id,
        )
        can_edit_in_scope = can_edit_owned_unassigned and can_manage_in_scope
        can_change_owner_in_scope = (
            RequestPolicy.can_change_owner(current_user, request_owner_user_id=owner_user_id)
            and can_manage_in_scope
        )
        return RequestActionsSchema(
            can_view_details=UserPolicy.can_view_requests(current_user),
            can_view_amounts=UserPolicy.can_view_request_amounts(current_user),
            can_open_contractor_view=has_permission(current_user, PermissionCodes.REQUESTS_CONTRACTOR_VIEW_READ),
            can_edit=can_edit_in_scope,
            can_change_owner=can_change_owner_in_scope,
            can_upload_files=has_permission(current_user, PermissionCodes.REQUESTS_FILES_UPLOAD) and can_edit_in_scope,
            can_delete_files=has_permission(current_user, PermissionCodes.REQUESTS_FILES_DELETE) and can_edit_in_scope,
            can_send_email_notifications=(
                has_permission(current_user, PermissionCodes.REQUESTS_EMAIL_NOTIFICATIONS_SEND)
                and can_edit_in_scope
                and status == "open"
            ),
            can_mark_deleted_alert_viewed=(
                has_permission(current_user, PermissionCodes.REQUESTS_DELETED_ALERTS_MARK_VIEWED)
                and can_edit_in_scope
                and (deleted_alert_count is None or deleted_alert_count > 0)
            ),
            can_create_offer=can_create_offer,
        )


class OfferActionBuilder:
    @staticmethod
    def build(
        current_user: CurrentUser,
        *,
        offer_owner_user_id: str,
        request_owner_user_id: str,
        contractor_user_id: str,
        offer_status: str,
        can_manage_in_scope: bool,
        offer_is_manual: bool = False,
    ) -> OfferActionsSchema:
        can_manage_request_offer = (
            RequestPolicy.can_edit(
                current_user,
                request_owner_user_id=request_owner_user_id,
            )
            and can_manage_in_scope
        )
        can_manage_own_offer = OfferPolicy.can_access_contractor_offer(
            current_user,
            offer_owner_user_id=offer_owner_user_id,
        )
        can_manage_offer = OfferPolicy.can_manage_offer(
            current_user,
            offer_owner_user_id=offer_owner_user_id,
            request_owner_user_id=request_owner_user_id,
        )
        is_contractor = current_user.role_id == settings.contractor_role_id
        can_upload_files_by_permission = (
            not is_contractor
            and has_permission(current_user, PermissionCodes.OFFERS_FILES_UPLOAD)
            and can_manage_offer
        )
        can_delete_files_by_permission = (
            not is_contractor
            and has_permission(current_user, PermissionCodes.OFFERS_FILES_DELETE)
            and can_manage_offer
        )
        can_update_status = has_permission(current_user, PermissionCodes.OFFERS_STATUS_UPDATE)
        return OfferActionsSchema(
            can_open_workspace=OfferPolicy.can_access_offer_workspace(
                current_user,
                offer_owner_user_id=offer_owner_user_id,
            ),
            can_view_contractor_info=OfferPolicy.can_view_contractor_info(
                current_user,
                contractor_user_id=contractor_user_id,
            ),
            can_edit_amount=(
                has_permission(current_user, PermissionCodes.OFFERS_AMOUNT_UPDATE)
                and can_manage_offer
                and (
                    current_user.role_id != settings.contractor_role_id
                    or offer_status not in {"accepted", "rejected"}
                )
            ),
            can_accept=can_update_status and can_manage_request_offer and offer_status != "accepted",
            can_reject=can_update_status and can_manage_request_offer and offer_status != "rejected",
            can_delete=(
                can_update_status
                and offer_status != "deleted"
                and (can_manage_request_offer or can_manage_own_offer)
            ),
            can_upload_files=(
                (
                    has_permission(current_user, PermissionCodes.OFFERS_FILES_UPLOAD)
                    and can_manage_offer
                    and offer_status not in {"accepted", "rejected"}
                )
                if is_contractor
                else can_upload_files_by_permission
            ),
            can_delete_files=(
                (
                    has_permission(current_user, PermissionCodes.OFFERS_FILES_DELETE)
                    and can_manage_offer
                )
                if is_contractor
                else can_delete_files_by_permission
            ),
        )


class ChatActionBuilder:
    @staticmethod
    def build(
        current_user: CurrentUser,
        *,
        offer_owner_user_id: str,
        request_owner_user_id: str,
        can_acknowledge_messages: bool,
        can_view_in_scope: bool,
        can_send_in_scope: bool,
    ) -> ChatActionsSchema:
        can_send_message = (
            OfferPolicy.can_send_chat_message(
                current_user,
                offer_owner_user_id=offer_owner_user_id,
                request_owner_user_id=request_owner_user_id,
            )
            and can_send_in_scope
        )
        return ChatActionsSchema(
            can_view_messages=(
                OfferPolicy.can_view_chat(
                    current_user,
                    offer_owner_user_id=offer_owner_user_id,
                )
                and can_view_in_scope
            ),
            can_send_message=can_send_message,
            can_attach_files=can_send_message and has_permission(current_user, PermissionCodes.CHAT_MESSAGE_ATTACH),
            can_mark_messages_received=(
                can_acknowledge_messages
                and has_permission(current_user, PermissionCodes.CHAT_RECEIPTS_MARK_RECEIVED)
            ),
            can_mark_messages_read=(
                can_acknowledge_messages
                and has_permission(current_user, PermissionCodes.CHAT_RECEIPTS_MARK_READ)
            ),
        )


class UserActionBuilder:
    @staticmethod
    def build_list_item(
        current_user: CurrentUser,
        *,
        target_user_id: str,
        target_role_id: int,
        target_tg_user_id: int | None = None,
    ) -> UserActionsSchema:
        can_manage_subordinate_target = _can_manage_subordinate_target(
            current_user,
            target_role_id=target_role_id,
        ) and target_user_id != current_user.user_id
        can_update_manager_target_role = target_role_id in {
            settings.lead_economist_role_id,
            settings.economist_role_id,
        }
        has_role_update_any = has_permission(current_user, PermissionCodes.USERS_ROLE_UPDATE_ANY)
        has_role_update_economy = has_permission(current_user, PermissionCodes.USERS_ROLE_UPDATE_ECONOMY)
        can_update_role = False
        if has_role_update_any and target_role_id != settings.superadmin_role_id:
            can_update_role = True
        elif has_role_update_economy:
            can_update_role = (
                current_user.role_id in {settings.project_manager_role_id, settings.lead_economist_role_id}
                and target_role_id in ECONOMY_ROLE_IDS
                and can_manage_subordinate_target
            )
        can_update_status = UserPolicy.can_update_user_status(current_user)
        if current_user.role_id in {
            settings.project_manager_role_id,
            settings.lead_economist_role_id,
            settings.economist_role_id,
        }:
            can_update_status = can_update_status and can_manage_subordinate_target
        return UserActionsSchema(
            can_view_profile=can_manage_subordinate_target,
            can_update_status=can_update_status,
            can_update_role=can_update_role,
            can_update_manager=(
                UserPolicy.can_update_user_manager(current_user)
                and can_manage_subordinate_target
                and can_update_manager_target_role
            ),
            can_manage_manual_contractor=(
                UserPolicy.can_manage_manual_contractors(current_user)
                and target_role_id == settings.contractor_role_id
                and target_tg_user_id is None
            ),
        )

    @staticmethod
    def build_me(current_user: CurrentUser) -> UserActionsSchema:
        return UserActionsSchema(
            can_manage_own_profile=UserPolicy.can_manage_own_profile(current_user),
            can_manage_credentials=False,
            can_manage_company_contacts=UserPolicy.can_manage_own_company_contacts(current_user),
            can_manage_own_unavailability=UserPolicy.can_manage_own_unavailability(current_user),
        )

    @staticmethod
    def build_subordinate_profile(
        current_user: CurrentUser,
        *,
        target_role_id: int,
    ) -> UserActionsSchema:
        can_manage_subordinate_target = _can_manage_subordinate_target(
            current_user,
            target_role_id=target_role_id,
        )
        can_update_manager_target_role = target_role_id in {
            settings.lead_economist_role_id,
            settings.economist_role_id,
        }
        can_manage_subordinate = (
            UserPolicy.can_manage_subordinate_unavailability(current_user)
            and can_manage_subordinate_target
        )
        can_update_status = (
            UserPolicy.can_update_user_status(current_user)
            and can_manage_subordinate_target
        )
        return UserActionsSchema(
            can_view_profile=can_manage_subordinate_target,
            can_update_status=can_update_status,
            can_update_manager=(
                UserPolicy.can_update_user_manager(current_user)
                and can_manage_subordinate_target
                and can_update_manager_target_role
            ),
            can_manage_subordinate_unavailability=can_manage_subordinate,
        )


@dataclass(frozen=True, slots=True)
class ResolvedOfferActionContext:
    offer_owner_user_id: str
    request_owner_user_id: str
    request_id: int
    offer_is_manual: bool
    can_create_new_offer: bool
    can_acknowledge_messages: bool
    can_manage_request_in_scope: bool
    offer_actions: OfferActionsSchema
    chat_actions: ChatActionsSchema


class OfferActionResolver:
    def __init__(
        self,
        *,
        offers: OfferRepository,
        requests: RequestRepository,
        chats: ChatRepository,
        users: UserRepository,
    ) -> None:
        self._offers = offers
        self._requests = requests
        self._chats = chats
        self._users = users

    async def resolve_workspace_context(
        self,
        *,
        current_user: CurrentUser,
        offer_id: int,
    ) -> ResolvedOfferActionContext:
        offer = await self._offers.get_by_id(offer_id=offer_id)
        if offer is None:
            raise NotFound("Offer not found")

        request = await self._requests.get_by_id(request_id=offer.id_request)
        if request is None:
            raise NotFound("Request not found")
        offer_owner = await self._users.get_by_id(user_id=offer.id_user)
        if offer_owner is None:
            raise NotFound("Offer owner not found")
        offer_is_manual = (
            offer_owner.id_role == settings.contractor_role_id
            and offer_owner.tg_user_id is None
        )

        can_create_new_offer = False
        if current_user.role_id == settings.contractor_role_id and current_user.user_id == offer.id_user:
            latest_offer = await self._offers.get_contractor_offer_for_request(
                request_id=request.id,
                contractor_user_id=current_user.user_id,
            )
            can_create_new_offer = (
                request.status == "open"
                and (latest_offer is None or latest_offer.status == "deleted")
            )

        can_acknowledge_messages = False
        chat = await self._offers.get_chat(offer_id=offer.id)
        if chat is not None:
            participant = await self._chats.get_active_participant(chat_id=chat.id, user_id=current_user.user_id)
            can_acknowledge_messages = participant is not None

        staff_scope = StaffAccessScopeService(self._users)
        if current_user.role_id == settings.contractor_role_id:
            can_manage_in_scope = current_user.user_id == offer.id_user
            can_view_in_scope = can_manage_in_scope
            can_send_in_scope = can_manage_in_scope
        else:
            can_manage_in_scope = await staff_scope.can_manage_request_owner(
                current_user=current_user,
                request_owner_user_id=request.id_user,
            )
            can_view_in_scope = await staff_scope.can_view_chat_for_request(
                current_user=current_user,
                request_owner_user_id=request.id_user,
            )
            can_send_in_scope = await staff_scope.can_send_chat_for_request(
                current_user=current_user,
                request_owner_user_id=request.id_user,
            )

        offer_actions = OfferActionBuilder.build(
            current_user,
            offer_owner_user_id=offer.id_user,
            request_owner_user_id=request.id_user,
            contractor_user_id=offer.id_user,
            offer_status=offer.status,
            can_manage_in_scope=can_manage_in_scope,
            offer_is_manual=offer_is_manual,
        )
        chat_actions = ChatActionBuilder.build(
            current_user,
            offer_owner_user_id=offer.id_user,
            request_owner_user_id=request.id_user,
            can_acknowledge_messages=can_acknowledge_messages,
            can_view_in_scope=can_view_in_scope,
            can_send_in_scope=can_send_in_scope,
        )
        return ResolvedOfferActionContext(
            offer_owner_user_id=offer.id_user,
            request_owner_user_id=request.id_user,
            request_id=request.id,
            offer_is_manual=offer_is_manual,
            can_create_new_offer=can_create_new_offer,
            can_acknowledge_messages=can_acknowledge_messages,
            can_manage_request_in_scope=can_manage_in_scope,
            offer_actions=offer_actions,
            chat_actions=chat_actions,
        )
