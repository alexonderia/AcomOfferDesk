from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, Path, Query

from app.api.action_flags import UserActionBuilder, serialize_permissions
from app.api.dependencies import get_current_user, get_uow
from app.core.config import settings
from app.core.uow import UnitOfWork
from app.domain.exceptions import Conflict, Forbidden
from app.domain.iam_identity import stable_iam_account_id
from app.domain.iam_roles import technical_role_name
from app.domain.policies import CurrentUser
from app.domain.iam_status import iam_auth_status_for_user_status
from app.infrastructure.iam_client import IamClient
from app.models.auth_models import UserAuthAccount
from app.schemas.users import (
    DepartmentDelegationAccessSchema,
    EconomistListData,
    EconomistListItemSchema,
    EconomistListResponse,
    HierarchyRelationBriefSchema,
    HierarchyUnitBriefSchema,
    HierarchyUserBriefSchema,
    LegacyHierarchyData,
    NotificationPreferencesData,
    NotificationPreferencesResponse,
    ManualContractorCreateRequest,
    ManualContractorCreateResponse,
    ManualContractorDuplicateItemSchema,
    ManualContractorDuplicateListData,
    ManualContractorDuplicateListResponse,
    ManualContractorUpdateRequest,
    ManualContractorUpdateResponse,
    MeData,
    MeResponse,
    RequestContractorItemSchema,
    RequestContractorListData,
    RequestContractorListResponse,
    SetMyUnavailabilityPeriodRequest,
    SetMyUnavailabilityPeriodResponse,
    SetSubordinateUnavailabilityPeriodRequest,
    SetSubordinateUnavailabilityPeriodResponse,
    SubordinateProfileData,
    SubordinateProfileResponse,
    UpdateMyCompanyContactsRequest,
    UpdateMyProfileRequest,
    UserHierarchyData,
    UserHierarchyResponse,
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
    UserDepartmentDelegationsResponse,
    UserDepartmentDelegationsData,
    UserDepartmentDelegationsUpdateRequest,
    ContractorDelegationAccessSchema,
    UserContractorDelegationsResponse,
    UserContractorDelegationsData,
    UserContractorDelegationsUpdateRequest,
    UpdateNotificationPreferencesRequest,
)
from app.api.v1.units import _unit_node_schema
from app.schemas.units import UnitTreeData, UnitTreeResponse
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
from app.services.account_recovery import AccountRecoveryService
from app.services.unit_hierarchy import UnitHierarchyService, UserHierarchyProfileState
from app.services.units import UnitService
from app.services.user_contractor_delegations import UserContractorDelegationsService
from app.services.user_department_delegations import UserDepartmentDelegationsService
from app.services.user_notification_preferences import UserNotificationPreferencesService

router = APIRouter()


USER_STATUS_RU = {
    "active": "Активен",
    "inactive": "Неактивен",
    "review": "На проверке",
    "blacklist": "В черном списке",
}


def _ru_user_status(status: str) -> str:
    return USER_STATUS_RU.get(status, status)

def _user_list_schema(
    current_user: CurrentUser,
    item,
    subordinate_ids: set[str] | None = None,
) -> UserListItemSchema:
    data = asdict(item)
    data["status"] = _ru_user_status(data["status"])
    is_manual = data.pop("is_manual", False)
    is_hierarchy_subordinate = None
    if subordinate_ids is not None:
        is_hierarchy_subordinate = item.user_id in subordinate_ids
    data["actions"] = UserActionBuilder.build_list_item(
        current_user,
        target_user_id=item.user_id,
        target_role_id=item.role_id,
        is_manual=is_manual,
        is_hierarchy_subordinate=is_hierarchy_subordinate,
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
    data["permissions"] = serialize_permissions(current_user)
    data["actions"] = UserActionBuilder.build_me(current_user)
    return MeData(**data)


def _registration_onboarding_me_data(current_user: CurrentUser, item) -> MeData:
    data = _me_data(current_user, item).model_dump()
    actions = data.get("actions") or {}
    actions["can_manage_own_profile"] = True
    actions["can_manage_company_contacts"] = True
    data["actions"] = actions
    return MeData(**data)


def _subordinate_profile_data(current_user: CurrentUser, item) -> SubordinateProfileData:
    data = asdict(item)
    data["status"] = _ru_user_status(data["status"])
    data["actions"] = UserActionBuilder.build_subordinate_profile(
        current_user,
        target_role_id=item.role_id,
    )
    return SubordinateProfileData(**data)


def _department_delegations_data(item) -> UserDepartmentDelegationsData:
    return UserDepartmentDelegationsData(
        user_id=item.user_id,
        role_id=item.role_id,
        full_name=item.full_name,
        can_manage=item.can_manage,
        accesses=[
            DepartmentDelegationAccessSchema(
                code=access.code,
                permission_code=access.permission_code,
                group=access.group,
                label=access.label,
                enabled=access.enabled,
                granted_via_role=access.granted_via_role,
                granted_individually=access.granted_individually,
            )
            for access in item.accesses
        ],
        token_refresh_required=item.token_refresh_required,
        warning=item.warning,
    )


def _contractor_delegations_data(item) -> UserContractorDelegationsData:
    return UserContractorDelegationsData(
        user_id=item.user_id,
        role_id=item.role_id,
        full_name=item.full_name,
        can_manage=item.can_manage,
        accesses=[
            ContractorDelegationAccessSchema(
                code=access.code,
                label=access.label,
                description=access.description,
                enabled=access.enabled,
                granted_via_role=access.granted_via_role,
                granted_individually=access.granted_individually,
            )
            for access in item.accesses
        ],
        token_refresh_required=item.token_refresh_required,
        warning=item.warning,
    )


def _hierarchy_user_brief_schema(item) -> HierarchyUserBriefSchema:
    return HierarchyUserBriefSchema(
        user_id=item.user_id,
        full_name=item.full_name,
        role_id=item.role_id,
        role_name=item.role_name,
        status=_ru_user_status(item.status),
    )


def _hierarchy_relation_schema(item) -> HierarchyRelationBriefSchema:
    return HierarchyRelationBriefSchema(
        user_id=item.user_id,
        full_name=item.full_name,
        role_id=item.role_id,
        role_name=item.role_name,
        status=_ru_user_status(item.status),
        source_unit_id=item.source_unit_id,
        source_unit_name=item.source_unit_name,
    )


def _user_hierarchy_data(item: UserHierarchyProfileState) -> UserHierarchyData:
    return UserHierarchyData(
        user=_hierarchy_user_brief_schema(item.user),
        units=[
            HierarchyUnitBriefSchema(
                unit_id=unit.unit_id,
                name=unit.name,
                id_parent=unit.id_parent,
            )
            for unit in item.units
        ],
        managers=[_hierarchy_relation_schema(manager) for manager in item.managers],
        subordinates=[_hierarchy_relation_schema(subordinate) for subordinate in item.subordinates],
        legacy_hierarchy=LegacyHierarchyData(
            legacy_manager=(
                _hierarchy_user_brief_schema(item.legacy_hierarchy.legacy_manager)
                if item.legacy_hierarchy.legacy_manager is not None
                else None
            ),
            legacy_subordinates=[
                _hierarchy_user_brief_schema(subordinate)
                for subordinate in item.legacy_hierarchy.legacy_subordinates
            ],
            is_business_source=item.legacy_hierarchy.is_business_source,
            note=item.legacy_hierarchy.note,
        ),
    )


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
        subordinate_ids = await service.resolve_hierarchy_subordinate_user_ids(current_user=current_user)

    return UserListResponse(
        data=UserListData(
            items=[_user_list_schema(current_user, item, subordinate_ids) for item in users],
        ),
    )


@router.get(
    "/users/manager-candidates",
    response_model=UserListResponse,
    deprecated=True,
    summary="[Legacy] Кандидаты в руководители по users.id_parent",
)
@router.get("/users/manager-candidates/", response_model=UserListResponse, include_in_schema=False, deprecated=True)
async def list_manager_candidates(
    target_role_id: int = Query(..., ge=1),
    target_user_id: str | None = Query(default=None, min_length=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UserListResponse:
    async with uow:
        service = UserQueryService(uow.users, uow.user_status_periods)
        users = await service.list_manager_candidates(
            current_user=current_user,
            target_role_id=target_role_id,
            target_user_id=target_user_id,
        )

    return UserListResponse(
        data=UserListData(
            items=[_user_list_schema(current_user, item) for item in users],
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
        department_name = await uow.units.get_primary_department_name_for_user(
            user_id=current_user.user_id,
        )

    if current_user.role_id != settings.contractor_role_id:
        me = me.__class__(
            user_id=me.user_id,
            role_id=me.role_id,
            status=me.status,
            full_name=me.full_name,
            phone=me.phone,
            mail=me.mail,
            unavailable_period=me.unavailable_period,
            unavailable_periods=me.unavailable_periods,
        )

    return MeResponse(
        data=_me_data(current_user, me).model_copy(update={"department_name": department_name}),
    )


@router.get("/users/me/hierarchy", response_model=UserHierarchyResponse)
@router.get("/users/me/hierarchy/", response_model=UserHierarchyResponse, include_in_schema=False)
async def get_my_hierarchy(
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UserHierarchyResponse:
    async with uow:
        hierarchy = UnitHierarchyService(uow.users)
        state = await hierarchy.get_user_hierarchy_profile(user_id=current_user.user_id)
        if state is None:
            raise Forbidden("Иерархия пользователя недоступна")

    return UserHierarchyResponse(data=_user_hierarchy_data(state))


@router.get("/users/me/registration-profile", response_model=MeResponse)
async def get_my_registration_profile(
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> MeResponse:
    async with uow:
        service = UserQueryService(uow.users, uow.user_status_periods)
        me = await service.get_me_for_review_onboarding(current_user)

    return MeResponse(
        data=_registration_onboarding_me_data(current_user, me),
    )


@router.patch("/users/me/profile", response_model=MeResponse)
async def update_my_profile(
    payload: UpdateMyProfileRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> MeResponse:
    async with uow:
        self_service = UserSelfService(
            uow.users,
            uow.profiles,
            uow.company_contacts,
            uow.user_status_periods,
            uow.user_auth_accounts,
            uow.user_contact_channels,
        )
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
            full_name=me.full_name,
            phone=me.phone,
            mail=me.mail,
            unavailable_period=me.unavailable_period,
            unavailable_periods=me.unavailable_periods,
        )

    return MeResponse(
        data=_me_data(current_user, me),
    )


def _notification_preferences_data(item) -> NotificationPreferencesData:
    return NotificationPreferencesData(
        mode=item.mode,
        email_available=item.email_available,
        email=item.email,
        preferences={
            notification_type: {
                "email": notification_state.email,
            }
            for notification_type, notification_state in item.preferences.items()
        },
    )


@router.get("/users/me/notification-preferences", response_model=NotificationPreferencesResponse)
async def get_my_notification_preferences(
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> NotificationPreferencesResponse:
    async with uow:
        service = UserNotificationPreferencesService(
            uow.user_contact_channels,
            uow.user_notification_preferences,
            profiles=uow.profiles,
        )
        state = await service.get_state(user_id=current_user.user_id)

    return NotificationPreferencesResponse(data=_notification_preferences_data(state))


@router.put("/users/me/notification-preferences", response_model=NotificationPreferencesResponse)
async def update_my_notification_preferences(
    payload: UpdateNotificationPreferencesRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> NotificationPreferencesResponse:
    async with uow:
        service = UserNotificationPreferencesService(
            uow.user_contact_channels,
            uow.user_notification_preferences,
            profiles=uow.profiles,
        )
        if payload.preferences is not None:
            state = await service.update_preferences(
                user_id=current_user.user_id,
                preferences=payload.preferences,
            )
        elif payload.mode is not None:
            state = await service.update_mode(user_id=current_user.user_id, mode=payload.mode)
        else:
            state = await service.get_state(user_id=current_user.user_id)

    return NotificationPreferencesResponse(data=_notification_preferences_data(state))


@router.patch("/users/me/registration-profile", response_model=MeResponse)
async def update_my_registration_profile(
    payload: UpdateMyProfileRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> MeResponse:
    async with uow:
        self_service = UserSelfService(
            uow.users,
            uow.profiles,
            uow.company_contacts,
            uow.user_status_periods,
            uow.user_auth_accounts,
            uow.user_contact_channels,
        )
        await self_service.update_my_profile_for_review_onboarding(
            current_user,
            full_name=payload.full_name,
            phone=payload.phone,
            mail=payload.mail,
        )

        query_service = UserQueryService(uow.users, uow.user_status_periods)
        me = await query_service.get_me_for_review_onboarding(current_user)

    return MeResponse(
        data=_registration_onboarding_me_data(current_user, me),
    )


@router.patch("/users/me/company-contacts", response_model=MeResponse)
async def update_my_company_contacts(
    payload: UpdateMyCompanyContactsRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> MeResponse:
    async with uow:
        self_service = UserSelfService(
            uow.users,
            uow.profiles,
            uow.company_contacts,
            uow.user_status_periods,
            uow.user_auth_accounts,
            uow.user_contact_channels,
        )
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
    )


@router.patch("/users/me/registration-company-contacts", response_model=MeResponse)
async def update_my_registration_company_contacts(
    payload: UpdateMyCompanyContactsRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> MeResponse:
    async with uow:
        self_service = UserSelfService(
            uow.users,
            uow.profiles,
            uow.company_contacts,
            uow.user_status_periods,
            uow.user_auth_accounts,
            uow.user_contact_channels,
        )
        await self_service.update_my_company_contacts_for_review_onboarding(
            current_user,
            company_name=payload.company_name,
            inn=payload.inn,
            company_phone=payload.company_phone,
            company_mail=payload.company_mail,
            address=payload.address,
            note=payload.note,
        )

        query_service = UserQueryService(uow.users, uow.user_status_periods)
        me = await query_service.get_me_for_review_onboarding(current_user)

    return MeResponse(
        data=_registration_onboarding_me_data(current_user, me),
    )


@router.post("/users/me/unavailability-period", response_model=SetMyUnavailabilityPeriodResponse)
async def set_my_unavailability_period(
    payload: SetMyUnavailabilityPeriodRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> SetMyUnavailabilityPeriodResponse:
    async with uow:
        self_service = UserSelfService(
            uow.users,
            uow.profiles,
            uow.company_contacts,
            uow.user_status_periods,
            uow.user_auth_accounts,
            uow.user_contact_channels,
        )
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
            full_name=me.full_name,
            phone=me.phone,
            mail=me.mail,
            unavailable_period=me.unavailable_period,
            unavailable_periods=me.unavailable_periods,
        )

    return SetMyUnavailabilityPeriodResponse(
        data=_me_data(current_user, me),
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
    )


@router.get("/users/{user_id}/hierarchy", response_model=UserHierarchyResponse)
async def get_user_hierarchy(
    user_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UserHierarchyResponse:
    async with uow:
        hierarchy = UnitHierarchyService(uow.users)
        if not await hierarchy.can_view_user(current_user=current_user, target_user_id=user_id):
            raise Forbidden("Недостаточно прав для просмотра иерархии пользователя")
        visible_user_ids = await hierarchy.get_visible_user_ids(current_user=current_user)
        if current_user.user_id == user_id or visible_user_ids is None:
            visible_user_ids = None
        state = await hierarchy.get_user_hierarchy_profile(
            user_id=user_id,
            visible_user_ids=visible_user_ids,
        )
        if state is None:
            raise Forbidden("Иерархия пользователя недоступна")

    return UserHierarchyResponse(data=_user_hierarchy_data(state))


@router.get("/users/{user_id}/hierarchy/units-tree", response_model=UnitTreeResponse)
async def get_user_hierarchy_units_tree(
    user_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UnitTreeResponse:
    async with uow:
        hierarchy = UnitHierarchyService(uow.users)
        if not await hierarchy.can_view_user(current_user=current_user, target_user_id=user_id):
            raise Forbidden("Недостаточно прав для просмотра иерархии пользователя")
        service = UnitService(uow.units, uow.users)
        items = await service.get_tree_for_user_hierarchy(
            current_user=current_user,
            target_user_id=user_id,
        )

    return UnitTreeResponse(data=UnitTreeData(items=[_unit_node_schema(item) for item in items]))


@router.get("/users/{user_id}/delegations/department", response_model=UserDepartmentDelegationsResponse)
async def get_user_department_delegations(
    user_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UserDepartmentDelegationsResponse:
    async with uow:
        service = UserDepartmentDelegationsService(
            users=uow.users,
            profiles=uow.profiles,
            user_auth_accounts=uow.user_auth_accounts,
        )
        state = await service.get_state(
            current_user=current_user,
            target_user_id=user_id,
        )
    return UserDepartmentDelegationsResponse(data=_department_delegations_data(state))


@router.get("/users/{user_id}/delegations/contractors", response_model=UserContractorDelegationsResponse)
async def get_user_contractor_delegations(
    user_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UserContractorDelegationsResponse:
    async with uow:
        service = UserContractorDelegationsService(
            users=uow.users,
            profiles=uow.profiles,
            user_auth_accounts=uow.user_auth_accounts,
        )
        state = await service.get_state(
            current_user=current_user,
            target_user_id=user_id,
        )
    return UserContractorDelegationsResponse(data=_contractor_delegations_data(state))


@router.put("/users/{user_id}/delegations/contractors", response_model=UserContractorDelegationsResponse)
async def update_user_contractor_delegations(
    payload: UserContractorDelegationsUpdateRequest,
    user_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UserContractorDelegationsResponse:
    async with uow:
        service = UserContractorDelegationsService(
            users=uow.users,
            profiles=uow.profiles,
            user_auth_accounts=uow.user_auth_accounts,
        )
        state = await service.update_state(
            current_user=current_user,
            target_user_id=user_id,
            requested_access_codes=payload.access_codes,
        )
    return UserContractorDelegationsResponse(data=_contractor_delegations_data(state))


@router.put("/users/{user_id}/delegations/department", response_model=UserDepartmentDelegationsResponse)
async def update_user_department_delegations(
    payload: UserDepartmentDelegationsUpdateRequest,
    user_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UserDepartmentDelegationsResponse:
    async with uow:
        service = UserDepartmentDelegationsService(
            users=uow.users,
            profiles=uow.profiles,
            user_auth_accounts=uow.user_auth_accounts,
        )
        state = await service.update_state(
            current_user=current_user,
            target_user_id=user_id,
            requested_access_codes=payload.access_codes,
        )
    return UserDepartmentDelegationsResponse(data=_department_delegations_data(state))


@router.post("/users/{user_id}/unavailability-period", response_model=SetSubordinateUnavailabilityPeriodResponse)
async def set_subordinate_unavailability_period(
    payload: SetSubordinateUnavailabilityPeriodRequest,
    user_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> SetSubordinateUnavailabilityPeriodResponse:
    async with uow:
        self_service = UserSelfService(
            uow.users,
            uow.profiles,
            uow.company_contacts,
            uow.user_status_periods,
            uow.user_auth_accounts,
            uow.user_contact_channels,
        )
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
        ),
    )


@router.post("/users/manual-contractor", response_model=ManualContractorCreateResponse)
async def create_manual_contractor(
    payload: ManualContractorCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ManualContractorCreateResponse:
    async with uow:
        service = ManualContractorService(
            uow.users,
            uow.profiles,
            uow.company_contacts,
            uow.user_auth_accounts,
            uow.units,
            user_contact_channels=uow.user_contact_channels,
            after_commit_hook_registrar=getattr(uow, "add_after_commit_hook", None),
        )
        result = await service.create_manual_contractor(
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
        if result.created:
            binding = await uow.user_auth_accounts.get_by_user_provider(
                user_id=result.user_id,
                provider="iam",
                include_inactive=True,
            )
            account_id = stable_iam_account_id(result.user_id) if binding is None else binding.external_subject_id
            account = await IamClient().put_account(
                account_id=account_id,
                login=result.user_id,
                role="contractor",
                auth_status="active",
            )
            if binding is None:
                binding = UserAuthAccount(
                    id_user=result.user_id,
                    provider="iam",
                    external_subject_id=account.id,
                    external_username=result.user_id,
                    external_email=payload.company_mail,
                    is_active=True,
                )
                await uow.user_auth_accounts.add(binding)
            else:
                binding.is_active = True
            if payload.company_mail:
                await AccountRecoveryService(uow).request_recovery(identifier=result.user_id)
    return ManualContractorCreateResponse(
        data={
            "user_id": result.user_id,
            "outcome": "created" if result.created else "duplicate_found",
            "duplicate": None if result.created else {
                "company_name": result.company_name,
                "inn": result.inn,
                "company_mail": result.company_mail,
            },
        },
    )


@router.get("/users/manual-contractor-duplicates", response_model=ManualContractorDuplicateListResponse)
async def list_manual_contractor_duplicates(
    company_name: str | None = Query(default=None, max_length=256),
    inn: str | None = Query(default=None, max_length=32),
    company_mail: str | None = Query(default=None, max_length=256),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ManualContractorDuplicateListResponse:
    async with uow:
        service = ManualContractorService(
            uow.users,
            uow.profiles,
            uow.company_contacts,
            uow.user_auth_accounts,
            uow.units,
            user_contact_channels=uow.user_contact_channels,
        )
        items = await service.list_possible_duplicates(
            current_user=current_user,
            company_name=company_name,
            inn=inn,
            company_mail=company_mail,
        )
    return ManualContractorDuplicateListResponse(
        data=ManualContractorDuplicateListData(
            items=[ManualContractorDuplicateItemSchema(**item.__dict__) for item in items],
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
        service = ManualContractorService(uow.users, uow.profiles, uow.company_contacts, uow.user_auth_accounts, uow.units)
        updated_user_id = await service.update_manual_contractor(
            current_user=current_user,
            user_id=user_id,
            data=ManualContractorUpdateInput(
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
    )


@router.patch("/users/{user_id}/status", response_model=UserStatusUpdateResponse)
async def update_user_status(
    payload: UserStatusUpdateRequest,
    user_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UserStatusUpdateResponse:
    async with uow:
        target_user = await uow.users.get_by_id(user_id)
        if target_user is not None and target_user.id_role == settings.contractor_role_id:
            raise Forbidden("Статус контрагента изменяется только через /contractors/{contractor_id}/status")
        service = UserStatusService(
            uow.users,
            uow.profiles,
            uow.user_auth_accounts,
            user_contact_channels=uow.user_contact_channels,
            notification_preferences=UserNotificationPreferencesService(
                uow.user_contact_channels,
                uow.user_notification_preferences,
                profiles=uow.profiles,
            ),
            after_commit_hook_registrar=getattr(uow, "add_after_commit_hook", None),
        )
        result = await service.update_statuses(
            current_user=current_user,
            user_id=user_id,
            user_status=payload.user_status,
        )
        binding = await uow.user_auth_accounts.get_by_user_provider(
            user_id=user_id,
            provider="iam",
        )
        if binding is None:
            raise Conflict("Для пользователя отсутствует активная привязка IAM")
        iam_status = iam_auth_status_for_user_status(payload.user_status)
        await IamClient().update_status(
            account_id=binding.external_subject_id,
            auth_status=iam_status,
            actor_account_id=current_user.iam_account_id,
            actor_session_id=current_user.iam_session_id,
        )

    return UserStatusUpdateResponse(
        data=UserStatusUpdateData(
            user_id=result.user_id,
            user_status=_ru_user_status(result.user_status),
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
        service = UserRoleService(uow.users, uow.user_auth_accounts, uow.units)
        result = await service.update_role(
            current_user=current_user,
            user_id=user_id,
            role_id=payload.role_id,
        )
        binding = await uow.user_auth_accounts.get_by_user_provider(
            user_id=user_id,
            provider="iam",
        )
        role_name = technical_role_name(payload.role_id)
        if binding is None:
            raise Conflict("Для пользователя отсутствует активная привязка IAM")
        if role_name is None:
            raise Conflict("Выбранная роль не поддерживается IAM")
        await IamClient().update_role(
            account_id=binding.external_subject_id,
            role=role_name,
            actor_account_id=current_user.iam_account_id,
            actor_session_id=current_user.iam_session_id,
        )

    return UserRoleUpdateResponse(
        data=UserRoleUpdateData(user_id=result.user_id, role_id=result.role_id),
    )


@router.patch(
    "/users/{user_id}/manager",
    response_model=UserManagerUpdateResponse,
    deprecated=True,
    summary="[Legacy] Смена руководителя через users.id_parent",
)
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
    )

