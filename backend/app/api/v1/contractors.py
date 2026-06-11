from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Body, Depends, Path

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
    ContractorStatusUpdateData,
    ContractorStatusUpdateRequest,
    ContractorStatusUpdateResponse,
)
from app.services.contractor_invitations import ContractorInvitationService
from app.services.contractors import ContractorService
from app.services.normative_email_attachment import NormativeEmailAttachmentService
from app.services.user_notification_preferences import UserNotificationPreferencesService
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
    data["actions"] = ContractorActionBuilder.build_contractor_actions(current_user)
    return ContractorListItemSchema(**data)


def _contractor_profile_data(current_user: CurrentUser, item) -> ContractorProfileData:
    data = asdict(item)
    data["status"] = _ru_user_status(data["status"])
    data["actions"] = ContractorActionBuilder.build_contractor_actions(current_user)
    return ContractorProfileData(**data)


@router.get("/contractors", response_model=ContractorListResponse)
@router.get("/contractors/", response_model=ContractorListResponse, include_in_schema=False)
async def list_contractors(
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ContractorListResponse:
    async with uow:
        service = ContractorService(uow.users, uow.profiles)
        items = await service.list_contractors(current_user=current_user)

    return ContractorListResponse(
        data=ContractorListData(
            items=[_contractor_list_item(current_user, item) for item in items],
        ),
    )


@router.get("/contractors/{contractor_id}", response_model=ContractorProfileResponse)
async def get_contractor(
    contractor_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ContractorProfileResponse:
    async with uow:
        service = ContractorService(uow.users, uow.profiles)
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
        contractor_service = ContractorService(uow.users, uow.profiles)
        status_service = UserStatusService(
            uow.users,
            uow.tg_users,
            uow.profiles,
            uow.user_auth_accounts,
            uow.max_users,
            notification_preferences=UserNotificationPreferencesService(
                uow.user_contact_channels,
                uow.user_notification_preferences,
                profiles=uow.profiles,
            ),
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
