from __future__ import annotations

from fastapi import APIRouter, Body, Depends, File, Form, Path as PathParam, Query, UploadFile
from pydantic import ValidationError

from app.api.action_flags import OfferActionBuilder, OfferActionResolver, RequestActionBuilder
from app.api.dependencies import get_current_user, get_uow
from app.core.uow import UnitOfWork
from app.domain.exceptions import Conflict
from app.domain.policies import CurrentUser
from app.realtime.contracts import OutboundEnvelope
from app.realtime.runtime import get_chat_runtime
from app.schemas.links import Link, LinkSet
from app.schemas.offers import (
    ContractorInfoResponse,
    ContractorRequestViewResponse,
    ManualOfferCreateResponse,
    ManualContractorCreatePayload,
    OfferCreatePayload,
    OfferCreateResponse,
    OfferEditPayload,
    OfferEditResponse,
    OfferFileMutationResponse,
    OfferMessageCreatePayload,
    OfferMessageCreateResponse,
    OfferMessageFileUploadResponse,
    OfferMessageListData,
    OfferMessageListResponse,
    OfferMessageReadBySchema,
    OfferMessageSchema,
    OfferMessageStatusUpdatePayload,
    OfferMessageStatusUpdateResponse,
    OfferStatusMutationResponse,
    OfferStatusUpdatePayload,
    OfferWorkspaceResponse,
)
from app.schemas.requests import RequestFileSchema
from app.services.chat_realtime import ChatRealtimeService, build_offer_service
from app.services.files import FileService
from app.services.offers import AttachmentFileInput, ManualContractorCreateInput

router = APIRouter()

_MAX_ATTACHMENTS_PER_MESSAGE = 5
_MAX_TOTAL_ATTACHMENT_SIZE_BYTES = 25 * 1024 * 1024


def _request_file_schema(file_item) -> RequestFileSchema:
    return RequestFileSchema(
        id=file_item.id,
        path=file_item.path,
        name=file_item.name,
        download_url=f"/api/v1/files/{file_item.id}/download",
    )


def _offer_action_resolver(uow: UnitOfWork) -> OfferActionResolver:
    return OfferActionResolver(
        offers=uow.offers,
        requests=uow.requests,
        chats=uow.chats,
        users=uow.users,
    )


@router.get("/offers", response_model=ContractorInfoResponse)
async def get_contractor_info(
    id_user: str = Query(..., min_length=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ContractorInfoResponse:
    async with uow:
        service = build_offer_service(uow)
        contractor = await service.get_contractor_info(current_user=current_user, contractor_user_id=id_user)

    return ContractorInfoResponse(
        data={
            "user_id": contractor.user_id,
            "full_name": contractor.full_name,
            "phone": contractor.phone,
            "mail": contractor.mail,
            "company_name": contractor.company_name,
            "inn": contractor.inn,
            "company_phone": contractor.company_phone,
            "company_mail": contractor.company_mail,
            "address": contractor.address,
            "note": contractor.note,
        },
        _links=LinkSet(
            self=Link(href=f"/api/v1/offers?id_user={contractor.user_id}", method="GET"),
        ),
    )


@router.get("/requests/{request_id}/contractor-view", response_model=ContractorRequestViewResponse)
async def get_contractor_request_view(
    request_id: int = PathParam(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ContractorRequestViewResponse:
    async with uow:
        service = build_offer_service(uow)
        item = await service.get_request_view(current_user=current_user, request_id=request_id)

    can_create_offer = item.status == "open" and item.existing_offer is None
    return ContractorRequestViewResponse(
        data={
            "request_id": item.request_id,
            "description": item.description,
            "status": item.status,
            "status_label": item.status_label,
            "deadline_at": item.deadline_at,
            "owner_user_id": item.owner_user_id,
            "owner_full_name": item.owner_full_name,
            "files": [_request_file_schema(file_item) for file_item in item.files],
            "existing_offer": (
                {
                    "offer_id": item.existing_offer.offer_id,
                    "status": item.existing_offer.status,
                    "status_label": item.existing_offer.status_label,
                    "files": [_request_file_schema(file_item) for file_item in item.existing_offer.files],
                    "actions": OfferActionBuilder.build(
                        current_user,
                        offer_owner_user_id=current_user.user_id,
                        request_owner_user_id=item.owner_user_id,
                        contractor_user_id=current_user.user_id,
                        offer_status=item.existing_offer.status,
                    ),
                }
                if item.existing_offer is not None
                else None
            ),
            "actions": RequestActionBuilder.build(
                current_user,
                owner_user_id=item.owner_user_id,
                status=item.status,
                can_create_offer=can_create_offer,
            ),
        },
        _links=LinkSet(
            self=Link(href=f"/api/v1/requests/{request_id}/contractor-view", method="GET"),
        ),
    )


@router.post("/requests/{request_id}/offers", response_model=OfferCreateResponse)
async def create_empty_offer(
    request_id: int = PathParam(..., ge=1),
    payload: OfferCreatePayload | None = Body(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OfferCreateResponse:
    async with uow:
        service = build_offer_service(uow)
        offer_id = await service.create_offer(
            current_user=current_user,
            request_id=request_id,
            offer_amount=(payload.offer_amount if payload is not None else None),
        )

    return OfferCreateResponse(
        data={"offer_id": offer_id, "request_id": request_id},
        _links=LinkSet(
            self=Link(href=f"/api/v1/offers/{offer_id}/workspace", method="GET"),
        ),
    )


@router.post("/requests/{request_id}/offers/manual", response_model=ManualOfferCreateResponse)
async def create_manual_offer(
    request_id: int = PathParam(..., ge=1),
    contractor_mode: str = Form(...),
    contractor_user_id: str | None = Form(default=None),
    company_name: str | None = Form(default=None),
    inn: str | None = Form(default=None),
    company_phone: str | None = Form(default=None),
    company_mail: str | None = Form(default=None),
    address: str | None = Form(default=None),
    note: str | None = Form(default=None),
    offer_amount: float | None = Form(default=None),
    files: list[UploadFile] = File(default_factory=list),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ManualOfferCreateResponse:
    normalized_mode = contractor_mode.strip().lower()
    if normalized_mode not in {"existing", "new"}:
        raise Conflict("Unsupported contractor mode")

    if normalized_mode == "existing":
        normalized_contractor_user_id = (contractor_user_id or "").strip()
        if not normalized_contractor_user_id:
            raise Conflict("Existing contractor is required")
        manual_contractor_data = None
    else:
        normalized_contractor_user_id = None
        try:
            validated_payload = ManualContractorCreatePayload(
                company_name=(company_name or ""),
                inn=(inn or ""),
                company_phone=(company_phone or ""),
                company_mail=company_mail,
                address=address,
                note=note,
            )
        except ValidationError as exc:
            error = exc.errors()[0] if exc.errors() else None
            message = error.get("msg") if isinstance(error, dict) else None
            raise Conflict(message or "Invalid manual contractor payload") from exc

        manual_contractor_data = ManualContractorCreateInput(
            company_name=validated_payload.company_name,
            inn=validated_payload.inn,
            company_phone=validated_payload.company_phone,
            company_mail=validated_payload.company_mail,
            address=validated_payload.address,
            note=validated_payload.note,
        )

    validator = FileService()
    prepared_uploads: list[AttachmentFileInput] = []
    for file in files:
        prepared = await validator.prepare_upload(file)
        prepared_uploads.append(
            AttachmentFileInput(
                original_name=prepared.original_name,
                content_bytes=prepared.content_bytes,
                mime_type=prepared.mime_type,
            )
        )

    offer_file_service: FileService | None = None
    try:
        async with uow:
            offer_file_service = FileService(uow.files)
            service = build_offer_service(uow, file_service=offer_file_service)
            result = await service.create_manual_offer(
                current_user=current_user,
                request_id=request_id,
                contractor_user_id=normalized_contractor_user_id,
                contractor_data=manual_contractor_data,
                offer_amount=offer_amount,
                files=prepared_uploads,
            )
    except Exception:
        if offer_file_service is not None:
            await offer_file_service.cleanup_tracked_objects()
        raise

    return ManualOfferCreateResponse(
        data={
            "offer_id": result.offer_id,
            "request_id": result.request_id,
            "contractor_user_id": result.contractor_user_id,
            "contractor_created": result.contractor_created,
        },
        _links=LinkSet(
            self=Link(href=f"/api/v1/offers/{result.offer_id}/workspace", method="GET"),
        ),
    )


@router.get("/offers/{offer_id}/workspace", response_model=OfferWorkspaceResponse)
async def get_offer_workspace(
    offer_id: int = PathParam(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OfferWorkspaceResponse:
    async with uow:
        service = build_offer_service(uow)
        item = await service.get_workspace(current_user=current_user, offer_id=offer_id)
        resolved = await _offer_action_resolver(uow).resolve_workspace_context(
            current_user=current_user,
            offer_id=offer_id,
        )
    request_actions = RequestActionBuilder.build(
        current_user,
        owner_user_id=item.request.owner_user_id,
        status=item.request.status,
        can_create_offer=resolved.can_create_new_offer,
    )

    return OfferWorkspaceResponse(
        data={
            "request": {
                "request_id": item.request.request_id,
                "description": item.request.description,
                "status": item.request.status,
                "status_label": item.request.status_label,
                "initial_amount": item.request.initial_amount if request_actions.can_view_amounts else None,
                "final_amount": item.request.final_amount if request_actions.can_view_amounts else None,
                "deadline_at": item.request.deadline_at,
                "owner_user_id": item.request.owner_user_id,
                "owner_full_name": item.request.owner_full_name,
                "created_at": item.request.created_at,
                "updated_at": item.request.updated_at,
                "closed_at": item.request.closed_at,
                "files": [_request_file_schema(file_item) for file_item in item.request.files],
                "actions": request_actions,
            },
            "offer": {
                "offer_id": item.offer.offer_id,
                "status": item.offer.status,
                "status_label": item.offer.status_label,
                "offer_amount": item.offer.offer_amount,
                "created_at": item.offer.created_at,
                "updated_at": item.offer.updated_at,
                "files": [_request_file_schema(file_item) for file_item in item.offer.files],
                "actions": resolved.offer_actions,
            },
            "offers": [
                {
                    "offer_id": request_offer.offer_id,
                    "status": request_offer.status,
                    "status_label": request_offer.status_label,
                    "offer_amount": request_offer.offer_amount,
                    "created_at": request_offer.created_at,
                    "updated_at": request_offer.updated_at,
                    "files": [_request_file_schema(file_item) for file_item in request_offer.files],
                    "actions": OfferActionBuilder.build(
                        current_user,
                        offer_owner_user_id=item.contractor.user_id,
                        request_owner_user_id=item.request.owner_user_id,
                        contractor_user_id=item.contractor.user_id,
                        offer_status=request_offer.status,
                        offer_is_manual=resolved.offer_is_manual,
                    ),
                }
                for request_offer in item.offers
            ],
            "contractor": {
                "user_id": item.contractor.user_id,
                "full_name": item.contractor.full_name,
                "phone": item.contractor.phone,
                "mail": item.contractor.mail,
                "company_name": item.contractor.company_name,
                "inn": item.contractor.inn,
                "company_phone": item.contractor.company_phone,
                "company_mail": item.contractor.company_mail,
                "address": item.contractor.address,
                "note": item.contractor.note,
            },
            "chat_actions": resolved.chat_actions,
        },
        _links=LinkSet(
            self=Link(href=f"/api/v1/offers/{offer_id}/workspace", method="GET"),
        ),
    )


@router.patch("/offers/{offer_id}/status", response_model=OfferStatusMutationResponse)
async def update_offer_status(
    payload: OfferStatusUpdatePayload = Body(...),
    offer_id: int = PathParam(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OfferStatusMutationResponse:
    async with uow:
        service = build_offer_service(uow)
        status = await service.update_status(current_user=current_user, offer_id=offer_id, status=payload.status)

    return OfferStatusMutationResponse(
        data={"offer_id": offer_id, "status": status},
        _links=LinkSet(
            self=Link(href=f"/api/v1/offers/{offer_id}/status", method="PATCH"),
        ),
    )


@router.patch("/offers/{offer_id}", response_model=OfferEditResponse)
async def update_offer(
    payload: OfferEditPayload = Body(...),
    offer_id: int = PathParam(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OfferEditResponse:
    async with uow:
        service = build_offer_service(uow)
        offer_amount = await service.update_amount(
            current_user=current_user,
            offer_id=offer_id,
            offer_amount=payload.offer_amount,
        )

    return OfferEditResponse(
        data={"offer_id": offer_id, "offer_amount": offer_amount},
        _links=LinkSet(
            self=Link(href=f"/api/v1/offers/{offer_id}", method="PATCH"),
        ),
    )


@router.post("/offers/{offer_id}/files", response_model=OfferFileMutationResponse)
async def add_offer_file(
    offer_id: int = PathParam(..., ge=1),
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OfferFileMutationResponse:
    prepared = await FileService().prepare_upload(file)

    offer_file_service: FileService | None = None
    try:
        async with uow:
            offer_file_service = FileService(uow.files)
            service = build_offer_service(uow, file_service=offer_file_service)
            file_id = await service.add_file(
                current_user=current_user,
                offer_id=offer_id,
                upload=AttachmentFileInput(
                    original_name=prepared.original_name,
                    content_bytes=prepared.content_bytes,
                    mime_type=prepared.mime_type,
                ),
            )
    except Exception:
        if offer_file_service is not None:
            await offer_file_service.cleanup_tracked_objects()
        raise

    return OfferFileMutationResponse(
        data={"offer_id": offer_id, "file_id": file_id},
        _links=LinkSet(
            self=Link(href=f"/api/v1/offers/{offer_id}/files", method="POST"),
        ),
    )


@router.delete("/offers/{offer_id}/files/{file_id}", response_model=OfferFileMutationResponse)
async def delete_offer_file(
    offer_id: int = PathParam(..., ge=1),
    file_id: int = PathParam(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OfferFileMutationResponse:
    async with uow:
        service = build_offer_service(uow)
        await service.remove_file(current_user=current_user, offer_id=offer_id, file_id=file_id)

    return OfferFileMutationResponse(
        data={"offer_id": offer_id, "file_id": file_id},
        _links=LinkSet(
            self=Link(href=f"/api/v1/offers/{offer_id}/files/{file_id}", method="DELETE"),
        ),
    )


@router.get("/offers/{offer_id}/messages", response_model=OfferMessageListResponse)
async def list_offer_messages(
    offer_id: int = PathParam(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OfferMessageListResponse:
    async with uow:
        service = build_offer_service(uow)
        items = await service.list_messages(current_user=current_user, offer_id=offer_id)
        resolved = await _offer_action_resolver(uow).resolve_workspace_context(
            current_user=current_user,
            offer_id=offer_id,
        )

    return OfferMessageListResponse(
        data=OfferMessageListData(
            offer_id=offer_id,
            items=[
                OfferMessageSchema(
                    id=item.id,
                    user_id=item.user_id,
                    user_full_name=item.user_full_name,
                    text=item.text,
                    type=item.type,
                    status=item.status,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                    read_by=[
                        OfferMessageReadBySchema(
                            user_id=reader.user_id,
                            user_full_name=reader.user_full_name,
                            read_at=reader.read_at,
                        )
                        for reader in item.read_by
                    ],
                    attachments=[_request_file_schema(file_item) for file_item in item.attachments],
                )
                for item in items
            ],
            actions=resolved.chat_actions,
        ),
        _links=LinkSet(
            self=Link(href=f"/api/v1/offers/{offer_id}/messages", method="GET"),
        ),
    )


@router.post("/offers/{offer_id}/messages", response_model=OfferMessageCreateResponse)
async def create_offer_message(
    payload: OfferMessageCreatePayload = Body(...),
    offer_id: int = PathParam(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OfferMessageCreateResponse:
    realtime_service = ChatRealtimeService()
    result, message_payload = await realtime_service.create_message(
        current_user=current_user,
        offer_id=offer_id,
        text=payload.text,
    )

    await get_chat_runtime().publish_chat_event(
        chat_id=result.chat_id,
        event=OutboundEnvelope(
            type="message.created",
            data=message_payload,
        ),
    )

    return OfferMessageCreateResponse(
        data={"offer_id": offer_id, "message_id": result.message_id},
        _links=LinkSet(
            self=Link(href=f"/api/v1/offers/{offer_id}/messages", method="POST"),
        ),
    )


@router.post("/offers/{offer_id}/messages/files", response_model=OfferMessageFileUploadResponse)
async def upload_offer_message_file(
    offer_id: int = PathParam(..., ge=1),
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OfferMessageFileUploadResponse:
    prepared = await FileService().prepare_upload(file)
    realtime_service = ChatRealtimeService()
    uploaded = await realtime_service.upload_message_file(
        current_user=current_user,
        offer_id=offer_id,
        upload=AttachmentFileInput(
            original_name=prepared.original_name,
            content_bytes=prepared.content_bytes,
            mime_type=prepared.mime_type,
        ),
    )

    return OfferMessageFileUploadResponse(
        data=uploaded,
        _links=LinkSet(
            self=Link(href=f"/api/v1/offers/{offer_id}/messages/files", method="POST"),
        ),
    )


@router.post("/offers/{offer_id}/messages/attachments", response_model=OfferMessageCreateResponse)
async def create_offer_message_with_attachments(
    offer_id: int = PathParam(..., ge=1),
    text: str = Form(...),
    files: list[UploadFile] = File(default_factory=list),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OfferMessageCreateResponse:
    if len(files) > _MAX_ATTACHMENTS_PER_MESSAGE:
        raise Conflict("Too many attachments")

    attachments: list[AttachmentFileInput] = []
    total_size = 0
    for file in files:
        prepared = await FileService().prepare_upload(file)
        total_size += len(prepared.content_bytes)
        if total_size > _MAX_TOTAL_ATTACHMENT_SIZE_BYTES:
            raise Conflict("Attachments total size exceeded")
        attachments.append(
            AttachmentFileInput(
                original_name=prepared.original_name,
                content_bytes=prepared.content_bytes,
                mime_type=prepared.mime_type,
            )
        )

    offer_file_service: FileService | None = None
    try:
        async with uow:
            offer_file_service = FileService(uow.files)
            service = build_offer_service(uow, file_service=offer_file_service)
            result = await service.create_message(
                current_user=current_user,
                offer_id=offer_id,
                text=text,
                attachments=attachments,
            )
    except Exception:
        if offer_file_service is not None:
            await offer_file_service.cleanup_tracked_objects()
        raise

    message_payload = await ChatRealtimeService().load_message_payload(
        offer_id=result.offer_id,
        message_id=result.message_id,
    )
    await get_chat_runtime().publish_chat_event(
        chat_id=result.chat_id,
        event=OutboundEnvelope(
            type="message.created",
            data=message_payload,
        ),
    )

    return OfferMessageCreateResponse(
        data={"offer_id": offer_id, "message_id": result.message_id},
        _links=LinkSet(
            self=Link(href=f"/api/v1/offers/{offer_id}/messages/attachments", method="POST"),
        ),
    )


@router.patch("/offers/{offer_id}/messages/received", response_model=OfferMessageStatusUpdateResponse)
async def mark_offer_messages_received(
    payload: OfferMessageStatusUpdatePayload = Body(...),
    offer_id: int = PathParam(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OfferMessageStatusUpdateResponse:
    async with uow:
        service = build_offer_service(uow)
        ack = await service.mark_messages_received(
            current_user=current_user,
            offer_id=offer_id,
            message_ids=payload.message_ids,
            up_to_message_id=payload.up_to_message_id,
        )

    if ack.updated_message_ids:
        await get_chat_runtime().publish_chat_event(
            chat_id=ack.chat_id,
            event=OutboundEnvelope(
                type="message.delivered",
                data={
                    "chat_id": ack.chat_id,
                    "user_id": current_user.user_id,
                    "message_ids": ack.updated_message_ids,
                },
            ),
        )

    return OfferMessageStatusUpdateResponse(
        data={"offer_id": offer_id, "updated_count": ack.updated_count},
        _links=LinkSet(
            self=Link(href=f"/api/v1/offers/{offer_id}/messages/received", method="PATCH"),
        ),
    )


@router.patch("/offers/{offer_id}/messages/read", response_model=OfferMessageStatusUpdateResponse)
async def mark_offer_messages_read(
    payload: OfferMessageStatusUpdatePayload = Body(...),
    offer_id: int = PathParam(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OfferMessageStatusUpdateResponse:
    async with uow:
        service = build_offer_service(uow)
        ack = await service.mark_messages_read(
            current_user=current_user,
            offer_id=offer_id,
            message_ids=payload.message_ids,
            up_to_message_id=payload.up_to_message_id,
        )
        profile_full_name = None
        if uow.profiles is not None:
            profile_item = await uow.profiles.get_by_id(current_user.user_id)
            profile_full_name = profile_item.full_name if profile_item is not None else None

    if ack.updated_message_ids:
        await get_chat_runtime().publish_chat_event(
            chat_id=ack.chat_id,
            event=OutboundEnvelope(
                type="message.read",
                data={
                    "chat_id": ack.chat_id,
                    "user_id": current_user.user_id,
                    "user_full_name": profile_full_name,
                    "message_ids": ack.updated_message_ids,
                    "last_read_message_id": ack.last_read_message_id,
                },
            ),
        )

    return OfferMessageStatusUpdateResponse(
        data={"offer_id": offer_id, "updated_count": ack.updated_count},
        _links=LinkSet(
            self=Link(href=f"/api/v1/offers/{offer_id}/messages/read", method="PATCH"),
        ),
    )
