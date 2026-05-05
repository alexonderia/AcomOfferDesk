from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from app.core.config import settings
from app.domain.authorization import require_permission
from app.domain.exceptions import Conflict, Forbidden,  NotFound
from app.domain.permissions import PermissionCodes
from app.domain.policies import CurrentUser, RequestPolicy, UserPolicy
from app.repositories.files import FileRepository
from app.repositories.offers import OfferRepository
from app.repositories.requests import RequestRepository
from app.repositories.user_status_periods import UserStatusPeriodRepository
from app.repositories.users import UserRepository
from app.services.email_notifications import EmailNotificationService
from app.services.files import FileService
from app.services.tg_notifications import notify_new_request, notify_request_status_changed

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

def format_request_status(status: str | None) -> str:
    if not status:
        return "не указан"
    return REQUEST_STATUS_LABELS.get(status, status)


def format_offer_status(status: str | None) -> str:
    if not status:
        return "не указан"
    return OFFER_STATUS_LABELS.get(status, status)


@dataclass(frozen=True)
class RequestFileCreateInput:
    original_name: str
    content_bytes: bytes
    mime_type: str


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
    request_id: int
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
    request_id: int
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
    request_id: int
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
    chosen_offer_id: int | None
    id_plan: int | None
    count_submitted: int
    count_deleted_alert: int
    count_accepted_total: int
    count_rejected_total: int
    unread_messages_count: int
    files: list[RequestFileItem] = field(default_factory=list)
    offers: list[OfferItem] = field(default_factory=list)


@dataclass(frozen=True)
class DeletedAlertViewedResult:
    request_id: int
    count_deleted_alert: int
    updated_at: datetime


@dataclass(frozen=True)
class RequestEmailNotificationResult:
    request_id: int
    sent_to: list[str]


class RequestService:
    def __init__(
        self,
        requests: RequestRepository,
        files: FileRepository,
        users: UserRepository,
        offers: OfferRepository,
        user_status_periods: UserStatusPeriodRepository,
        email_notifications: EmailNotificationService | None = None,
        file_service: FileService | None = None,
    ):
        self._requests = requests
        self._files = files
        self._users = users
        self._offers = offers
        self._user_status_periods = user_status_periods
        self._email_notifications = email_notifications
        self._file_service = file_service or FileService(files)

    async def create_request(
        self,
        *,
        current_user: CurrentUser,
        deadline_at: datetime,
        description: str | None,
        initial_amount: float | None,
        id_plan: int | None = None,
        files: list[RequestFileCreateInput],
        additional_emails: list[str] | None = None,
        hidden_contractor_ids: list[str] | None = None,
    ) -> tuple[int, list[int]]:
        UserPolicy.ensure_can_create_request(current_user)
        if deadline_at < datetime.utcnow():
            raise Conflict("Deadline cannot be in the past")
        if not files:
            raise Conflict("At least one file is required")
        self._validate_amount(value=initial_amount, field_name="Initial amount")
        await self._ensure_plan_assignment_allowed(
            current_user=current_user,
            plan_id=id_plan,
        )
        normalized_additional_emails = self._normalize_additional_emails(additional_emails)
        normalized_hidden_contractor_ids = await self._normalize_hidden_contractor_ids(hidden_contractor_ids)

        request = await self._requests.create(
            id_user=current_user.user_id,
            deadline_at=deadline_at,
            description=description,
            initial_amount=initial_amount,
            id_plan=id_plan,
        )

        file_ids: list[int] = []
        partner_card_file_id = await self._attach_partner_card_file(request_id=request.id)
        file_ids.append(partner_card_file_id)
        for file_item in files:
            prepared = await self._file_service.prepare_bytes(
                original_name=file_item.original_name,
                content_bytes=file_item.content_bytes,
                mime_type=file_item.mime_type,
            )
            db_file = await self._file_service.create_request_file(
                request_id=request.id,
                upload=prepared,
            )
            await self._requests.attach_file(request_id=request.id, file_id=db_file.id)
            file_ids.append(db_file.id)

        await self._requests.hide_from_contractors(
            request_id=request.id,
            contractor_user_ids=normalized_hidden_contractor_ids,
        )

        if settings.telegram_legacy_enabled:
            tg_ids = await self._users.list_active_approved_contractor_tg_ids(
                contractor_role_id=settings.contractor_role_id,
                exclude_user_ids=normalized_hidden_contractor_ids,
            )
            await notify_new_request(
                tg_ids=tg_ids,
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

        return request.id, file_ids

    async def send_request_email_notification(
        self,
        *,
        current_user: CurrentUser,
        request_id: int,
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
        request_id: int,
        data: RequestEditInput,
    ) -> None:
        request = await self._requests.get_by_id(request_id=request_id)
        if request is None:
            raise NotFound("Request not found")

        has_request_edit_changes = any(
            value is not None
            for value in (
                data.initial_amount,
                data.final_amount,
                data.status,
                data.deadline_at,
            )
        ) or data.id_plan_provided
        if has_request_edit_changes:
            await self._ensure_can_edit_owned_unassigned_request(
                current_user=current_user,
                request_owner_user_id=request.id_user,
            )
        has_amount_changes = data.initial_amount is not None or data.final_amount is not None
        if has_amount_changes:
            require_permission(
                current_user,
                PermissionCodes.REQUESTS_AMOUNTS_READ,
                message="Insufficient permissions to update request amounts",
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
            status_changed = data.status != request.status
            closed_at = request.closed_at
            chosen_offer_id = request.id_offer
            if data.status == "closed":
                closed_at = datetime.utcnow()
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
                    await notify_request_status_changed(tg_id=tg_id)

        if data.deadline_at is not None:
            if data.deadline_at < datetime.utcnow():
                raise Conflict("Deadline cannot be in the past")
            await self._requests.update_deadline(request=request, deadline_at=data.deadline_at)

        if data.owner_user_id is not None:
            RequestPolicy.ensure_can_change_owner(current_user, request_owner_user_id=request.id_user)
            owner = await self._users.get_by_id(data.owner_user_id)
            if owner is None:
                raise NotFound("Owner user not found")
            
            if current_user.role_id in {
                settings.project_manager_role_id,
                settings.lead_economist_role_id,
            }:
                if owner.id == current_user.user_id:
                    raise Forbidden("Owner must be from current user's subordinates")
                is_subordinate = await self._is_descendant(
                    ancestor_user_id=current_user.user_id,
                    target_user_id=owner.id,
                )
                if not is_subordinate:
                    raise Forbidden("Owner must be from current user's subordinates")

            owner_unavailability = await self._user_status_periods.get_active_for_user(user_id=owner.id)
            if owner_unavailability is not None:
                raise Conflict(
                    "Owner user is unavailable in selected period "
                    f"{owner_unavailability.started_at.isoformat()} - {owner_unavailability.ended_at.isoformat()}"
                )
            await self._requests.update_owner(request=request, user_id=data.owner_user_id)

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
        cursor_id: str | None = target_user_id
        visited: set[str] = set()

        while cursor_id is not None and cursor_id not in visited:
            visited.add(cursor_id)
            if cursor_id == ancestor_user_id:
                return True
            cursor_user = await self._users.get_by_id(cursor_id)
            if cursor_user is None:
                return False
            cursor_id = cursor_user.id_parent

        return False

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
    
    async def mark_deleted_alert_viewed(self, *, current_user: CurrentUser, request_id: int) -> DeletedAlertViewedResult:
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
        request_id: int,
        file_data: RequestFileCreateInput,
    ) -> int:
        require_permission(
            current_user,
            PermissionCodes.REQUESTS_FILES_UPLOAD,
            message="Insufficient permissions to upload request files",
        )
        request = await self._requests.get_by_id(request_id=request_id)
        if request is None:
            raise NotFound("Request not found")

        await self._ensure_can_edit_request(
            current_user=current_user,
            request_owner_user_id=request.id_user,
        )

        prepared = await self._file_service.prepare_bytes(
            original_name=file_data.original_name,
            content_bytes=file_data.content_bytes,
            mime_type=file_data.mime_type,
        )
        db_file = await self._file_service.create_request_file(
            request_id=request.id,
            upload=prepared,
        )
        await self._requests.attach_file(request_id=request.id, file_id=db_file.id)
        return db_file.id

    async def remove_file(
        self,
        *,
        current_user: CurrentUser,
        request_id: int,
        file_id: int,
    ) -> None:
        require_permission(
            current_user,
            PermissionCodes.REQUESTS_FILES_DELETE,
            message="Insufficient permissions to delete request files",
        )
        request = await self._requests.get_by_id(request_id=request_id)
        if request is None:
            raise NotFound("Request not found")

        await self._ensure_can_edit_request(
            current_user=current_user,
            request_owner_user_id=request.id_user,
        )

        detached = await self._requests.detach_file(request_id=request_id, file_id=file_id)
        if not detached:
            raise NotFound("File is not attached to request")

        await self._file_service.delete_file(file_id=file_id)

    async def _attach_partner_card_file(self, *, request_id: int) -> int:
        partner_card = await self._files.get_normative_file(normative_id=PARTNER_CARD_NORMATIVE_ID)
        if partner_card is None:
            raise Conflict("Partner card file is not configured")

        db_file = await self._files.create(
            storage_object_id=partner_card.id_storage_object,
            original_name=partner_card.original_name,
        )
        await self._requests.attach_file(request_id=request_id, file_id=db_file.id)
        return db_file.id


    async def list_requests(self, *, current_user: CurrentUser) -> list[RequestListItem]:
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
        rows = await self._requests.list_open_with_files_for_contractor(contractor_user_id=current_user.user_id)
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
        rows = await self._requests.list_with_offers_for_contractor(contractor_user_id=current_user.user_id)

        grouped: dict[int, OpenRequestListItem] = {}
        request_offer_ids: dict[int, set[int]] = {}
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


    async def get_request_details(self, *, current_user: CurrentUser, request_id: int) -> RequestDetailItem:
        UserPolicy.ensure_can_view_requests(current_user)

        request_row = await self._requests.get_with_stats(request_id=request_id)
        if request_row is None:
            raise NotFound("Request not found")

        request, stats, owner_profile = request_row
        allowed_owner_ids = await self._resolve_visible_owner_ids_for_staff_scope(current_user=current_user)
        if allowed_owner_ids is not None:
            if request.id_user not in set(allowed_owner_ids):
                raise Forbidden("Request is outside your management scope")
        request_files = await self._requests.list_files(request_id=request_id)
        request_file_items = [
            RequestFileItem(id=file.id, path=file.path, name=file.name)
            for file in request_files
        ]

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
            chosen_offer_id=request.id_offer,
            id_plan=request.id_plan,
            count_submitted=stats.count_submitted if stats else 0,
            count_deleted_alert=stats.count_deleted_alert if stats else 0,
            count_accepted_total=stats.count_accepted_total if stats else 0,
            count_rejected_total=stats.count_rejected_total if stats else 0,
            unread_messages_count=sum(offer_item.unread_messages_count for offer_item in offers_by_id.values()),
            files=request_file_items,
            offers=list(offers_by_id.values()),
        )

    async def _resolve_visible_owner_ids_for_staff_scope(self, *, current_user: CurrentUser) -> list[str] | None:
        if current_user.role_id in {settings.project_manager_role_id, settings.lead_economist_role_id}:
            return await self._resolve_visible_owner_ids_for_hierarchy_root(root_user_id=current_user.user_id)
        if current_user.role_id == settings.economist_role_id:
            lead_root_user_id = await self._resolve_lead_economist_scope_root_user_id(
                current_user_id=current_user.user_id,
            )
            return await self._resolve_visible_owner_ids_for_hierarchy_root(root_user_id=lead_root_user_id)
        return None

    async def _ensure_can_edit_request(self, *, current_user: CurrentUser, request_owner_user_id: str) -> None:
        if current_user.role_id != settings.economist_role_id or request_owner_user_id == current_user.user_id:
            RequestPolicy.ensure_can_edit(current_user, request_owner_user_id=request_owner_user_id)
            return

        require_permission(
            current_user,
            PermissionCodes.REQUESTS_UPDATE,
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
        if current_user.role_id != settings.economist_role_id or request_owner_user_id == current_user.user_id:
            RequestPolicy.ensure_can_edit_owned_unassigned(
                current_user,
                request_owner_user_id=request_owner_user_id,
            )
            return

        require_permission(
            current_user,
            PermissionCodes.REQUESTS_UPDATE,
            message="Insufficient permissions to edit request",
        )
        if not await self._is_descendant(
            ancestor_user_id=current_user.user_id,
            target_user_id=request_owner_user_id,
        ):
            raise Forbidden("Economist can edit only own and subordinate requests")

    async def _resolve_lead_economist_scope_root_user_id(self, *, current_user_id: str) -> str:
        cursor_id: str | None = current_user_id
        visited: set[str] = set()

        while cursor_id is not None and cursor_id not in visited:
            visited.add(cursor_id)
            cursor_user = await self._users.get_by_id(cursor_id)
            if cursor_user is None:
                break
            if cursor_user.id_role == settings.lead_economist_role_id:
                return cursor_user.id
            cursor_id = cursor_user.id_parent

        return current_user_id

    async def _resolve_visible_owner_ids_for_hierarchy_root(self, *, root_user_id: str) -> list[str]:
        rows = await self._users.list_active_user_parent_pairs()
        children_by_parent: dict[str, list[str]] = {}
        for user_id, parent_id in rows:
            if parent_id is None:
                continue
            children_by_parent.setdefault(parent_id, []).append(user_id)

        visible: set[str] = {root_user_id}
        queue: list[str] = [root_user_id]
        while queue:
            manager_id = queue.pop()
            for child_id in children_by_parent.get(manager_id, []):
                if child_id in visible:
                    continue
                visible.add(child_id)
                queue.append(child_id)

        return list(visible)
