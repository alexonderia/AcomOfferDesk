from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Body, Depends, File, Form, Path as PathParam, UploadFile
from fastapi.responses import StreamingResponse

from app.api.action_flags import OfferActionBuilder, RequestActionBuilder, serialize_permissions
from app.api.dependencies import get_current_user, get_uow
from app.core.config import settings
from app.core.uow import UnitOfWork
from app.domain.authorization import has_permission
from app.domain.exceptions import Forbidden, NotFound
from app.domain.permissions import PermissionCodes
from app.domain.policies import CurrentUser, RequestPolicy
from app.schemas.links import Link, LinkSet
from app.schemas.requests import (
    DeletedAlertViewed,
    DeletedAlertViewedResponse,
    OfferItemSchema,
    OfferedRequestOfferSchema,
    OpenRequestItemSchema,
    OpenRequestListData,
    OpenRequestListResponse,
    RequestCreateResponse,
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
from app.services.requests import RequestEditInput, RequestFileCreateInput, RequestService

router = APIRouter()


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


def _request_item_schema(current_user: CurrentUser, item) -> RequestItemSchema:
    return RequestItemSchema(
        request_id=item.request_id,
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
            deleted_alert_count=item.count_deleted_alert,
        ),
    )


def _open_request_item_schema(current_user: CurrentUser, item) -> OpenRequestItemSchema:
    can_create_offer = (
        current_user.role_id == settings.contractor_role_id
        and item.status == "open"
        and item.latest_offer_status in {None, "deleted"}
    )
    return OpenRequestItemSchema(
        request_id=item.request_id,
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
                ),
            )
            for offer in item.offers
        ],
        actions=RequestActionBuilder.build(
            current_user,
            owner_user_id=item.owner_user_id,
            status=item.status,
            can_create_offer=can_create_offer,
        ),
    )


@router.get("/requests", response_model=RequestListResponse)
@router.get("/requests/", response_model=RequestListResponse, include_in_schema=False)
async def list_requests(
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> RequestListResponse:
    async with uow:
        service = RequestService(uow.requests, uow.files, uow.users, uow.offers, uow.user_status_periods)
        items = await service.list_requests(current_user=current_user)

    return RequestListResponse(
        data=RequestListData(
            items=[_request_item_schema(current_user, item) for item in items],
            permissions=serialize_permissions(current_user),
        ),
        _links=LinkSet(
            self=Link(href="/api/v1/requests", method="GET"),
        ),
    )


@router.get("/requests/open", response_model=OpenRequestListResponse)
@router.get("/requests/open/", response_model=OpenRequestListResponse, include_in_schema=False)
async def list_open_requests(
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OpenRequestListResponse:
    async with uow:
        service = RequestService(uow.requests, uow.files, uow.users, uow.offers, uow.user_status_periods)
        if current_user.role_id == settings.contractor_role_id:
            items = await service.list_open_requests_for_contractor(current_user=current_user)
        else:
            items = await service.list_open_requests(current_user=current_user)

    return OpenRequestListResponse(
        data=OpenRequestListData(
            items=[_open_request_item_schema(current_user, item) for item in items],
            permissions=serialize_permissions(current_user),
        ),
        _links=LinkSet(
            self=Link(href="/api/v1/requests/open", method="GET"),
        ),
    )


@router.get("/requests/offered", response_model=OpenRequestListResponse)
@router.get("/requests/offered/", response_model=OpenRequestListResponse, include_in_schema=False)
async def list_offered_requests(
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OpenRequestListResponse:
    async with uow:
        service = RequestService(uow.requests, uow.files, uow.users, uow.offers, uow.user_status_periods)
        items = await service.list_offered_requests_for_contractor(current_user=current_user)

    return OpenRequestListResponse(
        data=OpenRequestListData(
            items=[_open_request_item_schema(current_user, item) for item in items],
            permissions=serialize_permissions(current_user),
        ),
        _links=LinkSet(
            self=Link(href="/api/v1/requests/offered", method="GET"),
        ),
    )


@router.get("/requests/{request_id}", response_model=RequestDetailsResponse)
@router.get("/requests/{request_id}/", response_model=RequestDetailsResponse, include_in_schema=False)
async def get_request_details(
    request_id: int = PathParam(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> RequestDetailsResponse:
    async with uow:
        service = RequestService(uow.requests, uow.files, uow.users, uow.offers, uow.user_status_periods)
        item = await service.get_request_details(current_user=current_user, request_id=request_id)
    request_actions = RequestActionBuilder.build(
        current_user,
        owner_user_id=item.owner_user_id,
        status=item.status,
        can_create_offer=(
            item.status == "open"
            and RequestPolicy.can_create_manual_offer(
                current_user,
                request_owner_user_id=item.owner_user_id,
            )
        ),
        deleted_alert_count=item.count_deleted_alert,
    )

    return RequestDetailsResponse(
        data=RequestDetailsResponseData(
            item=RequestDetailsSchema(
                request_id=item.request_id,
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
                chosen_offer_id=item.chosen_offer_id,
                id_plan=item.id_plan,
                stats=_request_stats_schema(item),
                unread_messages_count=item.unread_messages_count,
                files=[_request_file_schema(file_item) for file_item in item.files],
                actions=request_actions,
                offers=[
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
                        ),
                    )
                    for offer in item.offers
                ],
            ),
            permissions=serialize_permissions(current_user),
        ),
        _links=LinkSet(
            self=Link(href=f"/api/v1/requests/{request_id}", method="GET"),
        ),
    )


@router.post("/requests", response_model=RequestCreateResponse)
async def create_request(
    deadline_at: datetime = Form(...),
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
            email_notifications = EmailNotificationService(uow.profiles, uow.requests)
            service = RequestService(
                uow.requests,
                uow.files,
                uow.users,
                uow.offers,
                uow.user_status_periods,
                email_notifications=email_notifications,
                file_service=request_file_service,
            )
            request_id, file_ids = await service.create_request(
                current_user=current_user,
                deadline_at=deadline_at,
                description=description,
                initial_amount=initial_amount,
                id_plan=id_plan,
                files=file_inputs,
                additional_emails=additional_emails,
                hidden_contractor_ids=hidden_contractor_ids,
            )
    except Exception:
        if request_file_service is not None:
            await request_file_service.cleanup_tracked_objects()
        raise

    return RequestCreateResponse(
        data={"request_id": request_id, "file_ids": file_ids},
        _links=LinkSet(
            self=Link(href=f"/api/v1/requests/{request_id}", method="GET"),
        ),
    )


@router.patch("/requests/{request_id}", response_model=RequestMutationResponse)
async def update_request(
    payload: RequestEditPayload = Body(...),
    request_id: int = PathParam(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> RequestMutationResponse:
    async with uow:
        service = RequestService(uow.requests, uow.files, uow.users, uow.offers, uow.user_status_periods)
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
        data={"request_id": request_id},
        _links=LinkSet(
            self=Link(href=f"/api/v1/requests/{request_id}", method="GET"),
        ),
    )


@router.post("/requests/{request_id}/email-notifications", response_model=RequestEmailNotificationResponse)
async def send_request_email_notifications(
    payload: RequestEmailNotificationPayload = Body(...),
    request_id: int = PathParam(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> RequestEmailNotificationResponse:
    async with uow:
        email_notifications = EmailNotificationService(uow.profiles, uow.requests)
        service = RequestService(
            uow.requests,
            uow.files,
            uow.users,
            uow.offers,
            uow.user_status_periods,
            email_notifications=email_notifications,
        )
        result = await service.send_request_email_notification(
            current_user=current_user,
            request_id=request_id,
            additional_emails=payload.additional_emails,
        )

    return RequestEmailNotificationResponse(
        data={"request_id": result.request_id, "sent_to": result.sent_to},
        _links=LinkSet(
            self=Link(href=f"/api/v1/requests/{request_id}/email-notifications", method="POST"),
        ),
    )


@router.post("/requests/{request_id}/files", response_model=RequestFileMutationResponse)
async def add_request_file(
    request_id: int = PathParam(..., ge=1),
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> RequestFileMutationResponse:
    prepared = await FileService().prepare_upload(file)

    request_file_service: FileService | None = None
    try:
        async with uow:
            request_file_service = FileService(uow.files)
            service = RequestService(
                uow.requests,
                uow.files,
                uow.users,
                uow.offers,
                uow.user_status_periods,
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
        data={"request_id": request_id, "file_id": file_id},
        _links=LinkSet(
            self=Link(href=f"/api/v1/requests/{request_id}/files", method="POST"),
        ),
    )


@router.delete("/requests/{request_id}/files/{file_id}", response_model=RequestFileMutationResponse)
async def delete_request_file(
    request_id: int = PathParam(..., ge=1),
    file_id: int = PathParam(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> RequestFileMutationResponse:
    async with uow:
        service = RequestService(uow.requests, uow.files, uow.users, uow.offers, uow.user_status_periods)
        await service.remove_file(
            current_user=current_user,
            request_id=request_id,
            file_id=file_id,
        )

    return RequestFileMutationResponse(
        data={"request_id": request_id, "file_id": file_id},
        _links=LinkSet(
            self=Link(href=f"/api/v1/requests/{request_id}/files/{file_id}", method="DELETE"),
        ),
    )


@router.patch("/requests/deleted-alerts/viewed", response_model=DeletedAlertViewedResponse)
async def mark_deleted_alert_viewed(
    payload: DeletedAlertViewed = Body(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> DeletedAlertViewedResponse:
    async with uow:
        service = RequestService(uow.requests, uow.files, uow.users, uow.offers, uow.user_status_periods)
        updated_stats = await service.mark_deleted_alert_viewed(
            current_user=current_user,
            request_id=payload.request_id,
        )

    return DeletedAlertViewedResponse(
        data={
            "status": "ok",
            "request_offer_stats": RequestOfferStatsSchema(
                request_id=updated_stats.request_id,
                count_deleted_alert=updated_stats.count_deleted_alert,
                updated_at=updated_stats.updated_at,
            ),
        },
        _links=LinkSet(
            self=Link(href="/api/v1/requests/deleted-alerts/viewed", method="PATCH"),
        ),
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

    can_download_without_scope_check = has_permission(current_user, PermissionCodes.REQUESTS_READ)

    async with uow:
        db_file = await uow.files.get_by_id(file_id)
        if db_file is None:
            raise NotFound("File not found")

        if not can_download_without_scope_check:
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
