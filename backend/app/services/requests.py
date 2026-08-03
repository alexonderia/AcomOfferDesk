from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Awaitable, Callable

from app.core.config import settings
from app.core.datetime_utils import normalize_to_utc, utc_now, utc_now_naive
from app.domain.authorization import has_permission, require_any_permission, require_permission
from app.domain.exceptions import Conflict, Forbidden,  NotFound
from app.domain.permissions import PermissionCodes
from app.domain.policies import CurrentUser, RequestPolicy, UserPolicy
from app.repositories.economy_plans import EconomyPlanRepository
from app.repositories.files import FileRepository
from app.repositories.offers import OfferRepository
from app.repositories.requests import RequestRepository
from app.repositories.user_status_periods import UserStatusPeriodRepository
from app.repositories.users import UserRepository
from app.infrastructure.notification_publisher import publish_process_notification_event
from app.services.email_notifications import EmailNotificationService
from app.services.contractor_units import ContractorUnitService
from app.services.department_scope import DepartmentScopeService
from app.services.staff_access_scope import StaffAccessScopeService
from app.services.unit_hierarchy import UnitHierarchyService
from app.services.files import FileService, PreparedUpload
from app.services.notifications import NotificationService
from app.services.contractor_outbound_notifications import (
    RequestEventKind,
    notify_contractors_with_offers_about_request,
)
from app.services.max_notifications import notify_new_request as notify_max_new_request
from app.services.tg_notifications import notify_new_request, notify_request_status_changed
from app.services.user_notification_preferences import UserNotificationPreferencesService
from shared.process_notifications import ProcessNotificationEvent, build_process_notification_event

PARTNER_CARD_NORMATIVE_ID = 1
EDITABLE_REQUEST_STATUSES = {"open", "review", "closed", "cancelled"}

REQUEST_STATUS_LABELS = {
    "open": "открыта",
    "review": "на рассмотрении",
    "closed": "закрыта",
    "cancelled": "отменена",
}

OFFER_STATUS_LABELS = {
    "submitted": "на рассмотрении",
    "accepted": "принят",
    "rejected": "отклонён",
    "deleted": "удалён",
}

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _utcnow() -> datetime:
    return utc_now()


def _utcnow_naive() -> datetime:
    return utc_now_naive()


def _normalize_to_utc(value: datetime) -> datetime:
    return normalize_to_utc(value)

def format_request_status(status: str | None) -> str:
    if not status:
        return "не указан"
    return REQUEST_STATUS_LABELS.get(status, status)


def format_offer_status(status: str | None) -> str:
    if not status:
        return "не указан"
    return OFFER_STATUS_LABELS.get(status, status)


@dataclass(frozen=True)
class RequestEditInput:
    status: str | None = None
    deadline_at: datetime | None = None
    owner_user_id: str | None = None
    initial_amount: float | None = None
    final_amount: float | None = None
    id_plan: int | None = None
    id_plan_provided: bool = False


@dataclass(frozen=True)
class RequestFileItem:
    id: int
    path: str
    name: str


@dataclass(frozen=True)
class RequestListItem:
    request_id: str
    description: str | None
    status: str
    status_label: str
    deadline_at: datetime
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    owner_user_id: str
    owner_full_name: str | None
    chosen_offer_id: int | None
    id_plan: int | None
    count_submitted: int
    count_deleted_alert: int
    count_accepted_total: int
    count_rejected_total: int
    unread_messages_count: int
    files: list[RequestFileItem] = field(default_factory=list)


@dataclass(frozen=True)
class OpenRequestListItem:
    request_id: str
    description: str | None
    status: str
    status_label: str
    deadline_at: datetime
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    owner_user_id: str
    owner_full_name: str | None
    chosen_offer_id: int | None
    id_plan: int | None
    files: list[RequestFileItem] = field(default_factory=list)
    offers: list[OfferedRequestOfferItem] = field(default_factory=list)
    latest_offer_id: int | None = None
    latest_offer_status: str | None = None


@dataclass(frozen=True)
class OfferedRequestOfferItem:
    offer_id: int
    status: str
    unread_messages_count: int


@dataclass(frozen=True)
class OfferItem:
    offer_id: int
    contractor_user_id: str
    status: str
    status_label: str
    offer_amount: float | None
    created_at: datetime
    updated_at: datetime
    offer_workspace_url: str
    contractor_full_name: str | None
    contractor_phone: str | None
    contractor_mail: str | None
    contractor_company_name: str | None
    contractor_inn: str | None
    contractor_company_phone: str | None
    contractor_company_mail: str | None
    contractor_contact_phone: str | None
    contractor_contact_mail: str | None
    contractor_address: str | None = None
    contractor_note: str | None = None
    files: list[RequestFileItem] = field(default_factory=list)
    unread_messages_count: int = 0



@dataclass(frozen=True)
class RequestDetailItem:
    request_id: str
    description: str | None
    status: str
    status_label: str
    initial_amount: float | None
    final_amount: float | None
    deadline_at: datetime
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    owner_user_id: str
    owner_full_name: str | None
    owner_phone: str | None
    owner_mail: str | None
    chosen_offer_id: int | None
    id_plan: int | None
    count_submitted: int
    count_deleted_alert: int
    count_accepted_total: int
    count_rejected_total: int
    unread_messages_count: int
    plan_name: str | None = None
    files: list[RequestFileItem] = field(default_factory=list)
    offers: list[OfferItem] = field(default_factory=list)


@dataclass(frozen=True)
class DeletedAlertViewedResult:
    request_id: str
    count_deleted_alert: int
    updated_at: datetime


@dataclass(frozen=True)
class RequestEmailNotificationResult:
    request_id: str
    sent_to: list[str]


class RequestService:
    def __init__(
        self,
        requests: RequestRepository,
        files: FileRepository,
        users: UserRepository,
        offers: OfferRepository,
        user_status_periods: UserStatusPeriodRepository,
        plans: EconomyPlanRepository | None = None,
        email_notifications: EmailNotificationService | None = None,
        file_service: FileService | None = None,
        notifications: NotificationService | None = None,
        notification_preferences: UserNotificationPreferencesService | None = None,
        after_commit_hook_registrar: Callable[[Callable[[], Awaitable[None]]], None] | None = None,
        process_event_publisher: Callable[[ProcessNotificationEvent], Awaitable[bool]] | None = None,
    ):
        self._requests = requests
        self._files = files
        self._users = users
        self._offers = offers
        self._user_status_periods = user_status_periods
        self._plans = plans
        self._email_notifications = email_notifications
        self._file_service = file_service or FileService(files)
        self._notifications = notifications
        self._notification_preferences = notification_preferences
        self._after_commit_hook_registrar = after_commit_hook_registrar
        self._process_event_publisher = process_event_publisher or publish_process_notification_event
        self._department_scope = DepartmentScopeService(users)
        self._staff_scope = StaffAccessScopeService(users)

    def _contractor_unit_service(self) -> ContractorUnitService:
        return ContractorUnitService(users=self._users)

    def _schedule_process_notification_event(self, event: ProcessNotificationEvent) -> bool:
        if self._after_commit_hook_registrar is None:
            return False
        self._after_commit_hook_registrar(
            lambda: self._process_event_publisher(event)
        )
        return True

    def _schedule_contractor_request_outbound(
        self,
        *,
        request_id: str,
        event_kind: RequestEventKind,
        actor_user_id: str | None = None,
        previous_status: str | None = None,
        new_status: str | None = None,
    ) -> None:
        if self._after_commit_hook_registrar is None:
            return
        self._after_commit_hook_registrar(
            lambda: notify_contractors_with_offers_about_request(
                request_id=request_id,
                event_kind=event_kind,
                actor_user_id=actor_user_id,
                previous_status=previous_status,
                new_status=new_status,
            )
        )

    async def check_request_id_available(self, *, request_id: str) -> tuple[bool, str | None]:
        normalized_id = request_id.strip()
        if not normalized_id:
            return False, "empty"
        if await self._requests.exists_by_id(request_id=normalized_id):
            return False, "already_exists"
        return True, None

    async def create_request(
        self,
        *,
        current_user: CurrentUser,
        request_id: str | None = None,
        deadline_at: datetime,
        description: str | None,
        initial_amount: float | None,
        id_plan: int | None = None,
        normative_file_id: int | None = None,
        files: list[PreparedUpload],
        additional_emails: list[str] | None = None,
        hidden_contractor_ids: list[str] | None = None,
    ) -> tuple[str, list[int]]:
        UserPolicy.ensure_can_create_request(current_user)
        UserPolicy.ensure_can_view_normative_files(current_user)
        if normative_file_id is None:
            raise Conflict("Для создания заявки необходимо выбрать актуальный нормативный документ")
        if not files:
            raise Conflict("Прикрепите файл заявки")
        if _normalize_to_utc(deadline_at) < _utcnow():
            raise Conflict("Deadline cannot be in the past")
        self._validate_amount(value=initial_amount, field_name="Initial amount")
        await self._ensure_plan_assignment_allowed(
            current_user=current_user,
            plan_id=id_plan,
        )
        normalized_additional_emails = self._normalize_additional_emails(additional_emails)
        normalized_hidden_contractor_ids = await self._normalize_hidden_contractor_ids(hidden_contractor_ids)

        normalized_request_id: str | None = None
        if request_id is not None:
            normalized_request_id = request_id.strip()
            if not normalized_request_id:
                raise Conflict("Request id cannot be empty")
            if await self._requests.exists_by_id(request_id=normalized_request_id):
                raise Conflict("Request with this id already exists")

        request = await self._requests.create(
            request_id=normalized_request_id,
            id_user=current_user.user_id,
            deadline_at=deadline_at,
            description=description,
            initial_amount=initial_amount,
            id_plan=id_plan,
        )

        file_ids: list[int] = []
        normative_file_id_value = await self._attach_normative_file_copy(
            request_id=request.id,
            normative_file_id=normative_file_id,
        )
        file_ids.append(normative_file_id_value)
        for file_item in files:
            db_file = await self._file_service.create_request_file(
                request_id=request.id,
                upload=file_item,
            )
            await self._requests.attach_file(request_id=request.id, file_id=db_file.id)
            file_ids.append(db_file.id)

        await self._requests.hide_from_contractors(
            request_id=request.id,
            contractor_user_ids=normalized_hidden_contractor_ids,
        )

        visible_contractor_user_ids = await self._contractor_unit_service().filter_contractor_user_ids_for_request_owner(
            contractor_user_ids=await self._requests.list_active_keycloak_visible_contractor_user_ids(
                request_id=request.id,
                contractor_role_id=settings.contractor_role_id,
            ),
            request_owner_user_id=request.id_user,
        )

        if settings.telegram_legacy_enabled:
            tg_recipients = await self._users.list_active_approved_contractor_tg_recipients(
                contractor_role_id=settings.contractor_role_id,
                exclude_user_ids=normalized_hidden_contractor_ids,
            )
            tg_ids = [
                tg_id
                for contractor_user_id, tg_id in tg_recipients
                if contractor_user_id in set(visible_contractor_user_ids)
            ]
            await notify_new_request(
                tg_ids=tg_ids,
                request_id=request.id,
                description=description,
                deadline_at=deadline_at,
            )

        if settings.max_bot_enabled:
            max_recipients = await self._users.list_active_approved_contractor_max_recipients(
                contractor_role_id=settings.contractor_role_id,
                exclude_user_ids=normalized_hidden_contractor_ids,
            )
            max_user_ids: list[str] = []
            for contractor_user_id, max_user_id in max_recipients:
                if contractor_user_id not in set(visible_contractor_user_ids):
                    continue
                if self._notification_preferences is not None:
                    is_enabled = await self._notification_preferences.is_channel_enabled(
                        user_id=contractor_user_id,
                        channel_type="max",
                        notification_type="request",
                    )
                    if not is_enabled:
                        continue
                max_user_ids.append(max_user_id)
            await notify_max_new_request(
                max_user_ids=max_user_ids,
                request_id=request.id,
                description=description,
                deadline_at=deadline_at,
            )

        if self._email_notifications is not None:
            await self._email_notifications.notify_new_request(
                request_id=request.id,
                additional_emails=normalized_additional_emails,
                hidden_contractor_ids=normalized_hidden_contractor_ids,
            )

        created_event = build_process_notification_event(
            event_type="request.created",
            actor_user_id=current_user.user_id,
            entity_type="request",
            entity_id=request.id,
            request_id=request.id,
            dedupe_key=f"request.created:{request.id}",
            payload={
                "responsible_user_id": request.id_user,
            },
        )
        self._schedule_process_notification_event(created_event)

        return request.id, file_ids

    async def send_request_email_notification(
        self,
        *,
        current_user: CurrentUser,
        request_id: str,
        additional_emails: list[str] | None,
    ) -> RequestEmailNotificationResult:
        require_permission(
            current_user,
            PermissionCodes.REQUESTS_EMAIL_NOTIFICATIONS_SEND,
            message="Insufficient permissions to send request email notifications",
        )
        request = await self._requests.get_by_id(request_id=request_id)
        if request is None:
            raise NotFound("Request not found")

        await self._ensure_can_edit_owned_unassigned_request(
            current_user=current_user,
            request_owner_user_id=request.id_user,
        )

        if request.status != "open":
            raise Conflict("Only open request can be emailed manually")

        normalized_additional_emails = self._normalize_additional_emails(additional_emails)
        if not normalized_additional_emails:
            raise Conflict("At least one additional email is required")

        if self._email_notifications is None:
            raise Conflict("Email notifications are not configured")

        await self._email_notifications.notify_request_to_additional_emails(
            request_id=request.id,
            additional_emails=normalized_additional_emails,
            initiator_user_id=current_user.user_id,
        )
        return RequestEmailNotificationResult(
            request_id=request.id,
            sent_to=normalized_additional_emails,
        )

    def _normalize_additional_emails(self, emails: list[str] | None) -> list[str]:
        if not emails:
            return []

        normalized: list[str] = []
        seen: set[str] = set()
        for email in emails:
            candidate = email.strip().lower()
            if not candidate:
                continue
            if not EMAIL_PATTERN.fullmatch(candidate):
                raise Conflict("Invalid additional email")
            if candidate in seen:
                continue
            seen.add(candidate)
            normalized.append(candidate)
        return normalized

    async def _normalize_hidden_contractor_ids(self, contractor_ids: list[str] | None) -> list[str]:
        if not contractor_ids:
            return []

        normalized: list[str] = []
        seen: set[str] = set()
        for contractor_id in contractor_ids:
            candidate = contractor_id.strip()
            if not candidate or candidate in seen:
                continue
            contractor = await self._users.get_by_id(candidate)
            if contractor is None:
                raise NotFound("Hidden contractor user not found")
            if contractor.id_role != settings.contractor_role_id:
                raise Conflict("Hidden user must be contractor")
            seen.add(candidate)
            normalized.append(candidate)
        return normalized
    
    async def update_request(
        self,
        *,
        current_user: CurrentUser,
        request_id: str,
        data: RequestEditInput,
    ) -> None:
        request = await self._requests.get_by_id(request_id=request_id)
        if request is None:
            raise NotFound("Request not found")

        has_general_edit_changes = any(
            value is not None
            for value in (
                data.initial_amount,
                data.final_amount,
                data.deadline_at,
            )
        ) or data.id_plan_provided
        has_status_change = data.status is not None
        if has_general_edit_changes:
            await self._ensure_can_edit_owned_unassigned_request(
                current_user=current_user,
                request_owner_user_id=request.id_user,
            )
        if has_status_change:
            await self._ensure_can_status_update_request(
                current_user=current_user,
                request_owner_user_id=request.id_user,
            )

        has_pricing_changes = data.initial_amount is not None or data.final_amount is not None
        has_deadline_change = data.deadline_at is not None

        if has_pricing_changes:
            require_permission(
                current_user,
                PermissionCodes.REQUESTS_PRICING_UPDATE,
                message="Insufficient permissions to update request amounts",
            )
            require_permission(
                current_user,
                PermissionCodes.REQUESTS_AMOUNTS_READ,
                message="Insufficient permissions to update request amounts",
            )
        if has_deadline_change:
            require_permission(
                current_user,
                PermissionCodes.REQUESTS_DEADLINE_UPDATE,
                message="Insufficient permissions to update request deadline",
            )

        if data.initial_amount is not None:
            self._validate_amount(value=data.initial_amount, field_name="Initial amount")
            await self._requests.update_initial_amount(request=request, initial_amount=data.initial_amount)

        if data.final_amount is not None:
            self._validate_amount(value=data.final_amount, field_name="Final amount")
            await self._requests.update_final_amount(request=request, final_amount=data.final_amount)

        resulting_status = data.status if data.status is not None else request.status

        if data.status is not None:
            if data.status not in EDITABLE_REQUEST_STATUSES:
                raise Conflict("Unsupported request status")
            previous_status = request.status
            status_changed = data.status != request.status
            closed_at = request.closed_at
            chosen_offer_id = request.id_offer
            if data.status == "closed":
                closed_at = _utcnow_naive()
                chosen_offer_id = await self._requests.get_latest_accepted_offer_id(request_id=request.id)
                accepted_offer = await self._offers.get_by_id(offer_id=chosen_offer_id) if chosen_offer_id is not None else None
                self._validate_closed_request_amounts(
                    request=request,
                    accepted_offer=accepted_offer,
                )

            await self._requests.update_status(
                request=request,
                status=data.status,
                closed_at=closed_at,
                chosen_offer_id=chosen_offer_id,
            )
            if status_changed and settings.telegram_legacy_enabled:
                tg_ids = await self._offers.list_contractor_tg_ids_for_request(
                    request_id=request.id,
                    contractor_role_id=settings.contractor_role_id,
                )
                for tg_id in tg_ids:
                    await notify_request_status_changed(
                        tg_id=tg_id,
                        request_id=request.id,
                        previous_status=previous_status,
                        new_status=data.status,
                    )
            if status_changed:
                self._schedule_contractor_request_outbound(
                    request_id=request.id,
                    event_kind="status_changed",
                    actor_user_id=current_user.user_id,
                    previous_status=previous_status,
                    new_status=data.status,
                )
            if status_changed:
                event = build_process_notification_event(
                    event_type="request.status_changed",
                    actor_user_id=current_user.user_id,
                    entity_type="request",
                    entity_id=request.id,
                    request_id=request.id,
                    dedupe_key=f"request.status_changed:{request.id}:{data.status}",
                    payload={
                        "responsible_user_id": request.id_user,
                        "old_status": previous_status,
                        "new_status": data.status,
                    },
                )
                is_scheduled = self._schedule_process_notification_event(event)
                if not is_scheduled and self._notifications is not None:
                    await self._notifications.notify_request_status_changed(
                        actor_user_id=current_user.user_id,
                        recipient_user_id=request.id_user,
                        request_id=request.id,
                        previous_status=previous_status,
                        new_status=data.status,
                    )

        if data.deadline_at is not None:
            if _normalize_to_utc(data.deadline_at) < _utcnow():
                raise Conflict("Deadline cannot be in the past")
            previous_deadline_iso = request.deadline_at.isoformat() if request.deadline_at is not None else None
            await self._requests.update_deadline(request=request, deadline_at=data.deadline_at)
            deadline_event = build_process_notification_event(
                event_type="request.deadline_changed",
                actor_user_id=current_user.user_id,
                entity_type="request",
                entity_id=request.id,
                request_id=request.id,
                dedupe_key=f"request.deadline_changed:{request.id}:{data.deadline_at.isoformat()}",
                payload={
                    "responsible_user_id": request.id_user,
                    "old_deadline": previous_deadline_iso,
                    "new_deadline": data.deadline_at.isoformat(),
                },
            )
            self._schedule_process_notification_event(deadline_event)
            self._schedule_contractor_request_outbound(
                request_id=request.id,
                event_kind="deadline_changed",
                actor_user_id=current_user.user_id,
            )

        if data.owner_user_id is not None:
            owner = await self._users.get_by_id(data.owner_user_id)
            if owner is None:
                raise NotFound("Owner user not found")

            await self._ensure_can_assign_request_owner(
                current_user=current_user,
                request_owner_user_id=request.id_user,
                new_owner_user_id=owner.id,
            )

            owner_unavailability = await self._user_status_periods.get_active_for_user(user_id=owner.id)
            if owner_unavailability is not None:
                raise Conflict(
                    "Owner user is unavailable in selected period "
                    f"{owner_unavailability.started_at.isoformat()} - {owner_unavailability.ended_at.isoformat()}"
                )
            previous_owner_user_id = request.id_user
            await self._requests.update_owner(request=request, user_id=data.owner_user_id)
            if previous_owner_user_id != data.owner_user_id:
                previous_owner_was_operator = await self._is_request_owned_by_operator(
                    request_owner_user_id=previous_owner_user_id,
                )
                owner_event = build_process_notification_event(
                    event_type="request.responsible_changed",
                    actor_user_id=current_user.user_id,
                    entity_type="request",
                    entity_id=request.id,
                    request_id=request.id,
                    dedupe_key=f"request.responsible_changed:{request.id}:{previous_owner_user_id}:{data.owner_user_id}",
                    payload={
                        "old_responsible_user_id": previous_owner_user_id,
                        "new_responsible_user_id": data.owner_user_id,
                        "assigned_from_operator": previous_owner_was_operator,
                    },
                )
                self._schedule_process_notification_event(owner_event)

        if data.id_plan_provided:
            await self._ensure_plan_assignment_allowed(
                current_user=current_user,
                plan_id=data.id_plan,
            )
            await self._requests.update_plan(request=request, plan_id=data.id_plan)

        if resulting_status == "closed" and data.status != "closed":
            accepted_offer_id = request.id_offer or await self._requests.get_latest_accepted_offer_id(request_id=request.id)
            accepted_offer = await self._offers.get_by_id(offer_id=accepted_offer_id) if accepted_offer_id is not None else None
            self._validate_closed_request_amounts(
                request=request,
                accepted_offer=accepted_offer,
            )

    async def _is_descendant(self, *, ancestor_user_id: str, target_user_id: str) -> bool:
        if ancestor_user_id == target_user_id:
            return True
        return await UnitHierarchyService(self._users).is_manager_of(
            manager_user_id=ancestor_user_id,
            subordinate_user_id=target_user_id,
        )

    async def _ensure_plan_assignment_allowed(
        self,
        *,
        current_user: CurrentUser,
        plan_id: int | None,
    ) -> None:
        if plan_id is None:
            return
        if plan_id <= 0:
            raise Conflict("Plan ID must be positive")
        plan_owner_user_id = await self._requests.get_economy_plan_owner_user_id(plan_id=plan_id)
        if plan_owner_user_id is None:
            raise NotFound("Plan not found")
        if current_user.role_id == settings.superadmin_role_id:
            return
        if await self._is_descendant(
            ancestor_user_id=current_user.user_id,
            target_user_id=plan_owner_user_id,
        ):
            return
        raise Forbidden("Selected plan is outside your management scope")

    def _validate_amount(self, *, value: float | None, field_name: str) -> None:
        if value is None:
            return
        if value < 0:
            raise Conflict(f"{field_name} cannot be negative")

    def _validate_closed_request_amounts(self, *, request, accepted_offer) -> None:
        if request.initial_amount is None:
            raise Conflict("Initial amount is required to close request")
        if request.final_amount is None:
            raise Conflict("Final amount is required to close request")

        initial_amount = Decimal(str(request.initial_amount))
        final_amount = Decimal(str(request.final_amount))
        if accepted_offer is None:
            if final_amount != initial_amount:
                raise Conflict("Final amount must match initial amount when request is closed without accepted offer")
            return

        if accepted_offer.offer_amount is None:
            raise Conflict("Accepted offer amount is required when request is closed with accepted offer")

        offer_amount = Decimal(str(accepted_offer.offer_amount))
        if final_amount != initial_amount and final_amount != offer_amount:
            raise Conflict("Final amount must match initial amount or accepted offer amount")
    
    async def mark_deleted_alert_viewed(self, *, current_user: CurrentUser, request_id: str) -> DeletedAlertViewedResult:
        require_permission(
            current_user,
            PermissionCodes.REQUESTS_DELETED_ALERTS_MARK_VIEWED,
            message="Insufficient permissions to update deleted request alerts",
        )
        request = await self._requests.get_by_id(request_id=request_id)
        if request is None:
            raise NotFound("Request not found")

        await self._ensure_can_edit_request(
            current_user=current_user,
            request_owner_user_id=request.id_user,
        )

        updated_stats = await self._requests.decrement_deleted_alert(request_id=request_id)
        if updated_stats is None:
            raise NotFound("Request offer stats not found")

        return DeletedAlertViewedResult(
            request_id=updated_stats.request_id,
            count_deleted_alert=updated_stats.count_deleted_alert,
            updated_at=updated_stats.updated_at,
        )

    async def attach_file(
        self,
        *,
        current_user: CurrentUser,
        request_id: str,
        file_data: PreparedUpload,
    ) -> int:
        request = await self._requests.get_by_id(request_id=request_id)
        if request is None:
            raise NotFound("Request not found")

        await self._ensure_can_manage_request_files(
            current_user=current_user,
            request_owner_user_id=request.id_user,
            upload=True,
        )

        db_file = await self._file_service.create_request_file(
            request_id=request.id,
            upload=file_data,
        )
        await self._requests.attach_file(request_id=request.id, file_id=db_file.id)
        original_name = getattr(db_file, "original_name", None) or file_data.original_name
        self._schedule_process_notification_event(
            build_process_notification_event(
                event_type="request.files_changed",
                actor_user_id=current_user.user_id,
                entity_type="request",
                entity_id=request.id,
                request_id=request.id,
                dedupe_key=f"request.files_changed:{request.id}:{db_file.id}",
                payload={
                    "request_id": request.id,
                    "actor_user_id": current_user.user_id,
                    "file_ids": [db_file.id],
                    "changed_file_count": 1,
                    "original_names": [original_name],
                },
            )
        )
        self._schedule_contractor_request_outbound(
            request_id=request.id,
            event_kind="files_changed",
            actor_user_id=current_user.user_id,
        )
        return db_file.id

    async def remove_file(
        self,
        *,
        current_user: CurrentUser,
        request_id: str,
        file_id: int,
    ) -> None:
        request = await self._requests.get_by_id(request_id=request_id)
        if request is None:
            raise NotFound("Request not found")

        await self._ensure_can_manage_request_files(
            current_user=current_user,
            request_owner_user_id=request.id_user,
            upload=False,
        )

        detached = await self._requests.detach_file(request_id=request_id, file_id=file_id)
        if not detached:
            raise NotFound("File is not attached to request")

        await self._file_service.delete_file(file_id=file_id)
        self._schedule_process_notification_event(
            build_process_notification_event(
                event_type="request.files_changed",
                actor_user_id=current_user.user_id,
                entity_type="request",
                entity_id=request.id,
                request_id=request.id,
                dedupe_key=f"request.files_changed:{request.id}:{file_id}:deleted",
                payload={
                    "request_id": request.id,
                    "actor_user_id": current_user.user_id,
                    "file_ids": [file_id],
                    "changed_file_count": 1,
                },
            )
        )
        self._schedule_contractor_request_outbound(
            request_id=request.id,
            event_kind="files_changed",
            actor_user_id=current_user.user_id,
        )

    async def _attach_normative_file_copy(self, *, request_id: str, normative_file_id: int) -> int:
        normative_status = await self._files.get_normative_file_status(normative_id=normative_file_id)
        if normative_status is None:
            raise Conflict("Для создания заявки необходимо выбрать актуальный нормативный документ")
        if normative_status != "actual":
            raise Conflict("Выбранный нормативный документ больше не актуален")

        normative_file = await self._files.get_normative_file(normative_id=normative_file_id)
        if normative_file is None:
            raise Conflict("Для создания заявки необходимо выбрать актуальный нормативный документ")

        db_file = await self._files.create(
            storage_object_id=normative_file.id_storage_object,
            original_name=normative_file.original_name,
        )
        await self._requests.attach_file(request_id=request_id, file_id=db_file.id)
        return db_file.id

    async def _attach_partner_card_file(self, *, request_id: str) -> int:
        return await self._attach_normative_file_copy(
            request_id=request_id,
            normative_file_id=PARTNER_CARD_NORMATIVE_ID,
        )


    async def list_requests(self, *, current_user: CurrentUser) -> list[RequestListItem]:
        if not (
            UserPolicy.can_view_requests(current_user)
            or has_permission(current_user, PermissionCodes.DEPARTMENT_REQUESTS_READ)
        ):
            UserPolicy.ensure_can_view_requests(current_user)
        owner_scope_ids = await self._resolve_visible_owner_ids_for_staff_scope(current_user=current_user)

        rows = await self._requests.list_with_stats_and_files(
            current_user_id=current_user.user_id,
            owner_user_ids=owner_scope_ids,
        )

        return [
            RequestListItem(
                request_id=request.id,
                description=request.description,
                status=request.status,
                status_label=format_request_status(request.status),
                deadline_at=request.deadline_at,
                created_at=request.created_at,
                updated_at=request.updated_at,
                closed_at=request.closed_at,
                owner_user_id=request.id_user,
                owner_full_name=profile.full_name if profile else None,
                chosen_offer_id=request.id_offer,
                id_plan=request.id_plan,
                count_submitted=stats.count_submitted if stats else 0,
                count_deleted_alert=stats.count_deleted_alert if stats else 0,
                count_accepted_total=stats.count_accepted_total if stats else 0,
                count_rejected_total=stats.count_rejected_total if stats else 0,
                unread_messages_count=unread_messages_count,
                files=[],
            )
            for request, stats, profile, unread_messages_count in rows
        ]


    async def list_open_requests_for_contractor(self, *, current_user: CurrentUser) -> list[OpenRequestListItem]:
        UserPolicy.ensure_can_view_open_requests(current_user)
        rows = await self._contractor_unit_service().filter_rows_by_request_owner_scope(
            contractor_user_id=current_user.user_id,
            rows=await self._requests.list_open_with_files_for_contractor(contractor_user_id=current_user.user_id),
            owner_user_id_getter=lambda row: row[0].id_user,
        )
        latest_offers_by_request_id = {
            offer.id_request: offer
            for offer in await self._offers.list_latest_contractor_offers_by_request_ids(
                contractor_user_id=current_user.user_id,
                request_ids=[request.id for request, _ in rows],
            )
        }

        return [
            OpenRequestListItem(
                request_id=request.id,
                description=request.description,
                status=request.status,
                status_label=format_request_status(request.status),
                deadline_at=request.deadline_at,
                created_at=request.created_at,
                updated_at=request.updated_at,
                closed_at=request.closed_at,
                owner_user_id=request.id_user,
                owner_full_name=profile.full_name if profile else None,
                chosen_offer_id=request.id_offer,
                id_plan=request.id_plan,
                files=[],
                latest_offer_id=latest_offers_by_request_id.get(request.id).id if request.id in latest_offers_by_request_id else None,
                latest_offer_status=latest_offers_by_request_id.get(request.id).status if request.id in latest_offers_by_request_id else None,
            )
            for request, profile in rows
        ]


    async def list_offered_requests_for_contractor(self, *, current_user: CurrentUser) -> list[OpenRequestListItem]:
        UserPolicy.ensure_can_view_offered_requests(current_user)
        rows = await self._contractor_unit_service().filter_rows_by_request_owner_scope(
            contractor_user_id=current_user.user_id,
            rows=await self._requests.list_with_offers_for_contractor(contractor_user_id=current_user.user_id),
            owner_user_id_getter=lambda row: row[0].id_user,
        )

        grouped: dict[str, OpenRequestListItem] = {}
        request_offer_ids: dict[str, set[int]] = {}
        for request, offer, profile, unread_messages_count in rows:
            existing = grouped.get(request.id)
            
            if existing is None:
                existing = OpenRequestListItem(
                    request_id=request.id,
                    description=request.description,
                    status=request.status,
                    status_label=format_request_status(request.status),
                    deadline_at=request.deadline_at,
                    created_at=request.created_at,
                    updated_at=request.updated_at,
                    closed_at=request.closed_at,
                    owner_user_id=request.id_user,
                    owner_full_name=profile.full_name if profile else None,
                    chosen_offer_id=None,
                    id_plan=request.id_plan,
                    files=[],
                    offers=[],
                    latest_offer_id=offer.id,
                    latest_offer_status=offer.status,
                )
                grouped[request.id] = existing
                request_offer_ids[request.id] = set()

            if offer.id not in request_offer_ids[request.id]:
                request_offer_ids[request.id].add(offer.id)
                existing.offers.append(
                    OfferedRequestOfferItem(
                        offer_id=offer.id,
                        status=offer.status,
                        unread_messages_count=unread_messages_count,
                    )
                )
                

        return list(grouped.values())
    
    
    async def list_open_requests(self, *, current_user: CurrentUser) -> list[RequestListItem]:
        UserPolicy.ensure_can_view_open_requests(current_user)
        owner_scope_ids = await self._resolve_visible_owner_ids_for_staff_scope(current_user=current_user)
        if owner_scope_ids is not None:
            rows = await self._requests.list_open_with_stats_and_files_by_owner_ids(owner_ids=owner_scope_ids)
        else:
            rows = await self._requests.list_open_with_stats_and_files()

        return [
            RequestListItem(
                request_id=request.id,
                description=request.description,
                status=request.status,
                status_label=format_request_status(request.status),
                deadline_at=request.deadline_at,
                created_at=request.created_at,
                updated_at=request.updated_at,
                closed_at=request.closed_at,
                owner_user_id=request.id_user,
                owner_full_name=profile.full_name if profile else None,
                chosen_offer_id=request.id_offer,
                id_plan=request.id_plan,
                count_submitted=stats.count_submitted if stats else 0,
                count_deleted_alert=stats.count_deleted_alert if stats else 0,
                count_accepted_total=stats.count_accepted_total if stats else 0,
                count_rejected_total=stats.count_rejected_total if stats else 0,
                unread_messages_count=0,
                files=[],
            )
            for request, stats, profile in rows
        ]


    async def get_request_details(self, *, current_user: CurrentUser, request_id: str) -> RequestDetailItem:
        if not (
            UserPolicy.can_view_requests(current_user)
            or has_permission(current_user, PermissionCodes.DEPARTMENT_REQUESTS_READ)
        ):
            UserPolicy.ensure_can_view_requests(current_user)

        request_row = await self._requests.get_with_stats(request_id=request_id)
        if request_row is None:
            raise NotFound("Request not found")

        request, stats, owner_profile = request_row
        await self._ensure_can_view_request_in_staff_scope(
            current_user=current_user,
            request_owner_user_id=request.id_user,
        )
        plan_name: str | None = None
        if request.id_plan is not None and self._plans is not None:
            plan = await self._plans.get_by_id(plan_id=request.id_plan)
            plan_name = plan.name if plan is not None else None
        request_files = await self._requests.list_files(request_id=request_id)
        request_file_items = [
            RequestFileItem(id=file.id, path=file.path, name=file.name)
            for file in request_files
        ]

        # Within one department requests are visible together with their offers;
        # edit/chat checks are enforced separately per action.
        can_view_offers = current_user.role_id != settings.contractor_role_id

        offer_rows = []
        if can_view_offers:
            offer_rows = await self._requests.list_offers_with_files_and_contacts(
                request_id=request_id,
                current_user_id=current_user.user_id,
            )
        offers_by_id: dict[int, OfferItem] = {}
        for offer, offer_file, profile, company_contact, unread_messages_count in offer_rows:
            offer_item = offers_by_id.get(offer.id)
            if offer_item is None:
                offer_item = OfferItem(
                    offer_id=offer.id,
                    contractor_user_id=offer.id_user,
                    status=offer.status,
                    status_label=format_offer_status(offer.status),
                    offer_amount=offer.offer_amount,
                    created_at=offer.created_at,
                    updated_at=offer.updated_at,
                    offer_workspace_url=f"/api/v1/offers/{offer.id}/workspace",
                    contractor_full_name=profile.full_name if profile else None,
                    contractor_phone=(company_contact.phone if company_contact else (profile.phone if profile else None)),
                    contractor_mail=(company_contact.mail if company_contact else (profile.mail if profile else None)),
                    contractor_inn=company_contact.inn if company_contact else None,
                    contractor_company_name=company_contact.company_name if company_contact else None,
                    contractor_company_phone=company_contact.phone if company_contact else None,
                    contractor_company_mail=company_contact.mail if company_contact else None,
                    contractor_contact_phone=profile.phone if profile else None,
                    contractor_contact_mail=profile.mail if profile else None,
                    contractor_address=company_contact.address if company_contact else None,
                    contractor_note=company_contact.note if company_contact else None,
                    files=[],
                    unread_messages_count=unread_messages_count,
                )
                offers_by_id[offer.id] = offer_item

            if offer_file is not None:
                offer_item.files.append(RequestFileItem(id=offer_file.id, path=offer_file.path, name=offer_file.name))

        return RequestDetailItem(
            request_id=request.id,
            description=request.description,
            status=request.status,
            status_label=format_request_status(request.status),
            initial_amount=request.initial_amount,
            final_amount=request.final_amount,
            deadline_at=request.deadline_at,
            created_at=request.created_at,
            updated_at=request.updated_at,
            closed_at=request.closed_at,
            owner_user_id=request.id_user,
            owner_full_name=owner_profile.full_name if owner_profile else None,
            owner_phone=owner_profile.phone if owner_profile else None,
            owner_mail=owner_profile.mail if owner_profile else None,
            chosen_offer_id=request.id_offer,
            id_plan=request.id_plan,
            plan_name=plan_name,
            count_submitted=stats.count_submitted if stats else 0,
            count_deleted_alert=stats.count_deleted_alert if stats else 0,
            count_accepted_total=stats.count_accepted_total if stats else 0,
            count_rejected_total=stats.count_rejected_total if stats else 0,
            unread_messages_count=sum(offer_item.unread_messages_count for offer_item in offers_by_id.values()),
            files=request_file_items,
            offers=list(offers_by_id.values()),
        )

    async def _resolve_visible_owner_ids_for_staff_scope(self, *, current_user: CurrentUser) -> list[str] | None:
        if current_user.role_id == settings.superadmin_role_id:
            return None
        if current_user.role_id == settings.operator_role_id:
            # Operator sees only own requests that are still unassigned (owner role is operator).
            return [current_user.user_id]

        # Project manager: the whole root-unit department (подразделение) they belong to,
        # combined with their hierarchy department subtree as a base (which deliberately stops
        # at any nested project manager, who owns a separate subdivision).
        if current_user.role_id == settings.project_manager_role_id:
            owners: set[str] = {current_user.user_id}
            owners.update(
                await self._department_scope.resolve_department_owner_ids_for_current_user(
                    current_user=current_user,
                )
            )
            return list(owners)

        if current_user.role_id in {
            settings.lead_economist_role_id,
            settings.economist_role_id,
        }:
            owners = {current_user.user_id}
            owners.update(
                await self._department_scope.resolve_unit_scope_owner_ids_for_user(
                    user_id=current_user.user_id,
                )
            )
            if has_permission(current_user, PermissionCodes.DEPARTMENT_REQUESTS_READ):
                owners.update(
                    await self._department_scope.resolve_department_owner_ids_for_current_user(
                        current_user=current_user,
                    )
                )
            return list(owners)
        # Non-hierarchy roles must not receive implicit global request visibility.
        return []

    async def _ensure_can_view_request_in_staff_scope(
        self,
        *,
        current_user: CurrentUser,
        request_owner_user_id: str,
    ) -> None:
        allowed_owner_ids = await self._resolve_visible_owner_ids_for_staff_scope(current_user=current_user)
        if allowed_owner_ids is None:
            return
        if request_owner_user_id not in set(allowed_owner_ids):
            raise Forbidden("Request is outside your management scope")
        if current_user.role_id != settings.operator_role_id:
            return
        if not await self._is_request_owned_by_operator(request_owner_user_id=request_owner_user_id):
            raise Forbidden("Request is no longer available for operator")

    async def _ensure_can_manage_request_files(
        self,
        *,
        current_user: CurrentUser,
        request_owner_user_id: str,
        upload: bool,
    ) -> None:
        if await self._can_edit_department_requests(
            current_user=current_user,
            request_owner_user_id=request_owner_user_id,
        ):
            return

        if upload:
            require_permission(
                current_user,
                PermissionCodes.REQUESTS_FILES_UPLOAD,
                message="Insufficient permissions to upload request files",
            )
        else:
            require_permission(
                current_user,
                PermissionCodes.REQUESTS_FILES_DELETE,
                message="Insufficient permissions to delete request files",
            )

        await self._ensure_can_edit_request_without_department_scope(
            current_user=current_user,
            request_owner_user_id=request_owner_user_id,
        )

    async def _ensure_can_edit_request(self, *, current_user: CurrentUser, request_owner_user_id: str) -> None:
        if await self._can_edit_department_requests(
            current_user=current_user,
            request_owner_user_id=request_owner_user_id,
        ):
            return
        if current_user.role_id != settings.economist_role_id or request_owner_user_id == current_user.user_id:
            RequestPolicy.ensure_can_edit(current_user, request_owner_user_id=request_owner_user_id)
            return

        require_any_permission(
            current_user,
            (
                PermissionCodes.REQUESTS_UPDATE,
                PermissionCodes.REQUESTS_PRICING_UPDATE,
                PermissionCodes.REQUESTS_DEADLINE_UPDATE,
                PermissionCodes.REQUESTS_STATUS_UPDATE,
            ),
            message="Insufficient permissions to edit request",
        )
        if not await self._is_descendant(
            ancestor_user_id=current_user.user_id,
            target_user_id=request_owner_user_id,
        ):
            raise Forbidden("Economist can edit only own and subordinate requests")

    async def _ensure_can_edit_owned_unassigned_request(
        self,
        *,
        current_user: CurrentUser,
        request_owner_user_id: str,
    ) -> None:
        if await self._can_edit_department_requests(
            current_user=current_user,
            request_owner_user_id=request_owner_user_id,
        ):
            return
        if current_user.role_id != settings.economist_role_id or request_owner_user_id == current_user.user_id:
            RequestPolicy.ensure_can_edit_owned_unassigned(
                current_user,
                request_owner_user_id=request_owner_user_id,
            )
            return

        require_any_permission(
            current_user,
            (
                PermissionCodes.REQUESTS_UPDATE,
                PermissionCodes.REQUESTS_PRICING_UPDATE,
                PermissionCodes.REQUESTS_DEADLINE_UPDATE,
                PermissionCodes.REQUESTS_STATUS_UPDATE,
            ),
            message="Insufficient permissions to edit request",
        )
        if not await self._is_descendant(
            ancestor_user_id=current_user.user_id,
            target_user_id=request_owner_user_id,
        ):
            raise Forbidden("Economist can edit only own and subordinate requests")

    async def _ensure_can_edit_request_without_department_scope(
        self,
        *,
        current_user: CurrentUser,
        request_owner_user_id: str,
    ) -> None:
        if current_user.role_id in {settings.project_manager_role_id, settings.lead_economist_role_id}:
            if not await self._is_inside_hierarchy_management_scope(
                current_user=current_user,
                request_owner_user_id=request_owner_user_id,
            ):
                raise Forbidden("Request is outside your management scope")

        if current_user.role_id != settings.economist_role_id or request_owner_user_id == current_user.user_id:
            RequestPolicy.ensure_can_edit(current_user, request_owner_user_id=request_owner_user_id)
            return

        require_any_permission(
            current_user,
            (
                PermissionCodes.REQUESTS_UPDATE,
                PermissionCodes.REQUESTS_PRICING_UPDATE,
                PermissionCodes.REQUESTS_DEADLINE_UPDATE,
                PermissionCodes.REQUESTS_STATUS_UPDATE,
            ),
            message="Insufficient permissions to edit request",
        )
        if not await self._is_descendant(
            ancestor_user_id=current_user.user_id,
            target_user_id=request_owner_user_id,
        ):
            raise Forbidden("Economist can edit only own and subordinate requests")

    async def _is_inside_hierarchy_management_scope(
        self,
        *,
        current_user: CurrentUser,
        request_owner_user_id: str,
    ) -> bool:
        if request_owner_user_id == current_user.user_id:
            return True
        return await self._staff_scope.is_hierarchy_manager_of(
            current_user=current_user,
            request_owner_user_id=request_owner_user_id,
        )

    async def _is_request_owned_by_operator(self, *, request_owner_user_id: str) -> bool:
        owner = await self._users.get_by_id(request_owner_user_id)
        return owner is not None and owner.id_role == settings.operator_role_id

    async def _ensure_can_status_update_request(
        self,
        *,
        current_user: CurrentUser,
        request_owner_user_id: str,
    ) -> None:
        if has_permission(current_user, PermissionCodes.DEPARTMENT_REQUESTS_STATUS_UPDATE):
            if await self._is_user_inside_current_department_scope(
                current_user=current_user,
                target_user_id=request_owner_user_id,
            ):
                return
        await self._ensure_can_status_update_request_without_department_scope(
            current_user=current_user,
            request_owner_user_id=request_owner_user_id,
        )

    async def _ensure_can_status_update_request_without_department_scope(
        self,
        *,
        current_user: CurrentUser,
        request_owner_user_id: str,
    ) -> None:
        require_permission(
            current_user,
            PermissionCodes.REQUESTS_STATUS_UPDATE,
            message="Insufficient permissions to update request status",
        )
        if current_user.role_id == settings.operator_role_id:
            if current_user.user_id != request_owner_user_id:
                raise Forbidden("Operator can update status only for own requests")
            return

        await self._ensure_can_edit_request_without_department_scope(
            current_user=current_user,
            request_owner_user_id=request_owner_user_id,
        )

    async def _ensure_can_assign_request_owner(
        self,
        *,
        current_user: CurrentUser,
        request_owner_user_id: str,
        new_owner_user_id: str,
    ) -> None:
        if has_permission(current_user, PermissionCodes.DEPARTMENT_REQUESTS_ASSIGN):
            owner_inside = await self._is_user_inside_current_department_scope(
                current_user=current_user,
                target_user_id=request_owner_user_id,
            )
            new_owner_inside = await self._is_user_inside_current_department_scope(
                current_user=current_user,
                target_user_id=new_owner_user_id,
            )
            if owner_inside and new_owner_inside:
                return

        RequestPolicy.ensure_can_change_owner(current_user, request_owner_user_id=request_owner_user_id)
        if current_user.role_id in {
            settings.project_manager_role_id,
            settings.lead_economist_role_id,
        }:
            operator_owned = await self._is_request_owned_by_operator(
                request_owner_user_id=request_owner_user_id,
            )
            if not operator_owned and not await self._is_inside_hierarchy_management_scope(
                current_user=current_user,
                request_owner_user_id=request_owner_user_id,
            ):
                raise Forbidden("Request is outside your management scope")
            if new_owner_user_id != current_user.user_id:
                # New owner must stay inside the current user's unit-based
                # management contour.
                is_subordinate = await self._is_inside_hierarchy_management_scope(
                    current_user=current_user,
                    request_owner_user_id=new_owner_user_id,
                )
                if not is_subordinate:
                    raise Forbidden("Owner must be current user or current user's subordinate")

    async def _can_edit_department_requests(
        self,
        *,
        current_user: CurrentUser,
        request_owner_user_id: str,
    ) -> bool:
        if not has_permission(current_user, PermissionCodes.DEPARTMENT_REQUESTS_UPDATE):
            return False
        return await self._is_user_inside_current_department_scope(
            current_user=current_user,
            target_user_id=request_owner_user_id,
        )

    async def _is_user_inside_current_department_scope(
        self,
        *,
        current_user: CurrentUser,
        target_user_id: str,
    ) -> bool:
        department_user_ids = await self._department_scope.resolve_department_owner_ids_for_current_user(
            current_user=current_user,
        )
        return target_user_id in set(department_user_ids)

