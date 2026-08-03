from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Body, Depends, Path, Query

from app.api.action_flags import ContractorActionBuilder
from app.api.dependencies import get_current_user, get_uow
from app.core.uow import UnitOfWork
from app.domain.policies import CurrentUser
from app.schemas.contractors import (
    ContractorInviteData,
    ContractorInviteRequest,
    ContractorInviteResponse,
    ContractorListData,
    ContractorListItemSchema,
    ContractorListResponse,
    ContractorProfileData,
    ContractorProfileResponse,
    ContractorRootUnitBindingItemSchema,
    ContractorRootUnitBindingsData,
    ContractorRootUnitBindingsResponse,
    ContractorRootUnitBindingsUpdateRequest,
    ContractorStatusUpdateData,
    ContractorStatusUpdateRequest,
    ContractorStatusUpdateResponse,
)
from app.services.contractor_invitations import ContractorInvitationService
from app.services.contractors import ContractorService
from app.services.normative_email_attachment import NormativeEmailAttachmentService
from app.services.users import UserStatusService

router = APIRouter()

USER_STATUS_RU = {
    "active": "Активен",
    "inactive": "Неактивен",
    "review": "На проверке",
    "blacklist": "В черном списке",
}


def _ru_user_status(status: str) -> str:
    return USER_STATUS_RU.get(status, status)


def _contractor_list_item(current_user: CurrentUser, item) -> ContractorListItemSchema:
    data = asdict(item)
    data["status"] = _ru_user_status(data["status"])
    is_manual = data.pop("is_manual")
    data["actions"] = ContractorActionBuilder.build_contractor_actions(
        current_user,
        is_manual=is_manual,
    )
    return ContractorListItemSchema(**data)


def _contractor_profile_data(current_user: CurrentUser, item) -> ContractorProfileData:
    data = asdict(item)
    data["status"] = _ru_user_status(data["status"])
    data["actions"] = ContractorActionBuilder.build_contractor_actions(current_user)
    return ContractorProfileData(**data)


def _contractor_root_unit_bindings_data(item) -> ContractorRootUnitBindingsData:
    return ContractorRootUnitBindingsData(
        contractor_user_id=item.contractor_user_id,
        can_manage=item.can_manage,
        items=[
            ContractorRootUnitBindingItemSchema(
                unit_id=binding.unit_id,
                unit_name=binding.unit_name,
                is_bound=binding.is_bound,
                can_manage=binding.can_manage,
            )
            for binding in item.items
        ],
    )


@router.get("/contractors", response_model=ContractorListResponse)
@router.get("/contractors/", response_model=ContractorListResponse, include_in_schema=False)
async def list_contractors(
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ContractorListResponse:
    status_label_to_code = {value.lower(): key for key, value in USER_STATUS_RU.items()}
    normalized_status = (status or "").strip().lower() or None
    if normalized_status is not None:
        normalized_status = status_label_to_code.get(normalized_status, normalized_status)
    async with uow:
        service = ContractorService(uow.users, uow.profiles, uow.units)
        result = await service.list_contractors(
            current_user=current_user,
            search=search,
            status=normalized_status,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )

    return ContractorListResponse(
        data=ContractorListData(
            items=[_contractor_list_item(current_user, item) for item in result.items],
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        ),
    )


@router.get("/contractors/{contractor_id}", response_model=ContractorProfileResponse)
async def get_contractor(
    contractor_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ContractorProfileResponse:
    async with uow:
        service = ContractorService(uow.users, uow.profiles, uow.units)
        profile = await service.get_contractor(
            current_user=current_user,
            contractor_id=contractor_id,
        )

    return ContractorProfileResponse(
        data=_contractor_profile_data(current_user, profile),
    )


@router.patch("/contractors/{contractor_id}/status", response_model=ContractorStatusUpdateResponse)
async def update_contractor_status(
    payload: ContractorStatusUpdateRequest,
    contractor_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ContractorStatusUpdateResponse:
    async with uow:
        contractor_service = ContractorService(uow.users, uow.profiles, uow.units)
        status_service = UserStatusService(
            uow.users,
            uow.profiles,
            uow.user_auth_accounts,
            after_commit_hook_registrar=getattr(uow, "add_after_commit_hook", None),
        )
        result = await contractor_service.update_contractor_status(
            current_user=current_user,
            contractor_id=contractor_id,
            user_status=payload.user_status,
            status_service=status_service,
        )

    return ContractorStatusUpdateResponse(
        data=ContractorStatusUpdateData(
            user_id=result.user_id,
            user_status=_ru_user_status(result.user_status),
        ),
    )


@router.get("/contractors/{contractor_id}/root-units", response_model=ContractorRootUnitBindingsResponse)
async def get_contractor_root_units(
    contractor_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ContractorRootUnitBindingsResponse:
    async with uow:
        service = ContractorService(uow.users, uow.profiles, uow.units)
        result = await service.get_contractor_root_unit_bindings(
            current_user=current_user,
            contractor_id=contractor_id,
        )

    return ContractorRootUnitBindingsResponse(
        data=_contractor_root_unit_bindings_data(result),
    )


@router.put("/contractors/{contractor_id}/root-units", response_model=ContractorRootUnitBindingsResponse)
async def update_contractor_root_units(
    payload: ContractorRootUnitBindingsUpdateRequest,
    contractor_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ContractorRootUnitBindingsResponse:
    async with uow:
        service = ContractorService(uow.users, uow.profiles, uow.units)
        result = await service.update_contractor_root_unit_bindings(
            current_user=current_user,
            contractor_id=contractor_id,
            root_unit_ids={int(unit_id) for unit_id in payload.root_unit_ids},
        )

    return ContractorRootUnitBindingsResponse(
        data=_contractor_root_unit_bindings_data(result),
    )


@router.post("/contractors/invite", response_model=ContractorInviteResponse)
async def invite_contractors(
    payload: ContractorInviteRequest = Body(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ContractorInviteResponse:
    async with uow:
        service = ContractorInvitationService(
            attachment_service=NormativeEmailAttachmentService(uow.files),
            after_commit_hook_registrar=getattr(uow, "add_after_commit_hook", None),
        )
        result = await service.invite_contractors(
            current_user=current_user,
            emails=payload.emails,
            normative_file_id=payload.normative_file_id,
        )

    return ContractorInviteResponse(
        data=ContractorInviteData(
            sent=result.sent,
            failed=[
                {"email": item.email, "reason": item.reason}
                for item in result.failed
            ],
            invalid=result.invalid,
        ),
    )
