"""Unit tests for dashboard/plan calculation behavior in existing services."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.domain.permissions import PermissionCodes
from app.services.dashboard import DashboardService
from app.services.plans import PlanService, PlanTreeNode, PlanNodeActions


def _dt() -> datetime:
    return datetime(2026, 5, 1, 10, 0, tzinfo=timezone.utc)


class _DashboardUsersRepo:
    async def get_by_id(self, user_id: str):
        if user_id == "econ-1":
            return SimpleNamespace(id="econ-1", id_role=settings.economist_role_id, id_parent="pm-1")
        if user_id == "pm-1":
            return SimpleNamespace(id="pm-1", id_role=settings.project_manager_role_id, id_parent=None)
        return None

    async def list_staff_with_profiles_and_roles_for_dashboard(self, *, role_ids):
        _ = role_ids
        return [
            (
                SimpleNamespace(id="econ-1", id_role=settings.economist_role_id, id_parent=None),
                SimpleNamespace(full_name="Economist One"),
                SimpleNamespace(role="economist"),
            )
        ]

    async def list_active_user_parent_pairs(self):
        return [("econ-1", "pm-1")]


class _DashboardRequestsRepo:
    async def count_in_progress_requests_by_owner(self, *, owner_ids):
        _ = owner_ids
        return [("econ-1", "open", 2), ("econ-1", "review", 1)]

    async def list_unassigned_requests(self, *, operator_role_id, owner_ids):
        _ = (operator_role_id, owner_ids)
        return []

    async def list_in_progress_requests_by_owner_ids(self, *, owner_ids):
        if not owner_ids:
            return []
        return [
            SimpleNamespace(
                id=11,
                description="In progress",
                status="open",
                deadline_at=_dt(),
                created_at=_dt(),
                updated_at=_dt(),
                id_user="econ-1",
            )
        ]

    async def list_closed_requests_with_chosen_offer_by_owner_ids(self, *, owner_ids):
        _ = owner_ids
        return [
            (
                SimpleNamespace(
                    id=100,
                    id_user="econ-1",
                    initial_amount=100.0,
                    final_amount=80.0,
                    closed_at=_dt(),
                    id_plan=10,
                ),
                SimpleNamespace(offer_amount=80.0),
                SimpleNamespace(full_name="Economist One"),
            ),
            (
                SimpleNamespace(
                    id=101,
                    id_user="econ-1",
                    initial_amount=80.0,
                    final_amount=100.0,
                    closed_at=_dt(),
                    id_plan=10,
                ),
                SimpleNamespace(offer_amount=100.0),
                SimpleNamespace(full_name="Economist One"),
            ),
        ]


class _DashboardUserStatusPeriodsRepo:
    async def list_active_for_users(self, *, user_ids):
        _ = user_ids
        return {}

    async def list_next_for_users(self, *, user_ids):
        _ = user_ids
        return []


class _DashboardPlansRepo:
    async def list_by_ids(self, *, plan_ids):
        return [SimpleNamespace(id=plan_id, name=f"Plan {plan_id}") for plan_id in plan_ids]


def test_dashboard_savings_calculation_handles_core_edge_cases():
    service = DashboardService(
        users=_DashboardUsersRepo(),
        requests=_DashboardRequestsRepo(),
        user_status_periods=_DashboardUserStatusPeriodsRepo(),
        plans=_DashboardPlansRepo(),
    )

    assert service._calculate_savings(initial_amount=100, offer_amount=90, final_amount=90) == Decimal("10")
    assert service._calculate_savings(initial_amount=100, offer_amount=120, final_amount=100) == Decimal("20")
    assert service._calculate_savings(initial_amount=0, offer_amount=0, final_amount=0) == Decimal("0")
    assert service._calculate_savings(initial_amount=100, offer_amount=120, final_amount=120) == Decimal("-20")
    assert service._calculate_savings(initial_amount=None, offer_amount=120, final_amount=120) is None


@pytest.mark.asyncio
async def test_responsibility_dashboard_contains_status_counters_and_assigned_requests(make_current_user):
    service = DashboardService(
        users=_DashboardUsersRepo(),
        requests=_DashboardRequestsRepo(),
        user_status_periods=_DashboardUserStatusPeriodsRepo(),
        plans=_DashboardPlansRepo(),
    )
    current_user = make_current_user(
        role_id=settings.superadmin_role_id,
        permissions={
            PermissionCodes.DASHBOARD_PROCESS_READ,
            PermissionCodes.DASHBOARD_SAVINGS_READ,
        },
    )

    dashboard = await service.get_responsibility_dashboard(current_user=current_user)

    assert len(dashboard.tree) == 1
    node = dashboard.tree[0]
    assert node.user_id == "econ-1"
    assert {(item.status, item.count) for item in node.statuses} == {("open", 2), ("review", 1)}
    assert node.in_progress_total == 3
    assert len(dashboard.assigned_requests) == 1
    assert dashboard.assigned_requests[0].owner_user_id == "econ-1"
    assert dashboard.savings.total_closed_requests == 2
    assert dashboard.savings.total_with_savings == 2
    assert dashboard.savings.total_savings_amount == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_responsibility_dashboard_allows_department_dashboard_read_without_global_dashboard_pair(make_current_user):
    service = DashboardService(
        users=_DashboardUsersRepo(),
        requests=_DashboardRequestsRepo(),
        user_status_periods=_DashboardUserStatusPeriodsRepo(),
        plans=_DashboardPlansRepo(),
    )
    current_user = make_current_user(
        user_id="econ-1",
        role_id=settings.economist_role_id,
        permissions={PermissionCodes.DEPARTMENT_DASHBOARD_READ},
    )

    dashboard = await service.get_responsibility_dashboard(current_user=current_user)

    assert len(dashboard.tree) == 1
    assert dashboard.tree[0].user_id == "econ-1"


class _PlanRequestsRepo:
    async def aggregate_plan_request_stats(
        self,
        *,
        owner_ids,
        total_plan_ids,
        distributed_plan_ids,
        total_scope_to_plan_ids,
        total_owner_ids,
        distributed_owner_ids,
        period_start,
        period_end,
    ):
        _ = (
            owner_ids,
            total_plan_ids,
            distributed_plan_ids,
            total_scope_to_plan_ids,
            total_owner_ids,
            distributed_owner_ids,
            period_start,
            period_end,
        )
        return SimpleNamespace(
            total_requests=7,
            distributed_requests=5,
            unallocated_requests=2,
            request_fact_amount=Decimal("300.00"),
            unallocated_amount=Decimal("25.00"),
        )


@pytest.mark.asyncio
async def test_plan_request_stats_aggregate_by_hierarchy_existing_logic():
    service = PlanService(plans=SimpleNamespace(), users=SimpleNamespace(), requests=_PlanRequestsRepo())
    tree = PlanTreeNode(
        plan_id=1,
        plan_name="Root",
        id_parent_plan=None,
        user_id="manager-1",
        user_name="Manager",
        user_role="lead",
        parent_user_id_snapshot=None,
        period_start=_dt().date(),
        period_end=_dt().date(),
        plan_amount=Decimal("500.00"),
        delegated_amount=Decimal("0.00"),
        personal_plan_amount=Decimal("500.00"),
        unallocated_amount=Decimal("500.00"),
        fact_amount_self=Decimal("0.00"),
        fact_amount_subtree=Decimal("0.00"),
        period_fact_amount=Decimal("0.00"),
        period_progress_percent=Decimal("0.00"),
        in_progress_requests_count=0,
        remaining_amount=Decimal("500.00"),
        progress_percent=Decimal("0.00"),
        available_actions=PlanNodeActions(
            create_child_plan=True,
            create_subplan=True,
            delegate_plan=True,
            edit_plan=True,
            delete_child_plan=False,
            activate_plan=False,
            close_plan=False,
            view_plan=True,
        ),
        children=[],
    )

    stats = await service._request_stats_from_trees(
        trees=[tree],
        period_start=_dt().date(),
        period_end=_dt().date(),
    )

    assert stats.total_requests == 7
    assert stats.distributed_requests == 5
    assert stats.unallocated_requests == 2
    assert stats.request_fact_amount == Decimal("300.00")
    assert stats.unallocated_amount == Decimal("25.00")
    assert stats.completion_percent == Decimal("60.00")


def _make_plan_tree_node(*, plan_id: int, user_id: str, children: list[PlanTreeNode] | None = None) -> PlanTreeNode:
    return PlanTreeNode(
        plan_id=plan_id,
        plan_name=f"Plan {plan_id}",
        id_parent_plan=None,
        user_id=user_id,
        user_name=f"User {user_id}",
        user_role="lead",
        parent_user_id_snapshot=None,
        period_start=_dt().date(),
        period_end=_dt().date(),
        plan_amount=Decimal("200.00"),
        delegated_amount=Decimal("0.00"),
        personal_plan_amount=Decimal("200.00"),
        unallocated_amount=Decimal("200.00"),
        fact_amount_self=Decimal("0.00"),
        fact_amount_subtree=Decimal("0.00"),
        period_fact_amount=Decimal("0.00"),
        period_progress_percent=Decimal("0.00"),
        in_progress_requests_count=0,
        remaining_amount=Decimal("200.00"),
        progress_percent=Decimal("0.00"),
        available_actions=PlanNodeActions(
            create_child_plan=True,
            create_subplan=True,
            delegate_plan=True,
            edit_plan=True,
            delete_child_plan=False,
            activate_plan=False,
            close_plan=False,
            view_plan=True,
        ),
        children=children or [],
    )


@pytest.mark.asyncio
async def test_get_request_stats_for_selected_plan_uses_attached_plan_ids(make_current_user):
    captured: dict[str, object] = {}

    class _CapturingPlanRequestsRepo(_PlanRequestsRepo):
        async def aggregate_plan_request_stats(self, **kwargs):
            captured.update(kwargs)
            return await super().aggregate_plan_request_stats(**kwargs)

    child = _make_plan_tree_node(plan_id=2, user_id="econ-1")
    root = _make_plan_tree_node(plan_id=1, user_id="lead-1", children=[child])
    service = PlanService(
        plans=SimpleNamespace(),
        users=SimpleNamespace(),
        requests=_CapturingPlanRequestsRepo(),
    )

    async def _fake_load_relevant_period_plans(*, period_start, period_end):
        _ = (period_start, period_end)
        return [SimpleNamespace(id=1, id_user="lead-1")]

    async def _fake_build_trees_for_roots(
        *,
        period_plans,
        root_plans,
        period_start,
        period_end,
        current_user,
    ):
        _ = (period_plans, root_plans, period_start, period_end, current_user)
        return [root]

    service._load_relevant_period_plans = _fake_load_relevant_period_plans
    service._build_trees_for_roots = _fake_build_trees_for_roots

    current_user = make_current_user(
        role_id=settings.project_manager_role_id,
        permissions={PermissionCodes.DASHBOARD_PLANS_READ},
    )
    await service.get_request_stats(
        period_start=_dt().date(),
        period_end=_dt().date(),
        current_user=current_user,
        plan_id=1,
    )

    assert set(captured["distributed_plan_ids"]) == {1, 2}
    assert captured["distributed_owner_ids"] is None


class _PlanUsersRepo:
    def __init__(self) -> None:
        self._users = {
            "pm-1": SimpleNamespace(
                id="pm-1",
                id_role=settings.project_manager_role_id,
                id_parent=None,
            ),
            "lead-1": SimpleNamespace(
                id="lead-1",
                id_role=settings.lead_economist_role_id,
                id_parent="pm-1",
            ),
            "econ-1": SimpleNamespace(
                id="econ-1",
                id_role=settings.economist_role_id,
                id_parent="lead-1",
            ),
            "econ-2": SimpleNamespace(
                id="econ-2",
                id_role=settings.economist_role_id,
                id_parent="lead-1",
            ),
        }

    async def get_by_id(self, user_id: str):
        return self._users.get(user_id)

    async def list_active_user_parent_pairs(self):
        return [
            ("lead-1", "pm-1"),
            ("econ-1", "lead-1"),
            ("econ-2", "lead-1"),
        ]


@pytest.mark.asyncio
async def test_plan_dashboard_entry_for_economist_is_limited_to_own_delegated_branch(make_current_user):
    service = PlanService(
        plans=SimpleNamespace(),
        users=_PlanUsersRepo(),
        requests=_PlanRequestsRepo(),
    )
    current_user = make_current_user(
        user_id="econ-1",
        role_id=settings.economist_role_id,
        permissions={PermissionCodes.DASHBOARD_PLANS_READ},
    )
    period_plans = [
        SimpleNamespace(id=1, id_user="pm-1", id_parent_plan=None),
        SimpleNamespace(id=2, id_user="econ-1", id_parent_plan=1),
        SimpleNamespace(id=3, id_user="econ-1", id_parent_plan=2),
        SimpleNamespace(id=4, id_user="econ-2", id_parent_plan=1),
    ]

    entry_plans = await service._resolve_dashboard_entry_plans(
        period_plans=period_plans,
        current_user=current_user,
    )

    assert [plan.id for plan in entry_plans] == [2]


@pytest.mark.asyncio
async def test_plan_dashboard_entry_for_economist_uses_module_lead_root_when_present(make_current_user):
    service = PlanService(
        plans=SimpleNamespace(),
        users=_PlanUsersRepo(),
        requests=_PlanRequestsRepo(),
    )
    current_user = make_current_user(
        user_id="econ-1",
        role_id=settings.economist_role_id,
        permissions={PermissionCodes.DASHBOARD_PLANS_READ},
    )
    period_plans = [
        SimpleNamespace(id=1, id_user="pm-1", id_parent_plan=None),
        SimpleNamespace(id=10, id_user="lead-1", id_parent_plan=1),
        SimpleNamespace(id=11, id_user="econ-1", id_parent_plan=10),
        SimpleNamespace(id=12, id_user="econ-2", id_parent_plan=10),
    ]

    entry_plans = await service._resolve_dashboard_entry_plans(
        period_plans=period_plans,
        current_user=current_user,
    )

    assert [plan.id for plan in entry_plans] == [10]


@pytest.mark.asyncio
async def test_plan_dashboard_entry_with_department_plans_read_uses_department_root(make_current_user):
    service = PlanService(
        plans=SimpleNamespace(),
        users=_PlanUsersRepo(),
        requests=_PlanRequestsRepo(),
    )
    current_user = make_current_user(
        user_id="econ-1",
        role_id=settings.economist_role_id,
        permissions={PermissionCodes.DEPARTMENT_PLANS_READ},
    )
    period_plans = [
        SimpleNamespace(id=1, id_user="pm-1", id_parent_plan=None),
        SimpleNamespace(id=10, id_user="lead-1", id_parent_plan=1),
        SimpleNamespace(id=11, id_user="econ-1", id_parent_plan=10),
        SimpleNamespace(id=12, id_user="econ-2", id_parent_plan=10),
    ]

    entry_plans = await service._resolve_dashboard_entry_plans(
        period_plans=period_plans,
        current_user=current_user,
    )

    assert [plan.id for plan in entry_plans] == [1]
