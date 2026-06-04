from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Body, Depends, File, Form, Path as PathParam, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.api.action_flags import OfferActionBuilder, RequestActionBuilder
from app.api.dependencies import get_current_user, get_uow
from app.core.config import settings
from app.core.uow import UnitOfWork
from app.domain.authorization import has_permission
from app.domain.exceptions import Forbidden, NotFound
from app.domain.permissions import PermissionCodes
from app.domain.policies import CurrentUser, OfferPolicy, RequestPolicy, UserPolicy
from app.schemas.requests import (
    DeletedAlertViewed,
    DeletedAlertViewedResponse,
    OfferItemSchema,
    OfferedRequestOfferSchema,
    OpenRequestItemSchema,
    OpenRequestListData,
    OpenRequestListResponse,
    RequestCreateResponse,
    RequestIdAvailabilityResponse,
    RequestDetailsResponse,
    RequestDetailsResponseData,
    RequestDetailsSchema,
    RequestEditPayload,
    RequestEmailNotificationPayload,
    RequestEmailNotificationResponse,
    RequestFileMutationResponse,
    RequestFileSchema,
    RequestItemSchema,
    RequestListData,
    RequestListResponse,
    RequestMutationResponse,
    RequestOfferStatsSchema,
    RequestStatsSchema,
)
from app.services.email_notifications import EmailNotificationService
from app.services.files import FileService
from app.services.notifications import NotificationService
from app.services.department_scope import DepartmentScopeService
from app.services.requests import RequestEditInput, RequestFileCreateInput, RequestService
from app.services.staff_access_scope import StaffAccessScopeService

router = APIRouter()


def _request_id_as_str(value: str | int) -> str:
    return str(value)


def _build_notification_service(uow: UnitOfWork) -> NotificationService | None:
    notifications_repo = getattr(uow, "notifications", None)
    if notifications_repo is None:
        return None
    return NotificationService(notifications_repo)


def _build_request_service(
    uow: UnitOfWork,
    *,
    email_notifications: EmailNotificationService | None = None,
    file_service: FileService | None = None,
) -> RequestService:
    after_commit_hook_registrar = getattr(uow, "add_after_commit_hook", None)
    return RequestService(
        uow.requests,
        uow.files,
        uow.users,
        uow.offers,
        uow.user_status_periods,
        email_notifications=email_notifications,
        file_service=file_service,
        notifications=_build_notification_service(uow),
        after_commit_hook_registrar=after_commit_hook_registrar,
    )


def _request_file_schema(file_item) -> RequestFileSchema:
    return RequestFileSchema(
        id=file_item.id,
        path=file_item.path,
        name=file_item.name,
        download_url=f"/api/v1/files/{file_item.id}/download",
    )


def _request_stats_schema(item) -> RequestStatsSchema:
    return RequestStatsSchema(
        count_submitted=item.count_submitted,
        count_deleted_alert=item.count_deleted_alert,
        count_accepted_total=item.count_accepted_total,
        count_rejected_total=item.count_rejected_total,
    )


def _request_item_schema(
    current_user: CurrentUser,
    item,
    *,
    can_manage_in_scope: bool,
    can_update_status_in_scope: bool,
    can_change_owner_in_scope: bool,
) -> RequestItemSchema:
    return RequestItemSchema(
        request_id=_request_id_as_str(item.request_id),
        description=item.description,
        status=item.status,
        status_label=item.status_label,
        initial_amount=None,
        final_amount=None,
        deadline_at=item.deadline_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
        closed_at=item.closed_at,
        owner_user_id=item.owner_user_id,
        owner_full_name=item.owner_full_name,
        chosen_offer_id=item.chosen_offer_id,
        id_plan=item.id_plan,
        stats=_request_stats_schema(item),
        unread_messages_count=item.unread_messages_count,
        files=[_request_file_schema(file_item) for file_item in item.files],
        actions=RequestActionBuilder.build(
            current_user,
            owner_user_id=item.owner_user_id,
            status=item.status,
            can_manage_in_scope=can_manage_in_scope,
            can_update_status_in_scope=can_update_status_in_scope,
            can_change_owner_in_scope=can_change_owner_in_scope,
            deleted_alert_count=item.count_deleted_alert,
        ),
    )


def _open_request_item_schema(
    current_user: CurrentUser,
    item,
    *,
    can_manage_in_scope: bool,
    can_update_status_in_scope: bool,
    can_change_owner_in_scope: bool,
) -> OpenRequestItemSchema:
    can_create_offer = (
        current_user.role_id == settings.contractor_role_id
        and item.status == "open"
        and item.latest_offer_status in {None, "deleted"}
    )
    return OpenRequestItemSchema(
        request_id=_request_id_as_str(item.request_id),
        description=item.description,
        status=item.status,
        status_label=item.status_label,
        deadline_at=item.deadline_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
        closed_at=item.closed_at,
        owner_user_id=item.owner_user_id,
        owner_full_name=item.owner_full_name,
        chosen_offer_id=(None if current_user.role_id == settings.contractor_role_id else item.chosen_offer_id),
        id_plan=item.id_plan,
        files=[_request_file_schema(file_item) for file_item in item.files],
        offers=[
            OfferedRequestOfferSchema(
                offer_id=offer.offer_id,
                status=offer.status,
                unread_messages_count=offer.unread_messages_count,
                actions=OfferActionBuilder.build(
                    current_user,
                    offer_owner_user_id=current_user.user_id,
                    request_owner_user_id=item.owner_user_id,
                    contractor_user_id=current_user.user_id,
                    offer_status=offer.status,
                    can_manage_in_scope=True,
                ),
            )
            for offer in item.offers
        ],
        actions=RequestActionBuilder.build(
            current_user,
            owner_user_id=item.owner_user_id,
            status=item.status,
            can_manage_in_scope=can_manage_in_scope,
            can_update_status_in_scope=can_update_status_in_scope,
            can_change_owner_in_scope=can_change_owner_in_scope,
            can_create_offer=can_create_offer,
        ),
    )


async def _can_manage_request_in_scope(
    *,
    uow: UnitOfWork,
    current_user: CurrentUser,
    request_owner_user_id: str,
) -> bool:
    manageable_owner_ids = await _resolve_manageable_owner_ids_in_scope(
        uow=uow,
        current_user=current_user,
        owner_user_ids={request_owner_user_id},
    )
    return request_owner_user_id in manageable_owner_ids


async def _can_manage_offer_in_scope(
    *,
    uow: UnitOfWork,
    current_user: CurrentUser,
    request_owner_user_id: str,
) -> bool:
    if current_user.role_id == settings.contractor_role_id:
        return current_user.user_id == request_owner_user_id
    if current_user.role_id == settings.superadmin_role_id:
        return True

    users = getattr(uow, "users", None)
    if users is None or not callable(getattr(users, "get_by_id", None)):
        return False

    return await StaffAccessScopeService(users).is_hierarchy_manager_of(
        current_user=current_user,
        request_owner_user_id=request_owner_user_id,
    )


async def _can_update_request_status_in_scope(
    *,
    uow: UnitOfWork,
    current_user: CurrentUser,
    request_owner_user_id: str,
) -> bool:
    if current_user.role_id == settings.contractor_role_id:
        return False
    if current_user.role_id == settings.superadmin_role_id:
        return has_permission(current_user, PermissionCodes.REQUESTS_STATUS_UPDATE)

    users = getattr(uow, "users", None)
    if users is None or not callable(getattr(users, "get_by_id", None)):
        return False

    if has_permission(current_user, PermissionCodes.DEPARTMENT_REQUESTS_STATUS_UPDATE):
        is_inside_department_scope = await DepartmentScopeService(users).is_user_in_current_user_department(
            current_user=current_user,
            target_user_id=request_owner_user_id,
        )
        if is_inside_department_scope:
            return True

    if not has_permission(current_user, PermissionCodes.REQUESTS_STATUS_UPDATE):
        return False

    if current_user.role_id == settings.operator_role_id:
        return current_user.user_id == request_owner_user_id

    return await StaffAccessScopeService(users).is_hierarchy_manager_of(
        current_user=current_user,
        request_owner_user_id=request_owner_user_id,
    )


async def _can_change_request_owner_in_scope(
    *,
    uow: UnitOfWork,
    current_user: CurrentUser,
    request_owner_user_id: str,
) -> bool:
    if current_user.role_id == settings.contractor_role_id:
        return False

    users = getattr(uow, "users", None)
    if users is None or not callable(getattr(users, "get_by_id", None)):
        return False

    if has_permission(current_user, PermissionCodes.DEPARTMENT_REQUESTS_ASSIGN):
        is_inside_department_scope = await DepartmentScopeService(users).is_user_in_current_user_department(
            current_user=current_user,
            target_user_id=request_owner_user_id,
        )
        if is_inside_department_scope:
            return True

    if not RequestPolicy.can_change_owner(
        current_user,
        request_owner_user_id=request_owner_user_id,
    ):
        return False

    request_owner = await users.get_by_id(request_owner_user_id)
    if request_owner is not None and request_owner.id_role == settings.operator_role_id:
        return True

    if current_user.role_id in {
        settings.project_manager_role_id,
        settings.lead_economist_role_id,
    }:
        return await StaffAccessScopeService(users).is_hierarchy_manager_of(
            current_user=current_user,
            request_owner_user_id=request_owner_user_id,
        )

    return True


async def _resolve_manageable_owner_ids_in_scope(
    *,
    uow: UnitOfWork,
    current_user: CurrentUser,
    owner_user_ids: set[str],
) -> set[str]:
    if current_user.role_id == settings.contractor_role_id:
        return set()
    if not owner_user_ids:
        return set()
    users = getattr(uow, "users", None)
    if users is None or not callable(getattr(users, "get_by_id", None)):
        return set()
    return await StaffAccessScopeService(users).resolve_manageable_owner_ids(
        current_user=current_user,
        candidate_owner_ids=owner_user_ids,
    )


async def _can_update_offer_status_in_scope(
    *,
    uow: UnitOfWork,
    current_user: CurrentUser,
    request_owner_user_id: str,
    offer_owner_user_id: str,
    status: str,
) -> bool:
    users = getattr(uow, "users", None)
    if users is None or not callable(getattr(users, "get_by_id", None)):
        return False

    if has_permission(current_user, PermissionCodes.DEPARTMENT_OFFERS_ACCEPT) and status == "accepted":
        if await DepartmentScopeService(users).is_user_in_current_user_department(
            current_user=current_user,
            target_user_id=request_owner_user_id,
        ):
            return True
    if has_permission(current_user, PermissionCodes.DEPARTMENT_OFFERS_REJECT) and status == "rejected":
        if await DepartmentScopeService(users).is_user_in_current_user_department(
            current_user=current_user,
            target_user_id=request_owner_user_id,
        ):
            return True

    if not has_permission(current_user, PermissionCodes.OFFERS_STATUS_UPDATE):
        return False

    if current_user.role_id in {
        settings.project_manager_role_id,
        settings.lead_economist_role_id,
        settings.economist_role_id,
    }:
        if not await StaffAccessScopeService(users).is_hierarchy_manager_of(
            current_user=current_user,
            request_owner_user_id=request_owner_user_id,
        ):
            return False

    return OfferPolicy.can_manage_offer(
        current_user,
        offer_owner_user_id=offer_owner_user_id,
        request_owner_user_id=request_owner_user_id,
    )


async def _has_department_offer_update_scope(
    *,
    uow: UnitOfWork,
    current_user: CurrentUser,
    request_owner_user_id: str,
) -> bool:
    users = getattr(uow, "users", None)
    if users is None or not callable(getattr(users, "get_by_id", None)):
        return False
    if not has_permission(current_user, PermissionCodes.DEPARTMENT_OFFERS_UPDATE):
        return False
    return await DepartmentScopeService(users).is_user_in_current_user_department(
        current_user=current_user,
        target_user_id=request_owner_user_id,
    )


@router.get("/requests", response_model=RequestListResponse)
@router.get("/requests/", response_model=RequestListResponse, include_in_schema=False)
async def list_requests(
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> RequestListResponse:
    async with uow:
        service = _build_request_service(uow)
        items = await service.list_requests(current_user=current_user)
        manageable_owner_ids = await _resolve_manageable_owner_ids_in_scope(
            uow=uow,
            current_user=current_user,
            owner_user_ids={item.owner_user_id for item in items},
        )
        schema_items = []
        for item in items:
            can_manage_in_scope = item.owner_user_id in manageable_owner_ids
            can_update_status_in_scope = await _can_update_request_status_in_scope(
                uow=uow,
                current_user=current_user,
                request_owner_user_id=item.owner_user_id,
            )
            can_change_owner_in_scope = await _can_change_request_owner_in_scope(
                uow=uow,
                current_user=current_user,
                request_owner_user_id=item.owner_user_id,
            )
            schema_items.append(
                _request_item_schema(
                    current_user,
                    item,
                    can_manage_in_scope=can_manage_in_scope,
                    can_update_status_in_scope=can_update_status_in_scope,
                    can_change_owner_in_scope=can_change_owner_in_scope,
                )
            )

    return RequestListResponse(
        data=RequestListData(
            items=schema_items,
        ),
    )


@router.get("/requests/open", response_model=OpenRequestListResponse)
@router.get("/requests/open/", response_model=OpenRequestListResponse, include_in_schema=False)
async def list_open_requests(
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OpenRequestListResponse:
    async with uow:
        service = _build_request_service(uow)
        if current_user.role_id == settings.contractor_role_id:
            items = await service.list_open_requests_for_contractor(current_user=current_user)
            schema_items = [
                _open_request_item_schema(
                    current_user,
                    item,
                    can_manage_in_scope=False,
                    can_update_status_in_scope=False,
                    can_change_owner_in_scope=False,
                )
                for item in items
            ]
        else:
            items = await service.list_open_requests(current_user=current_user)
            manageable_owner_ids = await _resolve_manageable_owner_ids_in_scope(
                uow=uow,
                current_user=current_user,
                owner_user_ids={item.owner_user_id for item in items},
            )
            schema_items = []
            for item in items:
                can_manage_in_scope = item.owner_user_id in manageable_owner_ids
                can_update_status_in_scope = await _can_update_request_status_in_scope(
                    uow=uow,
                    current_user=current_user,
                    request_owner_user_id=item.owner_user_id,
                )
                can_change_owner_in_scope = await _can_change_request_owner_in_scope(
                    uow=uow,
                    current_user=current_user,
                    request_owner_user_id=item.owner_user_id,
                )
                schema_items.append(
                    _open_request_item_schema(
                        current_user,
                        item,
                        can_manage_in_scope=can_manage_in_scope,
                        can_update_status_in_scope=can_update_status_in_scope,
                        can_change_owner_in_scope=can_change_owner_in_scope,
                    )
                )

    return OpenRequestListResponse(
        data=OpenRequestListData(
            items=schema_items,
        ),
    )


@router.get("/requests/offered", response_model=OpenRequestListResponse)
@router.get("/requests/offered/", response_model=OpenRequestListResponse, include_in_schema=False)
async def list_offered_requests(
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OpenRequestListResponse:
    async with uow:
        service = _build_request_service(uow)
        items = await service.list_offered_requests_for_contractor(current_user=current_user)

    return OpenRequestListResponse(
        data=OpenRequestListData(
            items=[
                _open_request_item_schema(
                    current_user,
                    item,
                    can_manage_in_scope=False,
                    can_update_status_in_scope=False,
                    can_change_owner_in_scope=False,
                )
                for item in items
            ],
        ),
    )


@router.get("/requests/check-id", response_model=RequestIdAvailabilityResponse)
@router.get("/requests/check-id/", response_model=RequestIdAvailabilityResponse, include_in_schema=False)
async def check_request_id_availability(
    id: str = Query(..., min_length=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> RequestIdAvailabilityResponse:
    UserPolicy.ensure_can_create_request(current_user)
    normalized_id = id.strip()
    if not normalized_id:
        return RequestIdAvailabilityResponse(available=False, detail="Укажите номер заявки", reason="empty")

    async with uow:
        service = _build_request_service(uow)
        available, reason = await service.check_request_id_available(request_id=normalized_id)

    if available:
        return RequestIdAvailabilityResponse(available=True, detail="Номер заявки свободен")
    if reason == "already_exists":
        return RequestIdAvailabilityResponse(
            available=False,
            detail="Заявка с таким номером уже существует",
            reason="already_exists",
        )
    return RequestIdAvailabilityResponse(available=False, detail="Укажите номер заявки", reason=reason)


@router.get("/requests/{request_id}", response_model=RequestDetailsResponse)
@router.get("/requests/{request_id}/", response_model=RequestDetailsResponse, include_in_schema=False)
async def get_request_details(
    request_id: str = PathParam(..., min_length=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> RequestDetailsResponse:
    async with uow:
        service = _build_request_service(uow)
        item = await service.get_request_details(current_user=current_user, request_id=request_id)
        can_manage = await _can_manage_request_in_scope(
            uow=uow,
            current_user=current_user,
            request_owner_user_id=item.owner_user_id,
        )
        can_manage_offer = await _can_manage_offer_in_scope(
            uow=uow,
            current_user=current_user,
            request_owner_user_id=item.owner_user_id,
        )
        can_update_status = await _can_update_request_status_in_scope(
            uow=uow,
            current_user=current_user,
            request_owner_user_id=item.owner_user_id,
        )
        can_change_owner = await _can_change_request_owner_in_scope(
            uow=uow,
            current_user=current_user,
            request_owner_user_id=item.owner_user_id,
        )
    request_actions = RequestActionBuilder.build(
        current_user,
        owner_user_id=item.owner_user_id,
        status=item.status,
        can_manage_in_scope=can_manage,
        can_update_status_in_scope=can_update_status,
        can_change_owner_in_scope=can_change_owner,
        can_create_offer=(
            item.status == "open"
            and RequestPolicy.can_create_manual_offer(
                current_user,
                request_owner_user_id=item.owner_user_id,
            )
            and can_manage
        ),
        deleted_alert_count=item.count_deleted_alert,
    )
    offer_schemas: list[OfferItemSchema] = []
    has_department_offer_update_scope = await _has_department_offer_update_scope(
        uow=uow,
        current_user=current_user,
        request_owner_user_id=item.owner_user_id,
    )
    for offer in item.offers:
        can_accept_in_scope = await _can_update_offer_status_in_scope(
            uow=uow,
            current_user=current_user,
            request_owner_user_id=item.owner_user_id,
            offer_owner_user_id=offer.contractor_user_id,
            status="accepted",
        )
        can_reject_in_scope = await _can_update_offer_status_in_scope(
            uow=uow,
            current_user=current_user,
            request_owner_user_id=item.owner_user_id,
            offer_owner_user_id=offer.contractor_user_id,
            status="rejected",
        )
        offer_schemas.append(
            OfferItemSchema(
                offer_id=offer.offer_id,
                contractor_user_id=offer.contractor_user_id,
                status=offer.status,
                status_label=offer.status_label,
                offer_amount=offer.offer_amount,
                created_at=offer.created_at,
                updated_at=offer.updated_at,
                offer_workspace_url=offer.offer_workspace_url,
                contractor_full_name=offer.contractor_full_name,
                contractor_phone=offer.contractor_phone,
                contractor_mail=offer.contractor_mail,
                contractor_inn=offer.contractor_inn,
                contractor_company_name=offer.contractor_company_name,
                contractor_company_phone=offer.contractor_company_phone,
                contractor_company_mail=offer.contractor_company_mail,
                contractor_contact_phone=offer.contractor_contact_phone,
                contractor_contact_mail=offer.contractor_contact_mail,
                contractor_address=offer.contractor_address,
                contractor_note=offer.contractor_note,
                files=[_request_file_schema(file_item) for file_item in offer.files],
                unread_messages_count=offer.unread_messages_count,
                actions=OfferActionBuilder.build(
                    current_user,
                    offer_owner_user_id=offer.contractor_user_id,
                    request_owner_user_id=item.owner_user_id,
                    contractor_user_id=offer.contractor_user_id,
                    offer_status=offer.status,
                    can_manage_in_scope=can_manage_offer,
                    has_department_offer_update_scope=has_department_offer_update_scope,
                    can_accept_in_scope=can_accept_in_scope,
                    can_reject_in_scope=can_reject_in_scope,
                ),
            )
        )

    return RequestDetailsResponse(
        data=RequestDetailsResponseData(
            item=RequestDetailsSchema(
                request_id=_request_id_as_str(item.request_id),
                description=item.description,
                status=item.status,
                status_label=item.status_label,
                initial_amount=item.initial_amount if request_actions.can_view_amounts else None,
                final_amount=item.final_amount if request_actions.can_view_amounts else None,
                deadline_at=item.deadline_at,
                created_at=item.created_at,
                updated_at=item.updated_at,
                closed_at=item.closed_at,
                owner_user_id=item.owner_user_id,
                owner_full_name=item.owner_full_name,
                owner_phone=item.owner_phone,
                owner_mail=item.owner_mail,
                chosen_offer_id=item.chosen_offer_id,
                id_plan=item.id_plan,
                stats=_request_stats_schema(item),
                unread_messages_count=item.unread_messages_count,
                files=[_request_file_schema(file_item) for file_item in item.files],
                actions=request_actions,
                offers=offer_schemas,
            ),
        ),
    )


@router.post("/requests", response_model=RequestCreateResponse)
async def create_request(
    id: str = Form(...),
    deadline_at: datetime = Form(...),
    normative_file_id: int = Form(...),
    description: str | None = Form(default=None),
    initial_amount: float | None = Form(default=None),
    id_plan: int | None = Form(default=None),
    additional_emails: list[str] | None = Form(default=None),
    hidden_contractor_ids: list[str] | None = Form(default=None),
    files: list[UploadFile] = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> RequestCreateResponse:
    validator = FileService()
    file_inputs: list[RequestFileCreateInput] = []
    for file in files:
        prepared = await validator.prepare_upload(file)
        file_inputs.append(
            RequestFileCreateInput(
                original_name=prepared.original_name,
                content_bytes=prepared.content_bytes,
                mime_type=prepared.mime_type,
            )
        )

    request_file_service: FileService | None = None
    try:
        async with uow:
            request_file_service = FileService(uow.files)
            email_notifications = EmailNotificationService(uow.profiles, uow.requests, uow.files)
            service = _build_request_service(
                uow,
                email_notifications=email_notifications,
                file_service=request_file_service,
            )
            request_id, file_ids = await service.create_request(
                current_user=current_user,
                request_id=id,
                deadline_at=deadline_at,
                description=description,
                initial_amount=initial_amount,
                id_plan=id_plan,
                normative_file_id=normative_file_id,
                files=file_inputs,
                additional_emails=additional_emails,
                hidden_contractor_ids=hidden_contractor_ids,
            )
    except Exception:
        if request_file_service is not None:
            await request_file_service.cleanup_tracked_objects()
        raise

    return RequestCreateResponse(
        data={"request_id": _request_id_as_str(request_id), "file_ids": file_ids},
    )


@router.patch("/requests/{request_id}", response_model=RequestMutationResponse)
async def update_request(
    payload: RequestEditPayload = Body(...),
    request_id: str = PathParam(..., min_length=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> RequestMutationResponse:
    async with uow:
        service = _build_request_service(uow)
        await service.update_request(
            current_user=current_user,
            request_id=request_id,
            data=RequestEditInput(
                status=payload.status,
                deadline_at=payload.deadline_at,
                owner_user_id=payload.owner_user_id,
                initial_amount=payload.initial_amount,
                final_amount=payload.final_amount,
                id_plan=payload.id_plan,
                id_plan_provided=("id_plan" in payload.model_fields_set),
            ),
        )

    return RequestMutationResponse(
        data={"request_id": _request_id_as_str(request_id)},
    )


@router.post("/requests/{request_id}/email-notifications", response_model=RequestEmailNotificationResponse)
async def send_request_email_notifications(
    payload: RequestEmailNotificationPayload = Body(...),
    request_id: str = PathParam(..., min_length=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> RequestEmailNotificationResponse:
    async with uow:
        email_notifications = EmailNotificationService(
            uow.profiles,
            uow.requests,
            uow.files,
            after_commit_hook_registrar=getattr(uow, "add_after_commit_hook", None),
        )
        service = _build_request_service(
            uow,
            email_notifications=email_notifications,
        )
        result = await service.send_request_email_notification(
            current_user=current_user,
            request_id=request_id,
            additional_emails=payload.additional_emails,
        )

    return RequestEmailNotificationResponse(
        data={"request_id": _request_id_as_str(result.request_id), "sent_to": result.sent_to},
    )


@router.post("/requests/{request_id}/files", response_model=RequestFileMutationResponse)
async def add_request_file(
    request_id: str = PathParam(..., min_length=1),
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> RequestFileMutationResponse:
    prepared = await FileService().prepare_upload(file)

    request_file_service: FileService | None = None
    try:
        async with uow:
            request_file_service = FileService(uow.files)
            service = _build_request_service(
                uow,
                file_service=request_file_service,
            )
            file_id = await service.attach_file(
                current_user=current_user,
                request_id=request_id,
                file_data=RequestFileCreateInput(
                    original_name=prepared.original_name,
                    content_bytes=prepared.content_bytes,
                    mime_type=prepared.mime_type,
                ),
            )
    except Exception:
        if request_file_service is not None:
            await request_file_service.cleanup_tracked_objects()
        raise

    return RequestFileMutationResponse(
        data={"request_id": _request_id_as_str(request_id), "file_id": file_id},
    )


@router.delete("/requests/{request_id}/files/{file_id}", response_model=RequestFileMutationResponse)
async def delete_request_file(
    request_id: str = PathParam(..., min_length=1),
    file_id: int = PathParam(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> RequestFileMutationResponse:
    async with uow:
        service = _build_request_service(uow)
        await service.remove_file(
            current_user=current_user,
            request_id=request_id,
            file_id=file_id,
        )

    return RequestFileMutationResponse(
        data={"request_id": _request_id_as_str(request_id), "file_id": file_id},
    )


@router.patch("/requests/deleted-alerts/viewed", response_model=DeletedAlertViewedResponse)
async def mark_deleted_alert_viewed(
    payload: DeletedAlertViewed = Body(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> DeletedAlertViewedResponse:
    async with uow:
        service = _build_request_service(uow)
        updated_stats = await service.mark_deleted_alert_viewed(
            current_user=current_user,
            request_id=payload.request_id,
        )

    return DeletedAlertViewedResponse(
        data={
            "status": "ok",
            "request_offer_stats": RequestOfferStatsSchema(
                request_id=_request_id_as_str(updated_stats.request_id),
                count_deleted_alert=updated_stats.count_deleted_alert,
                updated_at=updated_stats.updated_at,
            ),
        },
    )


def _build_content_disposition(filename: str) -> str:
    quoted = quote(Path(filename).name, safe="")
    return f"attachment; filename*=UTF-8''{quoted}"


@router.get("/files/{file_id}/download")
@router.get("/files/{file_id}/download/", include_in_schema=False)
async def download_file(
    file_id: int = PathParam(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> StreamingResponse:
    if not has_permission(current_user, PermissionCodes.FILES_DOWNLOAD):
        raise Forbidden("Insufficient permissions for file download")

    async with uow:
        db_file = await uow.files.get_by_id(file_id)
        if db_file is None:
            raise NotFound("File not found")

        is_normative_file = await uow.files.is_normative_file(file_id=file_id)
        if is_normative_file:
            UserPolicy.ensure_can_view_normative_files(current_user)
        elif current_user.role_id == settings.contractor_role_id:
            linked_to_open_request = await uow.requests.is_file_linked_to_visible_open_request(
                contractor_user_id=current_user.user_id,
                file_id=file_id,
            )
            linked_to_own_offer = await uow.offers.is_file_linked_to_contractor(
                contractor_user_id=current_user.user_id,
                file_id=file_id,
            )
            linked_to_own_message = await uow.offers.is_message_file_linked_to_contractor(
                contractor_user_id=current_user.user_id,
                file_id=file_id,
            )
            if not linked_to_open_request and not linked_to_own_offer and not linked_to_own_message:
                raise Forbidden("Insufficient permissions for file download")
        else:
            request_owner_user_id = await uow.requests.get_request_owner_id_by_request_file_id(file_id=file_id)
            offer_owner_user_id = await uow.offers.get_request_owner_id_by_offer_file_id(file_id=file_id)
            message_owner_user_id = await uow.offers.get_request_owner_id_by_message_file_id(file_id=file_id)
            if all(owner_id is None for owner_id in (request_owner_user_id, offer_owner_user_id, message_owner_user_id)):
                raise Forbidden("Insufficient permissions for file download")

            is_allowed = False
            standard_scope_owner_ids: set[str] | None = None
            if (
                has_permission(current_user, PermissionCodes.REQUESTS_READ)
                or has_permission(current_user, PermissionCodes.OFFERS_WORKSPACE_READ)
                or has_permission(current_user, PermissionCodes.CHAT_READ)
            ):
                standard_scope_owner_ids = await _resolve_standard_owner_scope_ids_for_current_user(
                    uow=uow,
                    current_user=current_user,
                )

            def _owner_in_standard_scope(owner_user_id: str) -> bool:
                if standard_scope_owner_ids is None:
                    return True
                return owner_user_id in standard_scope_owner_ids

            if (
                request_owner_user_id is not None
                and has_permission(current_user, PermissionCodes.REQUESTS_READ)
                and _owner_in_standard_scope(request_owner_user_id)
            ):
                is_allowed = True
            if (
                not is_allowed
                and offer_owner_user_id is not None
                and has_permission(current_user, PermissionCodes.OFFERS_WORKSPACE_READ)
                and _owner_in_standard_scope(offer_owner_user_id)
            ):
                is_allowed = True
            if (
                not is_allowed
                and message_owner_user_id is not None
                and has_permission(current_user, PermissionCodes.CHAT_READ)
                and _owner_in_standard_scope(message_owner_user_id)
            ):
                is_allowed = True

            if not is_allowed:
                department_scope_owner_ids = await _resolve_department_owner_scope_ids_for_current_user(
                    uow=uow,
                    current_user=current_user,
                )
                if request_owner_user_id is not None and has_permission(
                    current_user,
                    PermissionCodes.DEPARTMENT_REQUESTS_READ,
                ):
                    is_allowed = request_owner_user_id in department_scope_owner_ids
                if (
                    not is_allowed
                    and message_owner_user_id is not None
                    and has_permission(current_user, PermissionCodes.DEPARTMENT_CHATS_READ)
                ):
                    is_allowed = message_owner_user_id in department_scope_owner_ids

            if not is_allowed:
                raise Forbidden("Insufficient permissions for file download")

    file_service = FileService()
    content = await file_service.read_bytes(db_file=db_file)
    media_type = db_file.mime_type or "application/octet-stream"
    headers = {
        "Content-Disposition": _build_content_disposition(db_file.original_name),
        "Content-Length": str(len(content)),
    }
    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers=headers,
    )


async def _resolve_department_owner_scope_ids_for_current_user(
    *,
    uow: UnitOfWork,
    current_user: CurrentUser,
) -> set[str]:
    if current_user.role_id not in {
        settings.project_manager_role_id,
        settings.lead_economist_role_id,
        settings.economist_role_id,
    }:
        return set()
    root_user_id = await _resolve_department_root_user_id(
        uow=uow,
        current_user=current_user,
    )
    if root_user_id is None:
        return set()
    return await _collect_hierarchy_user_ids(uow=uow, root_user_id=root_user_id)


async def _resolve_standard_owner_scope_ids_for_current_user(
    *,
    uow: UnitOfWork,
    current_user: CurrentUser,
) -> set[str] | None:
    if current_user.role_id == settings.superadmin_role_id:
        return None
    if current_user.role_id in {
        settings.project_manager_role_id,
        settings.lead_economist_role_id,
        settings.economist_role_id,
    }:
        users = getattr(uow, "users", None)
        if users is not None and callable(getattr(users, "get_by_id", None)):
            department_owner_ids = await DepartmentScopeService(users).resolve_department_owner_ids_for_current_user(
                current_user=current_user,
            )
            if department_owner_ids:
                return set(department_owner_ids)

        if current_user.role_id in {
            settings.project_manager_role_id,
            settings.lead_economist_role_id,
        }:
            return await _collect_hierarchy_user_ids(uow=uow, root_user_id=current_user.user_id)
        lead_root_user_id = await _resolve_lead_economist_scope_root_user_id(
            uow=uow,
            current_user_id=current_user.user_id,
        )
        visible = await _collect_hierarchy_user_ids(uow=uow, root_user_id=lead_root_user_id)
        return visible | {current_user.user_id}
    return set()


async def _resolve_lead_economist_scope_root_user_id(
    *,
    uow: UnitOfWork,
    current_user_id: str,
) -> str:
    cursor_id: str | None = current_user_id
    visited: set[str] = set()
    while cursor_id is not None and cursor_id not in visited:
        visited.add(cursor_id)
        cursor_user = await uow.users.get_by_id(cursor_id)
        if cursor_user is None:
            break
        if cursor_user.id_role == settings.lead_economist_role_id:
            return cursor_user.id
        cursor_id = cursor_user.id_parent
    return current_user_id


async def _resolve_department_root_user_id(
    *,
    uow: UnitOfWork,
    current_user: CurrentUser,
) -> str | None:
    if current_user.role_id == settings.project_manager_role_id:
        return current_user.user_id
    cursor_id: str | None = current_user.user_id
    visited: set[str] = set()
    while cursor_id is not None and cursor_id not in visited:
        visited.add(cursor_id)
        cursor_user = await uow.users.get_by_id(cursor_id)
        if cursor_user is None:
            return None
        if cursor_user.id_role == settings.project_manager_role_id:
            return cursor_user.id
        cursor_id = cursor_user.id_parent
    return None


async def _collect_hierarchy_user_ids(*, uow: UnitOfWork, root_user_id: str) -> set[str]:
    rows = await uow.users.list_active_user_parent_pairs()
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
    return visible
