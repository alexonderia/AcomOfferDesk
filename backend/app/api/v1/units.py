from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, Path, Query, Response

from app.api.dependencies import get_current_user, get_uow
from app.core.uow import UnitOfWork
from app.domain.policies import CurrentUser
from app.schemas.units import (
    AddUnitMemberRequest,
    AvailableUnitUsersData,
    AvailableUnitUsersResponse,
    AvailableUnitUserSchema,
    CreateUnitRequest,
    RecommendedHierarchyData,
    RecommendedHierarchyNodeSchema,
    RecommendedHierarchyResponse,
    UnitMemberResponse,
    UnitMembersData,
    UnitMembersResponse,
    UnitMemberSchema,
    UnitMutationResponse,
    UnitNodeSchema,
    UnitTreeData,
    UnitTreeResponse,
    UpdateUnitRequest,
)
from app.services.units import UnitService

router = APIRouter()


def _unit_member_schema(item) -> UnitMemberSchema:
    return UnitMemberSchema(
        user_id=item.user_id,
        full_name=item.full_name,
        role_id=item.role_id,
        role_name=item.role_name,
        status=item.status,
    )


def _available_user_schema(item) -> AvailableUnitUserSchema:
    return AvailableUnitUserSchema(
        user_id=item.user_id,
        full_name=item.full_name,
        role_id=item.role_id,
        role_name=item.role_name,
        status=item.status,
    )


def _unit_node_schema(item) -> UnitNodeSchema:
    return UnitNodeSchema(
        unit_id=item.unit_id,
        name=item.name,
        id_parent=item.id_parent,
        is_active=item.is_active,
        members=[_unit_member_schema(member) for member in item.members],
        children=[_unit_node_schema(child) for child in item.children],
        actions=asdict(item.actions),
    )


def _recommended_hierarchy_node_schema(item) -> RecommendedHierarchyNodeSchema:
    return RecommendedHierarchyNodeSchema(
        user_id=item.user_id,
        full_name=item.full_name,
        role_id=item.role_id,
        role_name=item.role_name,
        status=item.status,
        id_parent_user=item.id_parent_user,
        children=[_recommended_hierarchy_node_schema(child) for child in item.children],
    )


@router.get("/units/tree", response_model=UnitTreeResponse)
@router.get("/units/tree/", response_model=UnitTreeResponse, include_in_schema=False)
async def get_units_tree(
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UnitTreeResponse:
    async with uow:
        service = UnitService(uow.units, uow.users)
        items = await service.get_tree(current_user=current_user)

    return UnitTreeResponse(data=UnitTreeData(items=[_unit_node_schema(item) for item in items]))


@router.get("/units/recommended-tree", response_model=RecommendedHierarchyResponse)
@router.get("/units/recommended-tree/", response_model=RecommendedHierarchyResponse, include_in_schema=False)
async def get_recommended_units_tree(
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> RecommendedHierarchyResponse:
    async with uow:
        service = UnitService(uow.units, uow.users)
        items = await service.get_recommended_tree(current_user=current_user)

    return RecommendedHierarchyResponse(
        data=RecommendedHierarchyData(items=[_recommended_hierarchy_node_schema(item) for item in items])
    )


@router.post("/units", response_model=UnitMutationResponse)
async def create_unit(
    payload: CreateUnitRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UnitMutationResponse:
    async with uow:
        service = UnitService(uow.units, uow.users)
        item = await service.create_unit(
            current_user=current_user,
            name=payload.name,
            id_parent=payload.id_parent,
        )

    return UnitMutationResponse(data=_unit_node_schema(item))


@router.patch("/units/{unit_id}", response_model=UnitMutationResponse)
async def update_unit(
    payload: UpdateUnitRequest,
    unit_id: int = Path(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UnitMutationResponse:
    async with uow:
        service = UnitService(uow.units, uow.users)
        item = await service.update_unit(
            current_user=current_user,
            unit_id=unit_id,
            name=payload.name,
            is_active=payload.is_active,
        )

    return UnitMutationResponse(data=_unit_node_schema(item))


@router.get("/units/{unit_id}/members", response_model=UnitMembersResponse)
async def list_unit_members(
    unit_id: int = Path(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UnitMembersResponse:
    async with uow:
        service = UnitService(uow.units, uow.users)
        items = await service.list_members(current_user=current_user, unit_id=unit_id)

    return UnitMembersResponse(data=UnitMembersData(items=[_unit_member_schema(item) for item in items]))


@router.post("/units/{unit_id}/members", response_model=UnitMemberResponse)
async def add_unit_member(
    payload: AddUnitMemberRequest,
    unit_id: int = Path(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UnitMemberResponse:
    async with uow:
        service = UnitService(uow.units, uow.users)
        item = await service.add_member(
            current_user=current_user,
            unit_id=unit_id,
            user_id=payload.user_id,
        )

    return UnitMemberResponse(data=_unit_member_schema(item))


@router.delete("/units/{unit_id}/members/{user_id}", status_code=204)
async def remove_unit_member(
    unit_id: int = Path(..., ge=1),
    user_id: str = Path(..., min_length=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> Response:
    async with uow:
        service = UnitService(uow.units, uow.users)
        await service.remove_member(
            current_user=current_user,
            unit_id=unit_id,
            user_id=user_id,
        )
    return Response(status_code=204)


@router.get("/units/available-users", response_model=AvailableUnitUsersResponse)
@router.get("/units/available-users/", response_model=AvailableUnitUsersResponse, include_in_schema=False)
async def list_available_users_for_unit(
    unit_id: int | None = Query(default=None, ge=1),
    search: str | None = Query(default=None, min_length=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> AvailableUnitUsersResponse:
    async with uow:
        service = UnitService(uow.units, uow.users)
        items = await service.list_available_users_for_unit(
            current_user=current_user,
            unit_id=unit_id,
            search=search,
        )

    return AvailableUnitUsersResponse(
        data=AvailableUnitUsersData(items=[_available_user_schema(item) for item in items])
    )
