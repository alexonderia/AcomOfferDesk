from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, Path, Query

from app.api.action_flags import UserActionBuilder, serialize_permissions
from app.api.dependencies import get_current_user, get_uow
from app.core.config import settings
from app.core.uow import UnitOfWork
from app.domain.policies import CurrentUser
from app.schemas.links import Link, LinkSet
from app.schemas.users import (
    EconomistListData,
    EconomistListItemSchema,
    EconomistListResponse,
    ManualContractorCreateRequest,
    ManualContractorCreateResponse,
    ManualContractorUpdateRequest,
    ManualContractorUpdateResponse,
    MeData,
    MeResponse,
    RequestContractorItemSchema,
    RequestContractorListData,
    RequestContractorListResponse,
    RequestEconomistItemSchema,
    RequestEconomistListData,
    RequestEconomistListResponse,
    SetMyUnavailabilityPeriodRequest,
    SetMyUnavailabilityPeriodResponse,
    SetSubordinateUnavailabilityPeriodRequest,
    SetSubordinateUnavailabilityPeriodResponse,
    SubordinateProfileData,
    SubordinateProfileResponse,
    UpdateMyCompanyContactsRequest,
    UpdateMyCredentialsRequest,
    UpdateMyProfileRequest,
    UserListData,
    UserListItemSchema,
    UserManagerUpdateData,
    UserManagerUpdateRequest,
    UserManagerUpdateResponse,
    UserListResponse,
    UserRoleUpdateData,
    UserRoleUpdateRequest,
    UserRoleUpdateResponse,
    UserStatusUpdateData,
    UserStatusUpdateRequest,
    UserStatusUpdateResponse,
)
from app.services.users import (
    ManualContractorCreateInput,
    ManualContractorService,
    ManualContractorUpdateInput,
    UserManagerService,
    UserQueryService,
    UserRoleService,
    UserSelfService,
    UserStatusService,
)

router = APIRouter()


USER_STATUS_RU = {
    "active": "Активен",
    "inactive": "Неактивен",
    "review": "На проверке",
    "blacklist": "В черном списке",
}


def _ru_user_status(status: str) -> str:
    return USER_STATUS_RU.get(status, status)

def _user_list_schema(current_user: CurrentUser, item) -> UserListItemSchema:
    data = asdict(item)
    data["status"] = _ru_user_status(data["status"])
    data.pop("tg_user_id", None)
    data.pop("tg_status", None)
    data["actions"] = UserActionBuilder.build_list_item(
        current_user,
        target_user_id=item.user_id,
        target_role_id=item.role_id,
        target_tg_user_id=item.tg_user_id,
    )
    return UserListItemSchema(**data)


def _economist_list_schema(current_user: CurrentUser, item) -> EconomistListItemSchema:
    data = asdict(item)
    data["status"] = _ru_user_status(data["status"])
    data["actions"] = UserActionBuilder.build_list_item(
        current_user,
        target_user_id=item.user_id,
        target_role_id=settings.economist_role_id,
    )
    return EconomistListItemSchema(**data)


def _me_data(current_user: CurrentUser, item) -> MeData:
    data = asdict(item)
    data["status"] = _ru_user_status(data["status"])
    data.pop("tg_user_id", None)
    data["permissions"] = serialize_permissions(current_user)
    data["actions"] = UserActionBuilder.build_me(current_user)
    return MeData(**data)


def _subordinate_profile_data(current_user: CurrentUser, item) -> SubordinateProfileData:
    data = asdict(item)
    data["status"] = _ru_user_status(data["status"])
    data["actions"] = UserActionBuilder.build_subordinate_profile(
        current_user,
        target_role_id=item.role_id,
    )
    return SubordinateProfileData(**data)


@router.get("/users", response_model=UserListResponse)
@router.get("/users/", response_model=UserListResponse, include_in_schema=False)
async def list_users(
    role_id: int | None = Query(default=None, ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UserListResponse:
    async with uow:
        service = UserQueryService(uow.users, uow.user_status_periods)
        users = await service.list_users(current_user=current_user, role_id=role_id)

    return UserListResponse(
        data=UserListData(
            items=[_user_list_schema(current_user, item) for item in users],
            permissions=serialize_permissions(current_user),
        ),
        _links=LinkSet(
            self=Link(href="/api/v1/users", method="GET"),
        ),
    )


@router.get("/users/manager-candidates", response_model=UserListResponse)
@router.get("/users/manager-candidates/", response_model=UserListResponse, include_in_schema=False)
async def list_manager_candidates(
    target_role_id: int = Query(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UserListResponse:
    async with uow:
        service = UserQueryService(uow.users, uow.user_status_periods)
        users = await service.list_manager_candidates(current_user=current_user, target_role_id=target_role_id)

    return UserListResponse(
        data=UserListData(
            items=[_user_list_schema(current_user, item) for item in users],
            permissions=serialize_permissions(current_user),
        ),
        _links=LinkSet(
            self=Link(href="/api/v1/users/manager-candidates", method="GET"),
        ),
    )


@router.get("/users/economists", response_model=EconomistListResponse)
@router.get("/users/economists/", response_model=EconomistListResponse, include_in_schema=False)
async def list_economists(
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> EconomistListResponse:
    async with uow:
        service = UserQueryService(uow.users, uow.user_status_periods)
        economists = await service.list_economists(current_user=current_user)

    return EconomistListResponse(
        data=EconomistListData(
            items=[_economist_list_schema(current_user, item) for item in economists],
            permissions=serialize_permissions(current_user),
        ),
        _links=LinkSet(
            self=Link(href="/api/v1/users/economists", method="GET"),
        ),
    )


@router.get("/users/me", response_model=MeResponse)
@router.get("/users/me/", response_model=MeResponse, include_in_schema=False)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> MeResponse:
    async with uow:
        service = UserQueryService(uow.users, uow.user_status_periods)
        me = await service.get_me(current_user)

    if current_user.role_id != settings.contractor_role_id:
        me = me.__class__(
            user_id=me.user_id,
            role_id=me.role_id,
            status=me.status,
            tg_user_id=me.tg_user_id,
            full_name=me.full_name,
            phone=me.phone,
            mail=me.mail,
            unavailable_period=me.unavailable_period,
            unavailable_periods=me.unavailable_periods,
        )

    return MeResponse(
        data=_me_data(current_user, me),
        _links=LinkSet(
            self=Link(href="/api/v1/users/me", method="GET"),
        ),
    )


@router.patch("/users/me/credentials", response_model=MeResponse)
async def update_my_credentials(
    payload: UpdateMyCredentialsRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> MeResponse:
    async with uow:
        self_service = UserSelfService(uow.users, uow.profiles, uow.company_contacts, uow.user_status_periods)
        await self_service.update_my_credentials(
            current_user,
            current_password=payload.current_password,
            new_password=payload.new_password,
        )

        query_service = UserQueryService(uow.users, uow.user_status_periods)
        me = await query_service.get_me(current_user)

    if current_user.role_id != settings.contractor_role_id:
        me = me.__class__(
            user_id=me.user_id,
            role_id=me.role_id,
            status=me.status,
            tg_user_id=me.tg_user_id,
            full_name=me.full_name,
            phone=me.phone,
            mail=me.mail,
            unavailable_period=me.unavailable_period,
            unavailable_periods=me.unavailable_periods,
        )

    return MeResponse(
        data=_me_data(current_user, me),
        _links=LinkSet(
            self=Link(href="/api/v1/users/me/credentials", method="PATCH"),
        ),
    )


@router.patch("/users/me/profile", response_model=MeResponse)
async def update_my_profile(
    payload: UpdateMyProfileRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> MeResponse:
    async with uow:
        self_service = UserSelfService(uow.users, uow.profiles, uow.company_contacts, uow.user_status_periods)
        await self_service.update_my_profile(
            current_user,
            full_name=payload.full_name,
            phone=payload.phone,
            mail=payload.mail,
        )

        query_service = UserQueryService(uow.users, uow.user_status_periods)
        me = await query_service.get_me(current_user)

    if current_user.role_id != settings.contractor_role_id:
        me = me.__class__(
            user_id=me.user_id,
            role_id=me.role_id,
            status=me.status,
            tg_user_id=me.tg_user_id,
            full_name=me.full_name,
            phone=me.phone,
            mail=me.mail,
            unavailable_period=me.unavailable_period,
            unavailable_periods=me.unavailable_periods,
        )

    return MeResponse(
        data=_me_data(current_user, me),
        _links=LinkSet(
            self=Link(href="/api/v1/users/me/profile", method="PATCH"),
        ),
    )


@router.patch("/users/me/company-contacts", response_model=MeResponse)
async def update_my_company_contacts(
    payload: UpdateMyCompanyContactsRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> MeResponse:
    async with uow:
        self_service = UserSelfService(uow.users, uow.profiles, uow.company_contacts, uow.user_status_periods)
        await self_service.update_my_company_contacts(
            current_user,
            company_name=payload.company_name,
            inn=payload.inn,
            company_phone=payload.company_phone,
            company_mail=payload.company_mail,
            address=payload.address,
            note=payload.note,
        )

        query_service = UserQueryService(uow.users, uow.user_status_periods)
        me = await query_service.get_me(current_user)

    return MeResponse(
        data=_me_data(current_user, me),
        _links=LinkSet(
            self=Link(href="/api/v1/users/me/company-contacts", method="PATCH"),
        ),
    )


@router.post("/users/me/unavailability-period", response_model=SetMyUnavailabilityPeriodResponse)
async def set_my_unavailability_period(
    payload: SetMyUnavailabilityPeriodRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> SetMyUnavailabilityPeriodResponse:
    async with uow:
        self_service = UserSelfService(uow.users, uow.profiles, uow.company_contacts, uow.user_status_periods)
        await self_service.set_my_unavailability_period(
            current_user,
            status=payload.status,
            started_at=payload.started_at,
            ended_at=payload.ended_at,
        )

        query_service = UserQueryService(uow.users, uow.user_status_periods)
        me = await query_service.get_me(current_user)

    if current_user.role_id != settings.contractor_role_id:
        me = me.__class__(
            user_id=me.user_id,
            role_id=me.role_id,
            status=me.status,
            tg_user_id=me.tg_user_id,
            full_name=me.full_name,
            phone=me.phone,
            mail=me.mail,
            unavailable_period=me.unavailable_period,
            unavailable_periods=me.unavailable_periods,
        )

    return SetMyUnavailabilityPeriodResponse(
        data=_me_data(current_user, me),
        _links=LinkSet(
            self=Link(href="/api/v1/users/me/unavailability-period", method="POST"),
        ),
    )


@router.get("/users/{user_id}/profile", response_model=SubordinateProfileResponse)
async def get_subordinate_profile(
    user_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> SubordinateProfileResponse:
    async with uow:
        query_service = UserQueryService(uow.users, uow.user_status_periods)
        profile = await query_service.get_subordinate_profile(
            current_user=current_user,
            subordinate_user_id=user_id,
        )

    return SubordinateProfileResponse(
        data=_subordinate_profile_data(current_user, profile),
        _links=LinkSet(
            self=Link(href=f"/api/v1/users/{user_id}/profile", method="GET"),
        ),
    )


@router.post("/users/{user_id}/unavailability-period", response_model=SetSubordinateUnavailabilityPeriodResponse)
async def set_subordinate_unavailability_period(
    payload: SetSubordinateUnavailabilityPeriodRequest,
    user_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> SetSubordinateUnavailabilityPeriodResponse:
    async with uow:
        self_service = UserSelfService(uow.users, uow.profiles, uow.company_contacts, uow.user_status_periods)
        await self_service.set_subordinate_unavailability_period(
            current_user=current_user,
            subordinate_user_id=user_id,
            status=payload.status,
            started_at=payload.started_at,
            ended_at=payload.ended_at,
        )

        query_service = UserQueryService(uow.users, uow.user_status_periods)
        profile = await query_service.get_subordinate_profile(
            current_user=current_user,
            subordinate_user_id=user_id,
        )

    return SetSubordinateUnavailabilityPeriodResponse(
        data=_subordinate_profile_data(current_user, profile),
        _links=LinkSet(
            self=Link(href=f"/api/v1/users/{user_id}/unavailability-period", method="POST"),
        ),
    )


@router.get("/users/request-economists", response_model=RequestEconomistListResponse)
@router.get("/users/request-economists/", response_model=RequestEconomistListResponse, include_in_schema=False)
async def list_request_economists(
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> RequestEconomistListResponse:
    async with uow:
        service = UserQueryService(uow.users, uow.user_status_periods)
        users = await service.list_request_economists(current_user=current_user)

    return RequestEconomistListResponse(
        data=RequestEconomistListData(
            items=[RequestEconomistItemSchema(**asdict(item)) for item in users],
            permissions=serialize_permissions(current_user),
        ),
        _links=LinkSet(
            self=Link(href="/api/v1/users/request-economists", method="GET"),
        ),
    )


@router.get("/users/request-contractors", response_model=RequestContractorListResponse)
@router.get("/users/request-contractors/", response_model=RequestContractorListResponse, include_in_schema=False)
async def list_request_contractors(
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> RequestContractorListResponse:
    async with uow:
        service = UserQueryService(uow.users, uow.user_status_periods)
        users = await service.list_request_contractors(current_user=current_user)

    return RequestContractorListResponse(
        data=RequestContractorListData(
            items=[
                RequestContractorItemSchema(
                    user_id=item.user_id,
                    full_name=item.full_name,
                    company_name=item.company_name,
                    mail=item.mail,
                    company_mail=item.company_mail,
                )
                for item in users
            ],
            permissions=serialize_permissions(current_user),
        ),
        _links=LinkSet(
            self=Link(href="/api/v1/users/request-contractors", method="GET"),
        ),
    )


@router.post("/users/manual-contractor", response_model=ManualContractorCreateResponse)
async def create_manual_contractor(
    payload: ManualContractorCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ManualContractorCreateResponse:
    async with uow:
        service = ManualContractorService(uow.users, uow.profiles, uow.company_contacts, uow.user_auth_accounts)
        created_user_id = await service.create_manual_contractor(
            current_user=current_user,
            data=ManualContractorCreateInput(
                company_name=payload.company_name,
                inn=payload.inn,
                company_phone=payload.company_phone,
                company_mail=payload.company_mail,
                address=payload.address,
                note=payload.note,
            ),
        )

    return ManualContractorCreateResponse(
        data={"user_id": created_user_id},
        _links=LinkSet(
            self=Link(href="/api/v1/users/manual-contractor", method="POST"),
        ),
    )


@router.patch("/users/{user_id}/manual-contractor", response_model=ManualContractorUpdateResponse)
async def update_manual_contractor(
    payload: ManualContractorUpdateRequest,
    user_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ManualContractorUpdateResponse:
    async with uow:
        service = ManualContractorService(uow.users, uow.profiles, uow.company_contacts, uow.user_auth_accounts)
        updated_user_id = await service.update_manual_contractor(
            current_user=current_user,
            user_id=user_id,
            data=ManualContractorUpdateInput(
                login=payload.login,
                password=payload.password,
                full_name=payload.full_name,
                phone=payload.phone,
                mail=payload.mail,
                company_name=payload.company_name,
                inn=payload.inn,
                company_phone=payload.company_phone,
                company_mail=payload.company_mail,
                address=payload.address,
                note=payload.note,
            ),
        )

    return ManualContractorUpdateResponse(
        data={"user_id": updated_user_id},
        _links=LinkSet(
            self=Link(href=f"/api/v1/users/{updated_user_id}/manual-contractor", method="PATCH"),
        ),
    )


@router.patch("/users/{user_id}/status", response_model=UserStatusUpdateResponse)
async def update_user_status(
    payload: UserStatusUpdateRequest,
    user_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UserStatusUpdateResponse:
    async with uow:
        service = UserStatusService(uow.users, uow.tg_users, uow.profiles)
        result = await service.update_statuses(
            current_user=current_user,
            user_id=user_id,
            user_status=payload.user_status,
            tg_status=None,
        )

    return UserStatusUpdateResponse(
        data=UserStatusUpdateData(
            user_id=result.user_id,
            user_status=_ru_user_status(result.user_status),
            tg_user_id=result.tg_user_id,
            tg_status=result.tg_status,
        ),
        _links=LinkSet(
            self=Link(href=f"/api/v1/users/{result.user_id}/status", method="PATCH"),
        ),
    )


@router.patch("/users/{user_id}/role", response_model=UserRoleUpdateResponse)
async def update_user_role(
    payload: UserRoleUpdateRequest,
    user_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UserRoleUpdateResponse:
    async with uow:
        service = UserRoleService(uow.users)
        result = await service.update_role(
            current_user=current_user,
            user_id=user_id,
            role_id=payload.role_id,
        )

    return UserRoleUpdateResponse(
        data=UserRoleUpdateData(user_id=result.user_id, role_id=result.role_id),
        _links=LinkSet(
            self=Link(href=f"/api/v1/users/{result.user_id}/role", method="PATCH"),
        ),
    )


@router.patch("/users/{user_id}/manager", response_model=UserManagerUpdateResponse)
async def update_user_manager(
    payload: UserManagerUpdateRequest,
    user_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UserManagerUpdateResponse:
    async with uow:
        service = UserManagerService(uow.users)
        result = await service.update_manager(
            current_user=current_user,
            user_id=user_id,
            manager_user_id=payload.manager_user_id,
        )

    return UserManagerUpdateResponse(
        data=UserManagerUpdateData(user_id=result.user_id, manager_user_id=result.manager_user_id),
        _links=LinkSet(
            self=Link(href=f"/api/v1/users/{result.user_id}/manager", method="PATCH"),
        ),
    )

