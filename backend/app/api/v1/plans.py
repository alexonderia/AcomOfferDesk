from __future__ import annotations

from decimal import Decimal
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.api.dependencies import get_current_user, get_uow
from app.core.uow import UnitOfWork
from app.domain.policies import CurrentUser
from app.schemas.links import Link, LinkSet
from app.schemas.plans import (
    PlanDashboardDataSchema,
    PlanDashboardResponse,
    PlanDashboardSummarySchema,
    PlanRequestStatsSchema,
    PlanRequestStatsDataSchema,
    PlanRequestStatsResponse,
    PlanDelegateCandidateSchema,
    PlanDelegateCandidatesDataSchema,
    PlanDelegateCandidatesResponse,
    PlanDelegateRequest,
    PlanDeleteDataSchema,
    PlanDeleteResponse,
    PlanMutationDataSchema,
    PlanMutationResponse,
    PlanOptionSchema,
    PlanOptionsDataSchema,
    PlanOptionsResponse,
    PlanRootCreateRequest,
    PlanSubplanCreateRequest,
    PlanSummaryDataSchema,
    PlanSummaryResponse,
    PlanTreeDataSchema,
    PlanTreeNodeSchema,
    PlanTreeResponse,
    PlanUpdateRequest,
)
from app.services.plans import (
    PlanDashboardSummary,
    PlanNodeActions,
    PlanOption,
    PlanRequestStats,
    PlanService,
    PlanTreeNode,
    format_month_period,
    parse_month_period,
)

router = APIRouter()


def _to_float(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01")))


def _map_actions(actions: PlanNodeActions):
    return {
        "create_child_plan": actions.create_child_plan,
        "create_subplan": actions.create_subplan,
        "delegate_plan": actions.delegate_plan,
        "edit_plan": actions.edit_plan,
        "delete_child_plan": actions.delete_child_plan,
        "activate_plan": actions.activate_plan,
        "close_plan": actions.close_plan,
        "view_plan": actions.view_plan,
    }


def _map_tree_node(node: PlanTreeNode) -> PlanTreeNodeSchema:
    return PlanTreeNodeSchema(
        plan_id=node.plan_id,
        plan_name=node.plan_name,
        id_parent_plan=node.id_parent_plan,
        user_id=node.user_id,
        user_name=node.user_name,
        user_role=node.user_role,
        parent_user_id_snapshot=node.parent_user_id_snapshot,
        period_start=node.period_start,
        period_end=node.period_end,
        plan_amount=_to_float(node.plan_amount),
        delegated_amount=_to_float(node.delegated_amount),
        personal_plan_amount=_to_float(node.personal_plan_amount),
        unallocated_amount=_to_float(node.unallocated_amount),
        fact_amount_self=_to_float(node.fact_amount_self),
        fact_amount_subtree=_to_float(node.fact_amount_subtree),
        period_fact_amount=_to_float(node.period_fact_amount),
        period_progress_percent=_to_float(node.period_progress_percent),
        in_progress_requests_count=node.in_progress_requests_count,
        remaining_amount=_to_float(node.remaining_amount),
        progress_percent=_to_float(node.progress_percent),
        available_actions=_map_actions(node.available_actions),
        children=[_map_tree_node(child) for child in node.children],
    )


def _map_summary(summary: PlanDashboardSummary) -> PlanDashboardSummarySchema:
    return PlanDashboardSummarySchema(
        total_plan_amount=_to_float(summary.total_plan_amount),
        total_fact_amount=_to_float(summary.total_fact_amount),
        total_period_fact_amount=_to_float(summary.total_period_fact_amount),
        total_remaining_amount=_to_float(summary.total_remaining_amount),
        total_progress_percent=_to_float(summary.total_progress_percent),
        total_period_progress_percent=_to_float(summary.total_period_progress_percent),
    )


def _map_request_stats(stats: PlanRequestStats) -> PlanRequestStatsSchema:
    return PlanRequestStatsSchema(
        total_requests=stats.total_requests,
        distributed_requests=stats.distributed_requests,
        unallocated_requests=stats.unallocated_requests,
        request_fact_amount=_to_float(stats.request_fact_amount),
        unallocated_amount=_to_float(stats.unallocated_amount),
        completion_percent=_to_float(stats.completion_percent),
    )


def _map_mutation(plan) -> PlanMutationDataSchema:
    return PlanMutationDataSchema(
        plan_id=plan.id,
        plan_name=plan.name,
        id_parent_plan=plan.id_parent_plan,
        user_id=plan.id_user,
        parent_user_id_snapshot=plan.id_parent_user_snapshot,
        period_start=plan.period_start,
        period_end=plan.period_end,
        plan_amount=_to_float(Decimal(str(plan.plan_amount))),
    )


def _map_option(item: PlanOption) -> PlanOptionSchema:
    return PlanOptionSchema(
        plan_id=item.plan_id,
        plan_name=item.plan_name,
        user_id=item.user_id,
        user_name=item.user_name,
        user_role=item.user_role,
        period_start=item.period_start,
        period_end=item.period_end,
        is_closed=item.is_closed,
    )


def _build_service(uow: UnitOfWork) -> PlanService:
    return PlanService(
        plans=uow.economy_plans,
        users=uow.users,
        requests=uow.requests,
    )


@router.get("/plans", response_model=PlanDashboardResponse)
async def get_plan_dashboard(
    period: str | None = Query(default=None, min_length=7, max_length=7),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> PlanDashboardResponse:
    if date_from is not None or date_to is not None:
        if date_from is None or date_to is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Both date_from and date_to are required",
            )
    elif period is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either period or date_from/date_to must be provided",
        )

    async with uow:
        service = _build_service(uow)
        if date_from is not None and date_to is not None:
            dashboard = await service.get_dashboard_plan_tab_by_range(
                date_from=date_from,
                date_to=date_to,
                current_user=current_user,
            )
        else:
            dashboard = await service.get_dashboard_plan_tab(
                period=period or "",
                current_user=current_user,
            )

    return PlanDashboardResponse(
        data=PlanDashboardDataSchema(
            period=dashboard.period,
            period_start=dashboard.period_start,
            period_end=dashboard.period_end,
            can_create_root_plan=dashboard.can_create_root_plan,
            root_plan_exists=dashboard.root_plan_exists,
            summary=_map_summary(dashboard.summary),
            request_stats=_map_request_stats(dashboard.request_stats),
            tree=(_map_tree_node(dashboard.tree) if dashboard.tree else None),
            trees=[_map_tree_node(item) for item in dashboard.trees],
        ),
        _links=LinkSet(
            self=Link(
                href=(
                    f"/api/v1/plans?date_from={date_from.isoformat()}&date_to={date_to.isoformat()}"
                    if date_from is not None and date_to is not None
                    else f"/api/v1/plans?period={period}"
                ),
                method="GET",
            )
        ),
    )


@router.get("/plans/request-stats", response_model=PlanRequestStatsResponse)
async def get_plan_request_stats(
    period: str | None = Query(default=None, min_length=7, max_length=7),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    plan_id: int | None = Query(default=None, ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> PlanRequestStatsResponse:
    if date_from is not None or date_to is not None:
        if date_from is None or date_to is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Both date_from and date_to are required",
            )
        period_start = date_from
        period_end = date_to
    elif period is not None:
        period_start, period_end = parse_month_period(period)
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either period or date_from/date_to must be provided",
        )

    async with uow:
        service = _build_service(uow)
        stats = await service.get_request_stats(
            period_start=period_start,
            period_end=period_end,
            plan_id=plan_id,
            current_user=current_user,
        )

    query_parts = [f"date_from={period_start.isoformat()}", f"date_to={period_end.isoformat()}"]
    if plan_id is not None:
        query_parts.append(f"plan_id={plan_id}")
    query = "&".join(query_parts)
    return PlanRequestStatsResponse(
        data=PlanRequestStatsDataSchema(
            period_start=period_start,
            period_end=period_end,
            plan_id=plan_id,
            stats=_map_request_stats(stats),
        ),
        _links=LinkSet(
            self=Link(
                href=f"/api/v1/plans/request-stats?{query}",
                method="GET",
            )
        ),
    )


@router.get("/plans/tree", response_model=PlanTreeResponse)
async def get_plan_tree(
    period: str = Query(..., min_length=7, max_length=7),
    root_user_id: str = Query(..., min_length=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> PlanTreeResponse:
    async with uow:
        service = _build_service(uow)
        tree = await service.get_plan_tree(
            period=period,
            root_user_id=root_user_id,
            current_user=current_user,
        )
        period_start, period_end = parse_month_period(period)

    return PlanTreeResponse(
        data=PlanTreeDataSchema(
            period=format_month_period(period_start),
            period_start=period_start,
            period_end=period_end,
            tree=_map_tree_node(tree),
        ),
        _links=LinkSet(self=Link(href=f"/api/v1/plans/tree?period={period}&root_user_id={root_user_id}", method="GET")),
    )


@router.get("/plans/my-summary", response_model=PlanSummaryResponse)
async def get_my_plan_summary(
    period: str = Query(..., min_length=7, max_length=7),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> PlanSummaryResponse:
    async with uow:
        service = _build_service(uow)
        summary = await service.get_my_plan_summary(period=period, current_user=current_user)
        period_start, period_end = parse_month_period(period)

    return PlanSummaryResponse(
        data=PlanSummaryDataSchema(
            period=format_month_period(period_start),
            period_start=period_start,
            period_end=period_end,
            summary=_map_summary(summary),
        ),
        _links=LinkSet(self=Link(href=f"/api/v1/plans/my-summary?period={period}", method="GET")),
    )


@router.get("/plans/delegate-candidates", response_model=PlanDelegateCandidatesResponse)
async def list_delegate_candidates(
    parent_plan_id: int = Query(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> PlanDelegateCandidatesResponse:
    async with uow:
        service = _build_service(uow)
        candidates = await service.list_delegate_candidates(
            parent_plan_id=parent_plan_id,
            current_user=current_user,
        )

    return PlanDelegateCandidatesResponse(
        data=PlanDelegateCandidatesDataSchema(
            parent_plan_id=parent_plan_id,
            items=[
                PlanDelegateCandidateSchema(
                    user_id=item.user_id,
                    full_name=item.full_name,
                    role_name=item.role_name,
                    has_plan_for_period=item.has_plan_for_period,
                    existing_plan_id=item.existing_plan_id,
                )
                for item in candidates
            ],
        ),
        _links=LinkSet(
            self=Link(
                href=f"/api/v1/plans/delegate-candidates?parent_plan_id={parent_plan_id}",
                method="GET",
            ),
        ),
    )


@router.get("/plans/options", response_model=PlanOptionsResponse)
async def list_plan_options(
    period: str | None = Query(default=None, min_length=7, max_length=7),
    owner_user_id: str | None = Query(default=None, min_length=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> PlanOptionsResponse:
    async with uow:
        service = _build_service(uow)
        items = await service.list_plan_options(
            period=period,
            owner_user_id=owner_user_id,
            current_user=current_user,
        )

    return PlanOptionsResponse(
        data=PlanOptionsDataSchema(
            period=period or "",
            items=[_map_option(item) for item in items],
        ),
        _links=LinkSet(
            self=Link(
                href=(
                    f"/api/v1/plans/options?owner_user_id={owner_user_id}"
                    if owner_user_id
                    else (f"/api/v1/plans/options?period={period}" if period else "/api/v1/plans/options")
                ),
                method="GET",
            )
        ),
    )


@router.post("/plans/root", response_model=PlanMutationResponse)
async def create_root_plan(
    payload: PlanRootCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> PlanMutationResponse:
    async with uow:
        service = _build_service(uow)
        plan = await service.create_root_plan(
            period=payload.period,
            period_start=payload.period_start,
            period_end=payload.period_end,
            name=payload.name,
            plan_amount=payload.plan_amount,
            current_user=current_user,
        )

    return PlanMutationResponse(
        data=_map_mutation(plan),
        _links=LinkSet(self=Link(href="/api/v1/plans/root", method="POST")),
    )


@router.post("/plans/subplan", response_model=PlanMutationResponse)
async def create_subplan(
    payload: PlanSubplanCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> PlanMutationResponse:
    async with uow:
        service = _build_service(uow)
        plan = await service.create_subplan(
            parent_plan_id=payload.parent_plan_id,
            name=payload.name,
            period_start=payload.period_start,
            period_end=payload.period_end,
            child_user_id=payload.child_user_id,
            plan_amount=payload.plan_amount,
            current_user=current_user,
        )

    return PlanMutationResponse(
        data=_map_mutation(plan),
        _links=LinkSet(self=Link(href="/api/v1/plans/subplan", method="POST")),
    )


@router.post("/plans/delegate", response_model=PlanMutationResponse)
async def delegate_plan(
    payload: PlanDelegateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> PlanMutationResponse:
    async with uow:
        service = _build_service(uow)
        plan = await service.delegate_plan(
            parent_plan_id=payload.parent_plan_id,
            child_user_id=payload.child_user_id,
            child_period_start=payload.child_period_start,
            child_plan_amount=payload.child_plan_amount,
            current_user=current_user,
        )

    return PlanMutationResponse(
        data=_map_mutation(plan),
        _links=LinkSet(self=Link(href="/api/v1/plans/delegate", method="POST")),
    )


@router.patch("/plans/{plan_id}", response_model=PlanMutationResponse)
async def update_plan(
    payload: PlanUpdateRequest,
    plan_id: int = Path(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> PlanMutationResponse:
    # status is accepted for backward compatibility but ignored in current schema
    _ = payload.status

    async with uow:
        service = _build_service(uow)
        plan = await service.update_plan(
            plan_id=plan_id,
            new_amount=payload.plan_amount,
            new_name=payload.name,
            new_period_end=payload.period_end,
            current_user=current_user,
        )

    return PlanMutationResponse(
        data=_map_mutation(plan),
        _links=LinkSet(self=Link(href=f"/api/v1/plans/{plan_id}", method="PATCH")),
    )


@router.delete("/plans/{plan_id}", response_model=PlanDeleteResponse)
async def delete_child_plan(
    plan_id: int = Path(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> PlanDeleteResponse:
    async with uow:
        service = _build_service(uow)
        await service.delete_child_plan(plan_id=plan_id, current_user=current_user)

    return PlanDeleteResponse(
        data=PlanDeleteDataSchema(deleted_plan_id=plan_id),
        _links=LinkSet(self=Link(href=f"/api/v1/plans/{plan_id}", method="DELETE")),
    )


@router.post("/plans/{plan_id}/close", response_model=PlanMutationResponse)
async def close_plan(
    plan_id: int = Path(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> PlanMutationResponse:
    async with uow:
        service = _build_service(uow)
        plan = await service.close_plan(plan_id=plan_id, current_user=current_user)

    return PlanMutationResponse(
        data=_map_mutation(plan),
        _links=LinkSet(self=Link(href=f"/api/v1/plans/{plan_id}/close", method="POST")),
    )
