from __future__ import annotations

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.authorization import has_permission, require_any_permission, require_permission
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
    def can_view_normative_files(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.NORMATIVE_FILES_READ)

    @staticmethod
    def ensure_can_view_normative_files(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.NORMATIVE_FILES_READ,
            message="Недостаточно прав для просмотра нормативных файлов",
        )

    @staticmethod
    def can_create_normative_files(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.NORMATIVE_FILES_CREATE)

    @staticmethod
    def ensure_can_create_normative_files(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.NORMATIVE_FILES_CREATE,
            message="Недостаточно прав для создания нормативных файлов",
        )

    @staticmethod
    def can_manage_normative_files(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.NORMATIVE_FILES_MANAGE)

    @staticmethod
    def ensure_can_manage_normative_files(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.NORMATIVE_FILES_MANAGE,
            message="Только ведущий экономист может управлять нормативными файлами",
        )

    @staticmethod
    def can_view_feedback(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.FEEDBACK_READ)

    @staticmethod
    def ensure_can_view_feedback(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.FEEDBACK_READ,
            message="Только суперадминистратор может просматривать обратную связь",
        )

    @staticmethod
    def can_create_feedback(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.FEEDBACK_CREATE)

    @staticmethod
    def ensure_can_create_feedback(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.FEEDBACK_CREATE,
            message="Недостаточно прав для создания обратной связи",
        )

    @staticmethod
    def can_manage_economist_users(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.USERS_CREATE)

    @staticmethod
    def ensure_can_manage_economist_users(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.USERS_CREATE,
            message="Только администратор, суперадминистратор и ведущий экономист могут управлять пользователями-экономистами",
        )

    @staticmethod
    def can_register_user(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.USERS_CREATE)

    @staticmethod
    def ensure_can_register_user(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.USERS_CREATE,
            message="Только администратор, суперадминистратор и ведущий экономист могут управлять пользователями-экономистами",
        )

    @staticmethod
    def can_login(status: str) -> bool:
        return status == "active"

    @staticmethod
    def ensure_can_login(status: str) -> None:
        if not UserPolicy.can_login(status):
            raise Forbidden("Пользователь не активен")

    @staticmethod
    def can_list_users(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.USERS_READ)

    @staticmethod
    def ensure_can_list_users(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.USERS_READ,
            message="Недостаточно прав для просмотра пользователей",
        )

    @staticmethod
    def can_update_user_status(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.USERS_STATUS_UPDATE)

    @staticmethod
    def ensure_can_update_user_status(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.USERS_STATUS_UPDATE,
            message="Только администратор, суперадминистратор, руководитель проекта, ведущий экономист и экономист могут обновлять статус пользователя",
        )

    @staticmethod
    def can_list_contractors(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.CONTRACTORS_READ)

    @staticmethod
    def ensure_can_list_contractors(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.CONTRACTORS_READ,
            message="Недостаточно прав для просмотра контрагентов",
        )

    @staticmethod
    def can_read_contractor_profile(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.CONTRACTORS_PROFILE_READ)

    @staticmethod
    def ensure_can_read_contractor_profile(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.CONTRACTORS_PROFILE_READ,
            message="Недостаточно прав для просмотра профиля контрагента",
        )

    @staticmethod
    def can_update_contractor_profile_status(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.CONTRACTORS_PROFILE_STATUS_UPDATE)

    @staticmethod
    def ensure_can_update_contractor_profile_status(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.CONTRACTORS_PROFILE_STATUS_UPDATE,
            message="Недостаточно прав для изменения статуса профиля контрагента",
        )

    @staticmethod
    def can_update_user_role(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.USERS_ROLE_UPDATE_ANY) or has_permission(
            current_user,
            PermissionCodes.USERS_ROLE_UPDATE_ECONOMY,
        )

    @staticmethod
    def ensure_can_update_user_role(current_user: CurrentUser) -> None:
        if UserPolicy.can_update_user_role(current_user):
            return
        raise Forbidden("Только администратор, суперадминистратор, руководитель проекта и ведущий экономист могут обновлять роли пользователей")

    @staticmethod
    def can_update_user_manager(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.USERS_MANAGER_UPDATE)

    @staticmethod
    def ensure_can_update_user_manager(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.USERS_MANAGER_UPDATE,
            message="Только руководитель проекта, ведущий экономист и экономист могут обновлять руководителя пользователя",
        )

    @staticmethod
    def can_manage_manual_contractors(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.CONTRACTORS_MANUAL_MANAGE)

    @staticmethod
    def can_create_manual_contractors(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.CONTRACTORS_MANUAL_CREATE)

    @staticmethod
    def ensure_can_create_manual_contractors(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.CONTRACTORS_MANUAL_CREATE,
            message="Недостаточно прав для создания ручных контрагентов",
        )

    @staticmethod
    def ensure_can_manage_manual_contractors(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.CONTRACTORS_MANUAL_MANAGE,
            message="Недостаточно прав для управления вручную созданными контрагентами",
        )

    @staticmethod
    def can_manage_own_profile(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.PROFILE_MANAGE_OWN)

    @staticmethod
    def ensure_can_manage_own_profile(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.PROFILE_MANAGE_OWN,
            message="Недостаточно прав для доступа к собственному профилю",
        )

    @staticmethod
    def can_manage_any_profile(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.PROFILE_MANAGE_ANY)

    @staticmethod
    def ensure_can_manage_any_profile(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.PROFILE_MANAGE_ANY,
            message="Недостаточно прав для управления профилями пользователей",
        )

    @staticmethod
    def can_manage_own_unavailability(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.UNAVAILABILITY_MANAGE_OWN) or has_permission(
            current_user,
            PermissionCodes.UNAVAILABILITY_MANAGE_ALL,
        )

    @staticmethod
    def ensure_can_manage_own_unavailability(current_user: CurrentUser) -> None:
        require_any_permission(
            current_user,
            (
                PermissionCodes.UNAVAILABILITY_MANAGE_OWN,
                PermissionCodes.UNAVAILABILITY_MANAGE_ALL,
            ),
            message="Недостаточно прав для управления периодом недоступности",
        )

    @staticmethod
    def can_manage_subordinate_unavailability(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.UNAVAILABILITY_MANAGE_SUBORDINATE) or has_permission(
            current_user,
            PermissionCodes.UNAVAILABILITY_MANAGE_ALL,
        )

    @staticmethod
    def ensure_can_manage_subordinate_unavailability(current_user: CurrentUser) -> None:
        require_any_permission(
            current_user,
            (
                PermissionCodes.UNAVAILABILITY_MANAGE_SUBORDINATE,
                PermissionCodes.UNAVAILABILITY_MANAGE_ALL,
            ),
            message="Недостаточно прав для управления периодом недоступности подчиненного",
        )

    @staticmethod
    def can_manage_own_company_contacts(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.COMPANY_CONTACTS_MANAGE_OWN)

    @staticmethod
    def ensure_can_manage_own_company_contacts(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.COMPANY_CONTACTS_MANAGE_OWN,
            message="Только контрагент может управлять контактами компании",
        )

    @staticmethod
    def can_manage_any_company_contacts(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.COMPANY_CONTACTS_MANAGE_ANY)

    @staticmethod
    def ensure_can_manage_any_company_contacts(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.COMPANY_CONTACTS_MANAGE_ANY,
            message="Недостаточно прав для управления контактами компании",
        )

    @staticmethod
    def can_manage_requests(current_user: CurrentUser) -> bool:
        return _is_allowed(lambda: UserPolicy.ensure_can_manage_requests(current_user))

    @staticmethod
    def ensure_can_manage_requests(current_user: CurrentUser) -> None:
        require_any_permission(
            current_user,
            (
                PermissionCodes.REQUESTS_UPDATE,
                PermissionCodes.REQUESTS_PRICING_UPDATE,
                PermissionCodes.REQUESTS_DEADLINE_UPDATE,
                PermissionCodes.REQUESTS_STATUS_UPDATE,
            ),
            message="Недостаточно прав для управления заявками",
        )
        if current_user.role_id == settings.operator_role_id:
            raise Forbidden("Недостаточно прав для управления заявками")

    @staticmethod
    def can_view_requests(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.REQUESTS_READ)

    @staticmethod
    def ensure_can_view_requests(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.REQUESTS_READ,
            message="Недостаточно прав для просмотра заявок",
        )

    @staticmethod
    def can_view_request_amounts(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.REQUESTS_AMOUNTS_READ)

    @staticmethod
    def ensure_can_view_request_amounts(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.REQUESTS_AMOUNTS_READ,
            message="Недостаточно прав для просмотра сумм заявок",
        )

    @staticmethod
    def can_create_request(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.REQUESTS_CREATE)

    @staticmethod
    def ensure_can_create_request(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.REQUESTS_CREATE,
            message="Недостаточно прав для создания заявки",
        )

    @staticmethod
    def can_view_open_requests(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.REQUESTS_OPEN_READ)

    @staticmethod
    def ensure_can_view_open_requests(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.REQUESTS_OPEN_READ,
            message="Недостаточно прав для просмотра открытых заявок",
        )

    @staticmethod
    def can_create_offer(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.OFFERS_CREATE)

    @staticmethod
    def ensure_can_create_offer(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.OFFERS_CREATE,
            message="Только контрагент может создавать предложения",
        )

    @staticmethod
    def can_view_offered_requests(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.REQUESTS_OFFERED_READ)

    @staticmethod
    def ensure_can_view_offered_requests(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.REQUESTS_OFFERED_READ,
            message="Только контрагент может просматривать заявки с предложениями",
        )

    @staticmethod
    def can_view_responsibility_dashboard(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.DASHBOARD_PROCESS_READ) and has_permission(
            current_user,
            PermissionCodes.DASHBOARD_SAVINGS_READ,
        )

    @staticmethod
    def ensure_can_view_responsibility_dashboard(current_user: CurrentUser) -> None:
        require_any_permission(
            current_user,
            (
                PermissionCodes.DASHBOARD_PROCESS_READ,
                PermissionCodes.DASHBOARD_SAVINGS_READ,
            ),
            message="Недостаточно прав для просмотра дашборда ответственности",
        )
        if not UserPolicy.can_view_responsibility_dashboard(current_user):
            raise Forbidden("Недостаточно прав для просмотра раздела экономии в дашборде ответственности")

    @staticmethod
    def can_view_plan(current_user: CurrentUser) -> bool:
        return has_permission(current_user, PermissionCodes.DASHBOARD_PLANS_READ)

    @staticmethod
    def ensure_can_view_plan(current_user: CurrentUser) -> None:
        require_permission(
            current_user,
            PermissionCodes.DASHBOARD_PLANS_READ,
            message="Недостаточно прав для просмотра планов",
        )


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
        require_any_permission(
            current_user,
            (
                PermissionCodes.REQUESTS_UPDATE,
                PermissionCodes.REQUESTS_PRICING_UPDATE,
                PermissionCodes.REQUESTS_DEADLINE_UPDATE,
                PermissionCodes.REQUESTS_STATUS_UPDATE,
            ),
            message="Недостаточно прав для редактирования заявки",
        )
        if current_user.role_id == settings.operator_role_id:
            raise Forbidden("Недостаточно прав для редактирования заявки")
        if current_user.role_id == settings.economist_role_id and current_user.user_id != request_owner_user_id:
            raise Forbidden("Экономист может редактировать только свои заявки")

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
        require_any_permission(
            current_user,
            (
                PermissionCodes.REQUESTS_UPDATE,
                PermissionCodes.REQUESTS_PRICING_UPDATE,
                PermissionCodes.REQUESTS_DEADLINE_UPDATE,
                PermissionCodes.REQUESTS_STATUS_UPDATE,
            ),
            message="Недостаточно прав для редактирования заявки",
        )
        if current_user.role_id == settings.operator_role_id:
            if current_user.user_id != request_owner_user_id:
                raise Forbidden("Оператор может редактировать только свои неназначенные заявки")
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
            message="Только ведущий экономист, руководитель проекта и суперадминистратор могут менять владельца заявки",
        )
        require_permission(
            current_user,
            PermissionCodes.REQUESTS_READ,
            message="Недостаточно прав для смены владельца заявки",
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
            message="Недостаточно прав для создания ручных предложений",
        )
        if current_user.role_id == settings.economist_role_id and current_user.user_id != request_owner_user_id:
            raise Forbidden("Экономист может создавать ручные предложения только для своих заявок")


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
            message="Недостаточно прав для просмотра информации о контрагенте",
        )
        if current_user.role_id == settings.contractor_role_id and current_user.user_id != contractor_user_id:
            raise Forbidden("Контрагент может просматривать только свой профиль")

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
            raise Forbidden("Только контрагент может получать доступ к своим предложениям")
        if current_user.user_id != offer_owner_user_id:
            raise Forbidden("Контрагент может получать доступ только к своим предложениям")

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
            message="Недостаточно прав для редактирования файлов ручного предложения",
        )
        RequestPolicy.ensure_can_edit(current_user, request_owner_user_id=request_owner_user_id)
        if not offer_is_manual:
            raise Forbidden("Файлы ручного предложения можно редактировать только для вручную созданных предложений")

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
            message="Недостаточно прав для просмотра рабочего пространства предложения",
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
            message="Недостаточно прав для просмотра чата",
        )
        if current_user.role_id == settings.contractor_role_id and current_user.user_id != offer_owner_user_id:
            raise Forbidden("Недостаточно прав для просмотра чата")

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
            message="Недостаточно прав для отправки сообщения в чат",
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

        raise Forbidden("Недостаточно прав для отправки сообщения в чат")

