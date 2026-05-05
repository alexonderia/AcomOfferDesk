from __future__ import annotations

import re
from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from app.core.config import settings
from app.domain.exceptions import Conflict, Forbidden, NotFound
from app.domain.policies import CurrentUser, UserPolicy
from app.models.orm_models import EconomyPlan
from app.repositories.economy_plans import EconomyPlanRepository, PlanDistributionRow
from app.repositories.requests import RequestRepository
from app.repositories.users import UserRepository

MONTH_PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def parse_month_period(value: str) -> tuple[date, date]:
    normalized = value.strip()
    if not MONTH_PERIOD_RE.match(normalized):
        raise Conflict("Period must be in YYYY-MM format")
    year = int(normalized[:4])
    month = int(normalized[5:7])
    period_start = date(year, month, 1)
    period_end = date(year, month, monthrange(year, month)[1])
    return period_start, period_end


def format_month_period(period_start: date) -> str:
    return period_start.strftime("%Y-%m")


def month_bounds_for_date(value: date) -> tuple[date, date]:
    month_start = date(value.year, value.month, 1)
    month_end = date(value.year, value.month, monthrange(value.year, value.month)[1])
    return month_start, month_end


def normalize_amount(value: Decimal | float | int | str) -> Decimal:
    decimal_value = Decimal(str(value))
    return decimal_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def normalize_plan_name(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise Conflict("Plan name is required")
    return normalized


def percent(value: Decimal, total: Decimal) -> Decimal:
    if total == 0:
        return Decimal("0.00")
    return ((value / total) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class PlanNodeActions:
    create_child_plan: bool
    create_subplan: bool
    delegate_plan: bool
    edit_plan: bool
    delete_child_plan: bool
    activate_plan: bool
    close_plan: bool
    view_plan: bool = True


@dataclass
class PlanTreeNode:
    plan_id: int
    plan_name: str
    id_parent_plan: int | None
    user_id: str
    user_name: str
    user_role: str
    parent_user_id_snapshot: str | None
    period_start: date
    period_end: date
    plan_amount: Decimal
    delegated_amount: Decimal
    personal_plan_amount: Decimal
    unallocated_amount: Decimal
    fact_amount_self: Decimal
    fact_amount_subtree: Decimal
    period_fact_amount: Decimal
    period_progress_percent: Decimal
    in_progress_requests_count: int
    remaining_amount: Decimal
    progress_percent: Decimal
    available_actions: PlanNodeActions
    children: list["PlanTreeNode"] = field(default_factory=list)


@dataclass(frozen=True)
class PlanDashboardSummary:
    total_plan_amount: Decimal
    total_fact_amount: Decimal
    total_period_fact_amount: Decimal
    total_remaining_amount: Decimal
    total_progress_percent: Decimal
    total_period_progress_percent: Decimal


@dataclass(frozen=True)
class PlanDashboardData:
    period: str
    period_start: date
    period_end: date
    can_create_root_plan: bool
    root_plan_exists: bool
    summary: PlanDashboardSummary
    request_stats: "PlanRequestStats"
    tree: PlanTreeNode | None
    trees: list[PlanTreeNode] = field(default_factory=list)


@dataclass(frozen=True)
class PlanDelegateCandidate:
    user_id: str
    full_name: str | None
    role_name: str
    has_plan_for_period: bool
    existing_plan_id: int | None


@dataclass(frozen=True)
class PlanOption:
    plan_id: int
    plan_name: str
    user_id: str
    user_name: str
    user_role: str
    period_start: date
    period_end: date
    is_closed: bool


@dataclass(frozen=True)
class PlanRequestStats:
    total_requests: int
    distributed_requests: int
    unallocated_requests: int
    request_fact_amount: Decimal
    unallocated_amount: Decimal
    completion_percent: Decimal


class PlanService:
    def __init__(
        self,
        plans: EconomyPlanRepository,
        users: UserRepository,
        requests: RequestRepository,
    ):
        self._plans = plans
        self._users = users
        self._requests = requests

    async def create_root_plan(
        self,
        *,
        period: str | None,
        period_start: date | None,
        period_end: date | None,
        name: str,
        plan_amount: Decimal | float | int | str,
        current_user: CurrentUser,
    ) -> EconomyPlan:
        UserPolicy.ensure_can_view_plan(current_user)
        if current_user.role_id not in {settings.superadmin_role_id, settings.project_manager_role_id}:
            raise Forbidden("Only superadmin and project manager can create root plan")

        plan_start, plan_end, _month_start, _month_end = self._resolve_period_bounds(
            period=period,
            period_start=period_start,
            period_end=period_end,
        )

        normalized_name = normalize_plan_name(name)
        existing_identical = await self._plans.exists_identical_plan(
            user_id=current_user.user_id,
            parent_plan_id=None,
            name=normalized_name,
            period_start=plan_start,
            period_end=plan_end,
        )
        if existing_identical:
            raise Conflict("Identical root plan already exists for selected period")

        normalized_amount = normalize_amount(plan_amount)
        if normalized_amount < 0:
            raise Conflict("Plan amount cannot be negative")

        return await self._plans.create(
            name=normalized_name,
            user_id=current_user.user_id,
            parent_plan_id=None,
            parent_user_id_snapshot=None,
            period_start=plan_start,
            period_end=plan_end,
            plan_amount=normalized_amount,
        )

    async def create_subplan(
        self,
        *,
        parent_plan_id: int,
        name: str,
        plan_amount: Decimal | float | int | str,
        period_start: date | None,
        period_end: date | None,
        child_user_id: str | None,
        current_user: CurrentUser,
    ) -> EconomyPlan:
        UserPolicy.ensure_can_view_plan(current_user)
        normalized_amount = normalize_amount(plan_amount)
        if normalized_amount <= Decimal("0.00"):
            raise Conflict("Subplan amount must be greater than zero")

        parent_plan = await self._plans.get_by_id_for_update(plan_id=parent_plan_id)
        if parent_plan is None:
            raise NotFound("Parent plan not found")
        self._ensure_plan_is_open(parent_plan)
        await self._ensure_can_manage_node(current_user=current_user, plan_owner_user_id=parent_plan.id_user)
        await self._ensure_owner_has_direct_subordinates(parent_plan.id_user)
        await self._ensure_available_amount(parent_plan=parent_plan, requested_amount=normalized_amount)

        child_period_start, child_period_end = self._resolve_child_period_bounds(
            parent_plan=parent_plan,
            candidate_start=period_start,
            candidate_end=period_end,
        )
        target_user_id = parent_plan.id_user
        target_parent_snapshot = parent_plan.id_parent_user_snapshot
        if child_user_id is not None and child_user_id != parent_plan.id_user:
            child_user = await self._users.get_by_id(child_user_id)
            if child_user is None:
                raise NotFound("Child user not found")
            if child_user.id_parent != parent_plan.id_user:
                raise Forbidden("Subplan assignee must be a direct subordinate of parent plan owner")
            target_user_id = child_user.id
            target_parent_snapshot = parent_plan.id_user
        normalized_name = normalize_plan_name(name)
        exists_identical = await self._plans.exists_identical_plan(
            user_id=target_user_id,
            parent_plan_id=parent_plan.id,
            name=normalized_name,
            period_start=child_period_start,
            period_end=child_period_end,
        )
        if exists_identical:
            raise Conflict("Identical subplan already exists for selected period")

        return await self._plans.create(
            name=normalized_name,
            user_id=target_user_id,
            parent_plan_id=parent_plan.id,
            parent_user_id_snapshot=target_parent_snapshot,
            period_start=child_period_start,
            period_end=child_period_end,
            plan_amount=normalized_amount,
        )

    async def delegate_plan(
        self,
        *,
        parent_plan_id: int,
        child_user_id: str,
        child_plan_amount: Decimal | float | int | str,
        child_period_start: date | None,
        current_user: CurrentUser,
    ) -> EconomyPlan:
        UserPolicy.ensure_can_view_plan(current_user)
        normalized_amount = normalize_amount(child_plan_amount)
        if normalized_amount <= Decimal("0.00"):
            raise Conflict("Delegated plan amount must be greater than zero")

        parent_plan = await self._plans.get_by_id_for_update(plan_id=parent_plan_id)
        if parent_plan is None:
            raise NotFound("Parent plan not found")
        self._ensure_plan_is_open(parent_plan)
        await self._ensure_can_manage_node(current_user=current_user, plan_owner_user_id=parent_plan.id_user)
        await self._ensure_owner_has_direct_subordinates(parent_plan.id_user)

        child_user = await self._users.get_by_id(child_user_id)
        if child_user is None:
            raise NotFound("Child user not found")
        if child_user.id_parent != parent_plan.id_user:
            raise Forbidden("Plan can be delegated only to direct subordinate")

        await self._ensure_available_amount(parent_plan=parent_plan, requested_amount=normalized_amount)

        delegated_period_start = self._resolve_child_period_start(
            parent_plan=parent_plan,
            candidate_start=child_period_start,
        )
        delegated_period_end = parent_plan.period_end
        delegated_name = normalize_plan_name(parent_plan.name)
        exists_identical = await self._plans.exists_identical_plan(
            user_id=child_user_id,
            parent_plan_id=parent_plan.id,
            name=delegated_name,
            period_start=delegated_period_start,
            period_end=delegated_period_end,
        )
        if exists_identical:
            raise Conflict("Identical delegated plan already exists for selected period")

        return await self._plans.create(
            name=delegated_name,
            user_id=child_user_id,
            parent_plan_id=parent_plan.id,
            parent_user_id_snapshot=parent_plan.id_user,
            period_start=delegated_period_start,
            period_end=delegated_period_end,
            plan_amount=normalized_amount,
        )

    async def update_plan(
        self,
        *,
        plan_id: int,
        new_amount: Decimal | float | int | str | None,
        new_name: str | None,
        new_period_end: date | None,
        current_user: CurrentUser,
    ) -> EconomyPlan:
        UserPolicy.ensure_can_view_plan(current_user)
        if new_amount is None and new_name is None and new_period_end is None:
            raise Conflict("Nothing to update")

        plan = await self._plans.get_by_id_for_update(plan_id=plan_id)
        if plan is None:
            raise NotFound("Plan not found")
        await self._ensure_can_manage_node(current_user=current_user, plan_owner_user_id=plan.id_user)
        self._ensure_plan_is_open(plan)

        normalized_amount: Decimal | None = None
        if new_amount is not None:
            normalized_amount = normalize_amount(new_amount)
            if normalized_amount < 0:
                raise Conflict("Plan amount cannot be negative")

        normalized_name = normalize_plan_name(new_name) if new_name is not None else None
        normalized_period_end = None
        if new_period_end is not None:
            if new_period_end < plan.period_start:
                raise Conflict("Plan period end cannot be earlier than period start")
            normalized_period_end = new_period_end
        await self._plans.update(
            plan=plan,
            name=normalized_name,
            plan_amount=normalized_amount,
            period_end=normalized_period_end,
        )
        return plan

    async def delete_child_plan(
        self,
        *,
        plan_id: int,
        current_user: CurrentUser,
    ) -> None:
        UserPolicy.ensure_can_view_plan(current_user)
        plan = await self._plans.get_by_id_for_update(plan_id=plan_id)
        if plan is None:
            raise NotFound("Plan not found")

        await self._ensure_can_manage_node(current_user=current_user, plan_owner_user_id=plan.id_user)
        self._ensure_plan_is_open(plan)
        child_nodes = await self._plans.list_children(parent_plan_id=plan.id)
        if child_nodes:
            raise Conflict("Cannot delete plan that has subplans or delegated children")
        delegated_sum = await self._plans.sum_children_plan_amount(parent_plan_id=plan.id)
        if delegated_sum > Decimal("0.00"):
            raise Conflict("Cannot delete plan with delegated distribution")
        active_fact = await self._plans.aggregate_active_request_facts_by_plan_ids(plan_ids=[plan.id])
        fact_amount = active_fact.get(plan.id, Decimal("0.00"))
        persisted_fact_amount = Decimal(str(plan.fact_amount or 0))
        if fact_amount > Decimal("0.00") or persisted_fact_amount > Decimal("0.00"):
            raise Conflict("Cannot delete plan with completed requests")
        await self._plans.delete(plan=plan)

    async def close_plan(
        self,
        *,
        plan_id: int,
        current_user: CurrentUser,
    ) -> EconomyPlan:
        UserPolicy.ensure_can_view_plan(current_user)
        plan = await self._plans.get_by_id_for_update(plan_id=plan_id)
        if plan is None:
            raise NotFound("Plan not found")
        await self._ensure_can_manage_node(current_user=current_user, plan_owner_user_id=plan.id_user)

        if self._is_plan_closed(plan):
            raise Conflict("Plan is already closed")

        close_date = date.today()
        subtree = await self._plans.list_subtree(root_plan_id=plan.id)
        if any(node.period_start > close_date for node in subtree):
            raise Conflict("Cannot close plan before period start of one of child nodes")

        await self._plans.close_subtree(root_plan_id=plan.id, closed_at=close_date)
        plan.period_end = close_date
        return plan

    async def get_plan_tree(
        self,
        *,
        period: str,
        root_user_id: str,
        current_user: CurrentUser,
    ) -> PlanTreeNode:
        UserPolicy.ensure_can_view_plan(current_user)
        month_start, month_end = parse_month_period(period)
        period_plans = await self._plans.list_by_month_bucket(month_start=month_start, month_end=month_end)
        if not period_plans:
            raise NotFound("No plans found for selected period")

        root_plans = self._find_entry_plans_for_user(period_plans=period_plans, user_id=root_user_id)
        if not root_plans:
            raise NotFound("User plan branch not found for selected period")

        await self._ensure_can_view_root(current_user=current_user, requested_root_user_id=root_user_id)
        trees = await self._build_trees_for_roots(
            period_plans=period_plans,
            root_plans=root_plans,
            period_start=month_start,
            period_end=month_end,
            current_user=current_user,
        )
        if not trees:
            raise NotFound("User plan branch not found for selected period")
        return trees[0]

    async def get_my_plan_summary(
        self,
        *,
        period: str,
        current_user: CurrentUser,
    ) -> PlanDashboardSummary:
        UserPolicy.ensure_can_view_plan(current_user)
        dashboard = await self.get_dashboard_plan_tab(period=period, current_user=current_user)
        return dashboard.summary

    async def get_request_stats(
        self,
        *,
        period_start: date,
        period_end: date,
        current_user: CurrentUser,
        plan_id: int | None = None,
    ) -> PlanRequestStats:
        UserPolicy.ensure_can_view_plan(current_user)
        if period_start > period_end:
            raise Conflict("date_from must be less than or equal to date_to")

        period_plans = await self._load_relevant_period_plans(
            period_start=period_start,
            period_end=period_end,
        )
        if not period_plans:
            return PlanRequestStats(
                total_requests=0,
                distributed_requests=0,
                unallocated_requests=0,
                request_fact_amount=Decimal("0.00"),
                unallocated_amount=Decimal("0.00"),
                completion_percent=Decimal("0.00"),
            )

        if plan_id is not None:
            plan_by_id = {plan.id: plan for plan in period_plans}
            selected_plan = plan_by_id.get(plan_id)
            if selected_plan is None:
                raise NotFound("Plan not found for selected period")
            await self._ensure_can_manage_node(
                current_user=current_user,
                plan_owner_user_id=selected_plan.id_user,
            )
            trees = await self._build_trees_for_roots(
                period_plans=period_plans,
                root_plans=[selected_plan],
                period_start=period_start,
                period_end=period_end,
                current_user=current_user,
            )
            return await self._request_stats_from_trees(
                trees=trees,
                period_start=period_start,
                period_end=period_end,
            )

        my_entry_plans = self._find_entry_plans_for_user(
            period_plans=period_plans,
            user_id=current_user.user_id,
        )
        if not my_entry_plans:
            return PlanRequestStats(
                total_requests=0,
                distributed_requests=0,
                unallocated_requests=0,
                request_fact_amount=Decimal("0.00"),
                unallocated_amount=Decimal("0.00"),
                completion_percent=Decimal("0.00"),
            )
        trees = await self._build_trees_for_roots(
            period_plans=period_plans,
            root_plans=my_entry_plans,
            period_start=period_start,
            period_end=period_end,
            current_user=current_user,
        )
        return await self._request_stats_from_trees(
            trees=trees,
            period_start=period_start,
            period_end=period_end,
        )

    async def get_dashboard_plan_tab(
        self,
        *,
        period: str,
        current_user: CurrentUser,
    ) -> PlanDashboardData:
        UserPolicy.ensure_can_view_plan(current_user)
        month_start, month_end = parse_month_period(period)
        period_plans = await self._load_relevant_period_plans(
            period_start=month_start,
            period_end=month_end,
        )
        my_entry_plans = self._find_entry_plans_for_user(period_plans=period_plans, user_id=current_user.user_id)

        can_create_root_plan = current_user.role_id in {settings.superadmin_role_id, settings.project_manager_role_id}
        if not my_entry_plans:
            empty_summary = PlanDashboardSummary(
                total_plan_amount=Decimal("0.00"),
                total_fact_amount=Decimal("0.00"),
                total_period_fact_amount=Decimal("0.00"),
                total_remaining_amount=Decimal("0.00"),
                total_progress_percent=Decimal("0.00"),
                total_period_progress_percent=Decimal("0.00"),
            )
            return PlanDashboardData(
                period=format_month_period(month_start),
                period_start=month_start,
                period_end=month_end,
                can_create_root_plan=can_create_root_plan,
                root_plan_exists=False,
                summary=empty_summary,
                request_stats=PlanRequestStats(
                    total_requests=0,
                    distributed_requests=0,
                    unallocated_requests=0,
                    request_fact_amount=Decimal("0.00"),
                    unallocated_amount=Decimal("0.00"),
                    completion_percent=Decimal("0.00"),
                ),
                tree=None,
                trees=[],
            )

        trees = await self._build_trees_for_roots(
            period_plans=period_plans,
            root_plans=my_entry_plans,
            period_start=month_start,
            period_end=month_end,
            current_user=current_user,
        )
        summary = await self._summary_from_trees(trees, period_start=month_start, period_end=month_end)
        request_stats = await self._request_stats_from_trees(
            trees=trees,
            period_start=month_start,
            period_end=month_end,
        )
        return PlanDashboardData(
            period=format_month_period(month_start),
            period_start=month_start,
            period_end=month_end,
            can_create_root_plan=can_create_root_plan,
            root_plan_exists=True,
            summary=summary,
            request_stats=request_stats,
            tree=(trees[0] if trees else None),
            trees=trees,
        )

    async def get_dashboard_plan_tab_by_range(
        self,
        *,
        date_from: date,
        date_to: date,
        current_user: CurrentUser,
    ) -> PlanDashboardData:
        UserPolicy.ensure_can_view_plan(current_user)
        if date_from > date_to:
            raise Conflict("date_from must be less than or equal to date_to")

        period_plans = await self._load_relevant_period_plans(
            period_start=date_from,
            period_end=date_to,
        )
        my_entry_plans = self._find_entry_plans_for_user(
            period_plans=period_plans,
            user_id=current_user.user_id,
        )
        can_create_root_plan = current_user.role_id in {
            settings.superadmin_role_id,
            settings.project_manager_role_id,
        }
        if not my_entry_plans:
            empty_summary = PlanDashboardSummary(
                total_plan_amount=Decimal("0.00"),
                total_fact_amount=Decimal("0.00"),
                total_period_fact_amount=Decimal("0.00"),
                total_remaining_amount=Decimal("0.00"),
                total_progress_percent=Decimal("0.00"),
                total_period_progress_percent=Decimal("0.00"),
            )
            return PlanDashboardData(
                period=f"{date_from.isoformat()}..{date_to.isoformat()}",
                period_start=date_from,
                period_end=date_to,
                can_create_root_plan=can_create_root_plan,
                root_plan_exists=False,
                summary=empty_summary,
                request_stats=PlanRequestStats(
                    total_requests=0,
                    distributed_requests=0,
                    unallocated_requests=0,
                    request_fact_amount=Decimal("0.00"),
                    unallocated_amount=Decimal("0.00"),
                    completion_percent=Decimal("0.00"),
                ),
                tree=None,
                trees=[],
            )

        trees = await self._build_trees_for_roots(
            period_plans=period_plans,
            root_plans=my_entry_plans,
            period_start=date_from,
            period_end=date_to,
            current_user=current_user,
        )
        summary = await self._summary_from_trees(trees, period_start=date_from, period_end=date_to)
        request_stats = await self._request_stats_from_trees(
            trees=trees,
            period_start=date_from,
            period_end=date_to,
        )
        return PlanDashboardData(
            period=f"{date_from.isoformat()}..{date_to.isoformat()}",
            period_start=date_from,
            period_end=date_to,
            can_create_root_plan=can_create_root_plan,
            root_plan_exists=True,
            summary=summary,
            request_stats=request_stats,
            tree=(trees[0] if trees else None),
            trees=trees,
        )

    async def _load_relevant_period_plans(
        self,
        *,
        period_start: date,
        period_end: date,
    ) -> list[EconomyPlan]:
        range_plans = await self._plans.list_by_period_start_range(
            range_start=period_start,
            range_end=period_end,
        )
        started_plans = await self._plans.list_started_before_or_on(
            period_end=period_end,
        )
        carry_over_open_plans = [
            plan
            for plan in started_plans
            if (not self._is_plan_closed(plan)) and plan.period_start <= period_end
        ]
        activity_plans = await self._plans.list_by_closed_requests_period(
            period_start=period_start,
            period_end=period_end,
        )
        combined_by_id: dict[int, EconomyPlan] = {
            plan.id: plan
            for plan in [*range_plans, *carry_over_open_plans, *activity_plans]
        }
        if not combined_by_id:
            return []
        return await self._extend_with_missing_ancestors(
            plans=list(combined_by_id.values()),
        )

    async def _extend_with_missing_ancestors(
        self,
        *,
        plans: list[EconomyPlan],
    ) -> list[EconomyPlan]:
        by_id: dict[int, EconomyPlan] = {plan.id: plan for plan in plans}
        missing_parent_ids = {
            plan.id_parent_plan
            for plan in by_id.values()
            if plan.id_parent_plan is not None and plan.id_parent_plan not in by_id
        }
        while missing_parent_ids:
            fetched_parents = await self._plans.list_by_ids(
                plan_ids=list(missing_parent_ids),
            )
            if not fetched_parents:
                break
            for parent_plan in fetched_parents:
                by_id[parent_plan.id] = parent_plan
            missing_parent_ids = {
                plan.id_parent_plan
                for plan in by_id.values()
                if plan.id_parent_plan is not None and plan.id_parent_plan not in by_id
            }
        return sorted(by_id.values(), key=lambda item: item.id)

    async def list_plan_options(
        self,
        *,
        period: str | None,
        owner_user_id: str | None,
        current_user: CurrentUser,
    ) -> list[PlanOption]:
        UserPolicy.ensure_can_view_plan(current_user)
        _ = period
        target_user_id = owner_user_id or current_user.user_id
        user_plans = await self._plans.list_by_user(user_id=target_user_id)
        if not user_plans:
            return []
        open_user_plans = [plan for plan in user_plans if not self._is_plan_closed(plan)]
        if not open_user_plans:
            return []

        users_rows = await self._users.list_by_ids_with_profiles_and_roles(
            user_ids=list({plan.id_user for plan in open_user_plans}),
        )
        user_meta_by_id = {
            user.id: {
                "full_name": (profile.full_name if profile else None),
                "role_name": role.role,
                "id_parent": user.id_parent,
            }
            for user, profile, role in users_rows
        }
        parent_pairs = await self._users.list_active_user_parent_pairs()
        for user_id, parent_id in parent_pairs:
            if user_id not in user_meta_by_id:
                user_meta_by_id[user_id] = {
                    "full_name": None,
                    "role_name": None,
                    "id_parent": parent_id,
                }
        options: list[PlanOption] = []
        for plan in open_user_plans:
            if not self._can_manage_node_sync(
                current_user=current_user,
                plan_owner_user_id=plan.id_user,
                user_meta_by_id=user_meta_by_id,
            ):
                continue
            user_meta = user_meta_by_id.get(plan.id_user, {})
            options.append(
                PlanOption(
                    plan_id=plan.id,
                    plan_name=plan.name,
                    user_id=plan.id_user,
                    user_name=(user_meta.get("full_name") or plan.id_user),
                    user_role=(user_meta.get("role_name") or "unknown"),
                    period_start=plan.period_start,
                    period_end=plan.period_end,
                    is_closed=self._is_plan_closed(plan),
                )
            )
        options.sort(key=lambda item: (item.period_start, item.plan_name.lower(), item.plan_id))
        return options

    async def list_delegate_candidates(
        self,
        *,
        parent_plan_id: int,
        current_user: CurrentUser,
    ) -> list[PlanDelegateCandidate]:
        UserPolicy.ensure_can_view_plan(current_user)
        parent_plan = await self._plans.get_by_id(plan_id=parent_plan_id)
        if parent_plan is None:
            raise NotFound("Parent plan not found")

        await self._ensure_can_manage_node(current_user=current_user, plan_owner_user_id=parent_plan.id_user)
        subordinates = await self._users.list_direct_subordinates_with_profiles_and_roles(
            manager_user_id=parent_plan.id_user,
            include_inactive=False,
        )
        if not subordinates:
            return []

        delegated_children = await self._plans.list_children(parent_plan_id=parent_plan.id)
        delegated_by_user: dict[str, EconomyPlan] = {}
        for child in delegated_children:
            if child.id_user not in delegated_by_user:
                delegated_by_user[child.id_user] = child

        return [
            PlanDelegateCandidate(
                user_id=user.id,
                full_name=(profile.full_name if profile else None),
                role_name=role.role,
                has_plan_for_period=user.id in delegated_by_user,
                existing_plan_id=delegated_by_user[user.id].id if user.id in delegated_by_user else None,
            )
            for user, profile, role in subordinates
        ]

    async def _summary_from_tree(
        self,
        tree: PlanTreeNode,
        *,
        period_start: date,
        period_end: date,
    ) -> PlanDashboardSummary:
        return await self._summary_from_trees([tree], period_start=period_start, period_end=period_end)

    async def _summary_from_trees(
        self,
        trees: list[PlanTreeNode],
        *,
        period_start: date,
        period_end: date,
    ) -> PlanDashboardSummary:
        if not trees:
            return PlanDashboardSummary(
                total_plan_amount=Decimal("0.00"),
                total_fact_amount=Decimal("0.00"),
                total_period_fact_amount=Decimal("0.00"),
                total_remaining_amount=Decimal("0.00"),
                total_progress_percent=Decimal("0.00"),
                total_period_progress_percent=Decimal("0.00"),
            )
        total_plan_amount = sum((tree.plan_amount for tree in trees), Decimal("0.00")).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        total_fact_amount = sum((tree.fact_amount_subtree for tree in trees), Decimal("0.00")).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        total_remaining_amount = sum((tree.remaining_amount for tree in trees), Decimal("0.00")).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        total_progress_percent = percent(total_fact_amount, total_plan_amount)
        tree_plan_ids = self._collect_tree_plan_ids(trees)
        period_fact_by_plan_id = await self._plans.aggregate_closed_request_facts_by_plan_ids(
            plan_ids=tree_plan_ids,
            period_start=period_start,
            period_end=period_end,
        )
        total_period_fact_amount = sum(period_fact_by_plan_id.values(), Decimal("0.00")).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        total_period_progress_percent = percent(total_period_fact_amount, total_plan_amount)
        return PlanDashboardSummary(
            total_plan_amount=total_plan_amount,
            total_fact_amount=total_fact_amount,
            total_period_fact_amount=total_period_fact_amount,
            total_remaining_amount=total_remaining_amount,
            total_progress_percent=total_progress_percent,
            total_period_progress_percent=total_period_progress_percent,
        )

    def _collect_tree_plan_ids(self, trees: list[PlanTreeNode]) -> list[int]:
        plan_ids: set[int] = set()
        stack = list(trees)
        while stack:
            node = stack.pop()
            plan_ids.add(node.plan_id)
            stack.extend(node.children)
        return list(plan_ids)

    async def _request_stats_from_trees(
        self,
        *,
        trees: list[PlanTreeNode],
        period_start: date,
        period_end: date,
    ) -> PlanRequestStats:
        if not trees:
            return PlanRequestStats(
                total_requests=0,
                distributed_requests=0,
                unallocated_requests=0,
                request_fact_amount=Decimal("0.00"),
                unallocated_amount=Decimal("0.00"),
                completion_percent=Decimal("0.00"),
            )
        plan_ids = self._collect_tree_plan_ids(trees)
        owner_ids: set[str] = set()
        stack = list(trees)
        while stack:
            node = stack.pop()
            owner_ids.add(node.user_id)
            stack.extend(node.children)
        aggregated = await self._requests.aggregate_plan_request_stats(
            owner_ids=list(owner_ids),
            plan_ids=plan_ids,
            period_start=period_start,
            period_end=period_end,
        )
        plan_total = sum((tree.plan_amount for tree in trees), Decimal("0.00"))
        completion_percent = percent(aggregated.request_fact_amount, plan_total)
        return PlanRequestStats(
            total_requests=aggregated.total_requests,
            distributed_requests=aggregated.distributed_requests,
            unallocated_requests=aggregated.unallocated_requests,
            request_fact_amount=aggregated.request_fact_amount,
            unallocated_amount=aggregated.unallocated_amount,
            completion_percent=completion_percent,
        )

    async def _build_trees_for_roots(
        self,
        *,
        period_plans: list[EconomyPlan],
        root_plans: list[EconomyPlan],
        period_start: date,
        period_end: date,
        current_user: CurrentUser,
    ) -> list[PlanTreeNode]:
        if not period_plans or not root_plans:
            return []

        by_parent_plan_id = self._group_by_parent_plan_id(period_plans)
        subtree_plan_ids: set[int] = set()
        for root_plan in root_plans:
            subtree_plan_ids.update(
                self._collect_subtree_plan_ids(
                    by_parent_plan_id=by_parent_plan_id,
                    root_plan_id=root_plan.id,
                )
            )

        subtree_plans = [plan for plan in period_plans if plan.id in subtree_plan_ids]
        users_rows = await self._users.list_by_ids_with_profiles_and_roles(
            user_ids=list({plan.id_user for plan in subtree_plans}),
        )
        user_meta_by_id = {
            user.id: {
                "full_name": (profile.full_name if profile else None),
                "role_name": role.role,
                "id_parent": user.id_parent,
            }
            for user, profile, role in users_rows
        }
        parent_pairs = await self._users.list_active_user_parent_pairs()
        for user_id, parent_id in parent_pairs:
            if user_id not in user_meta_by_id:
                user_meta_by_id[user_id] = {
                    "full_name": None,
                    "role_name": None,
                    "id_parent": parent_id,
                }
        managers_with_subordinates = {parent_id for _, parent_id in parent_pairs if parent_id}

        distribution_by_plan_id = await self._plans.fetch_distribution_by_plan_ids(plan_ids=[plan.id for plan in subtree_plans])
        self_fact_by_plan_id = await self._plans.aggregate_active_request_facts_by_plan_ids(plan_ids=[plan.id for plan in subtree_plans])
        in_progress_counts_rows = await self._requests.count_in_progress_requests_by_owner(
            owner_ids=list({plan.id_user for plan in subtree_plans}),
        )
        in_progress_count_by_user_id: dict[str, int] = {}
        for owner_user_id, _status, count in in_progress_counts_rows:
            in_progress_count_by_user_id[owner_user_id] = in_progress_count_by_user_id.get(owner_user_id, 0) + int(count or 0)
        period_fact_by_plan_id = await self._plans.aggregate_closed_request_facts_by_plan_ids(
            plan_ids=[plan.id for plan in subtree_plans],
            period_start=period_start,
            period_end=period_end,
        )

        return [
            self._build_tree_node(
                plan=root_plan,
                by_parent_plan_id=by_parent_plan_id,
                distribution_by_plan_id=distribution_by_plan_id,
                self_fact_by_plan_id=self_fact_by_plan_id,
                in_progress_count_by_user_id=in_progress_count_by_user_id,
                period_fact_by_plan_id=period_fact_by_plan_id,
                user_meta_by_id=user_meta_by_id,
                managers_with_subordinates=managers_with_subordinates,
                current_user=current_user,
            )
            for root_plan in root_plans
        ]

    def _build_tree_node(
        self,
        *,
        plan: EconomyPlan,
        by_parent_plan_id: dict[int | None, list[EconomyPlan]],
        distribution_by_plan_id: dict[int, PlanDistributionRow],
        self_fact_by_plan_id: dict[int, Decimal],
        in_progress_count_by_user_id: dict[str, int],
        period_fact_by_plan_id: dict[int, Decimal],
        user_meta_by_id: dict[str, dict[str, str | None]],
        managers_with_subordinates: set[str],
        current_user: CurrentUser,
    ) -> PlanTreeNode:
        child_plans = by_parent_plan_id.get(plan.id, [])
        child_nodes = [
            self._build_tree_node(
                plan=child,
                by_parent_plan_id=by_parent_plan_id,
                distribution_by_plan_id=distribution_by_plan_id,
                self_fact_by_plan_id=self_fact_by_plan_id,
                in_progress_count_by_user_id=in_progress_count_by_user_id,
                period_fact_by_plan_id=period_fact_by_plan_id,
                user_meta_by_id=user_meta_by_id,
                managers_with_subordinates=managers_with_subordinates,
                current_user=current_user,
            )
            for child in child_plans
        ]

        plan_total = Decimal(str(plan.plan_amount or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        distribution = distribution_by_plan_id.get(plan.id)
        delegated_amount = (
            Decimal(str(distribution.allocated_to_children_amount))
            if distribution is not None
            else sum((child.plan_amount for child in child_nodes), Decimal("0.00"))
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        personal_plan_amount = (
            Decimal(str(distribution.unallocated_amount))
            if distribution is not None
            else (plan_total - delegated_amount)
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        fact_amount_self = self_fact_by_plan_id.get(plan.id, Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        fact_amount_subtree = Decimal(str(plan.fact_amount or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if fact_amount_subtree == Decimal("0.00"):
            fact_amount_subtree = (
                fact_amount_self + sum((child.fact_amount_subtree for child in child_nodes), Decimal("0.00"))
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        remaining_by_fact = (plan_total - fact_amount_subtree).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        delegated_overflow = (plan_total - delegated_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        # Negative remainder is meaningful only when parent plan became lower than
        # already delegated amount to subordinates and they need rebalancing.
        # Overperformance (fact > plan) should not produce negative remainder.
        if delegated_overflow < Decimal("0.00"):
            remaining_amount = delegated_overflow
        else:
            remaining_amount = max(remaining_by_fact, Decimal("0.00"))
        progress_percent = percent(fact_amount_subtree, plan_total)
        period_fact_amount = period_fact_by_plan_id.get(plan.id, Decimal("0.00")).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        period_progress_percent = percent(period_fact_amount, plan_total)

        user_meta = user_meta_by_id.get(plan.id_user, {})
        can_manage = self._can_manage_node_sync(
            current_user=current_user,
            plan_owner_user_id=plan.id_user,
            user_meta_by_id=user_meta_by_id,
        )
        is_closed = self._is_plan_closed(plan)
        has_subordinates = plan.id_user in managers_with_subordinates
        can_create_subplan = can_manage and has_subordinates and not is_closed
        can_delegate = can_manage and has_subordinates and not is_closed
        can_delete = (
            can_manage
            and not is_closed
            and not child_nodes
            and delegated_amount <= Decimal("0.00")
            and fact_amount_self <= Decimal("0.00")
            and fact_amount_subtree <= Decimal("0.00")
        )
        return PlanTreeNode(
            plan_id=plan.id,
            plan_name=plan.name,
            id_parent_plan=plan.id_parent_plan,
            user_id=plan.id_user,
            user_name=(user_meta.get("full_name") or plan.id_user),
            user_role=(user_meta.get("role_name") or "unknown"),
            parent_user_id_snapshot=plan.id_parent_user_snapshot,
            period_start=plan.period_start,
            period_end=plan.period_end,
            plan_amount=plan_total,
            delegated_amount=delegated_amount,
            personal_plan_amount=personal_plan_amount,
            unallocated_amount=personal_plan_amount,
            fact_amount_self=fact_amount_self,
            fact_amount_subtree=fact_amount_subtree,
            period_fact_amount=period_fact_amount,
            period_progress_percent=period_progress_percent,
            in_progress_requests_count=in_progress_count_by_user_id.get(plan.id_user, 0),
            remaining_amount=remaining_amount,
            progress_percent=progress_percent,
            children=child_nodes,
            available_actions=PlanNodeActions(
                create_child_plan=can_create_subplan or can_delegate,
                create_subplan=can_create_subplan,
                delegate_plan=can_delegate,
                edit_plan=can_manage and not is_closed,
                delete_child_plan=can_delete,
                activate_plan=False,
                close_plan=can_manage and not is_closed and plan.period_start <= date.today(),
                view_plan=True,
            ),
        )

    def _group_by_parent_plan_id(self, plans: list[EconomyPlan]) -> dict[int | None, list[EconomyPlan]]:
        grouped: dict[int | None, list[EconomyPlan]] = {}
        for plan in plans:
            grouped.setdefault(plan.id_parent_plan, []).append(plan)
        for items in grouped.values():
            items.sort(key=lambda item: item.id)
        return grouped

    def _collect_subtree_plan_ids(
        self,
        *,
        by_parent_plan_id: dict[int | None, list[EconomyPlan]],
        root_plan_id: int,
    ) -> set[int]:
        collected: set[int] = set()
        stack: list[int] = [root_plan_id]
        while stack:
            plan_id = stack.pop()
            if plan_id in collected:
                continue
            collected.add(plan_id)
            for child in by_parent_plan_id.get(plan_id, []):
                stack.append(child.id)
        return collected

    def _find_entry_plans_for_user(
        self,
        *,
        period_plans: list[EconomyPlan],
        user_id: str,
    ) -> list[EconomyPlan]:
        by_id = {plan.id: plan for plan in period_plans}
        raw_candidates: list[EconomyPlan] = []
        for plan in period_plans:
            if plan.id_user != user_id:
                continue
            if plan.id_parent_plan is None:
                raw_candidates.append(plan)
                continue
            parent = by_id.get(plan.id_parent_plan)
            if parent is None:
                continue
            if parent.id_user != user_id:
                raw_candidates.append(plan)

        candidate_ids = {plan.id for plan in raw_candidates}
        filtered: list[EconomyPlan] = []
        for candidate in raw_candidates:
            cursor_id = candidate.id_parent_plan
            has_candidate_ancestor = False
            visited: set[int] = set()
            while cursor_id is not None and cursor_id not in visited:
                if cursor_id in candidate_ids:
                    has_candidate_ancestor = True
                    break
                visited.add(cursor_id)
                parent = by_id.get(cursor_id)
                cursor_id = parent.id_parent_plan if parent else None
            if not has_candidate_ancestor:
                filtered.append(candidate)

        filtered.sort(key=lambda item: item.id)
        return filtered

    def _find_entry_plan_for_user(
        self,
        *,
        period_plans: list[EconomyPlan],
        user_id: str,
    ) -> EconomyPlan | None:
        candidates = self._find_entry_plans_for_user(period_plans=period_plans, user_id=user_id)
        if not candidates:
            return None
        return candidates[0]

    def _resolve_period_bounds(
        self,
        *,
        period: str | None,
        period_start: date | None,
        period_end: date | None,
    ) -> tuple[date, date, date, date]:
        if period_start is not None:
            if period_end is None:
                month_start, month_end = month_bounds_for_date(period_start)
                return period_start, month_end, month_start, month_end
            if period_end < period_start:
                raise Conflict("Plan period end cannot be earlier than period start")
            month_start, _month_end = month_bounds_for_date(period_start)
            return period_start, period_end, month_start, period_end
        if period is None:
            raise Conflict("Either period or period_start is required")
        month_start, month_end = parse_month_period(period)
        return month_start, month_end, month_start, month_end

    def _resolve_child_period_bounds(
        self,
        *,
        parent_plan: EconomyPlan,
        candidate_start: date | None,
        candidate_end: date | None,
    ) -> tuple[date, date]:
        if candidate_start is None:
            child_start = parent_plan.period_start
        else:
            child_start = candidate_start
        if child_start < parent_plan.period_start:
            raise Conflict("Child plan period start cannot be earlier than parent period start")
        if child_start > parent_plan.period_end:
            raise Conflict("Child plan period start cannot be later than parent period end")
        if candidate_end is None:
            return child_start, parent_plan.period_end
        if candidate_end < child_start:
            raise Conflict("Child plan period end cannot be earlier than child plan period start")
        if candidate_end > parent_plan.period_end:
            raise Conflict("Child plan period end cannot be later than parent plan period end")
        return child_start, candidate_end

    def _is_plan_closed(self, plan: EconomyPlan) -> bool:
        # Plan is considered closed only after explicit close action.
        # By default, period_end is month end for period_start; automatic date rollover
        # must not lock editing for historical months.
        if plan.period_end is None:
            return False
        _month_start, month_end = month_bounds_for_date(plan.period_start)
        return plan.period_end != month_end

    def _ensure_plan_is_open(self, plan: EconomyPlan) -> None:
        if self._is_plan_closed(plan):
            raise Conflict("Plan is closed and cannot be modified")

    async def _ensure_owner_has_direct_subordinates(self, owner_user_id: str) -> None:
        children = await self._users.list_direct_subordinates_with_profiles_and_roles(
            manager_user_id=owner_user_id,
            include_inactive=False,
        )
        if not children:
            raise Conflict("Plan split and delegation are available only for users with subordinates")

    async def _ensure_available_amount(self, *, parent_plan: EconomyPlan, requested_amount: Decimal) -> None:
        delegated_sum = await self._plans.sum_children_plan_amount(parent_plan_id=parent_plan.id)
        parent_total = Decimal(str(parent_plan.plan_amount or 0))
        available = parent_total - delegated_sum
        if requested_amount > available:
            raise Conflict("Requested amount exceeds parent available amount")

    async def _ensure_can_view_root(self, *, current_user: CurrentUser, requested_root_user_id: str) -> None:
        if current_user.role_id == settings.superadmin_role_id:
            return
        if await self._is_ancestor_or_self(
            ancestor_user_id=current_user.user_id,
            target_user_id=requested_root_user_id,
        ):
            return
        raise Forbidden("Requested plan branch is outside your management scope")

    async def _ensure_can_manage_node(self, *, current_user: CurrentUser, plan_owner_user_id: str) -> None:
        if current_user.role_id == settings.superadmin_role_id:
            return
        allowed = await self._is_ancestor_or_self(
            ancestor_user_id=current_user.user_id,
            target_user_id=plan_owner_user_id,
        )
        if not allowed:
            raise Forbidden("You cannot manage plans outside your hierarchy")

    async def _is_ancestor_or_self(self, *, ancestor_user_id: str, target_user_id: str) -> bool:
        cursor_id: str | None = target_user_id
        visited: set[str] = set()
        while cursor_id is not None and cursor_id not in visited:
            if cursor_id == ancestor_user_id:
                return True
            visited.add(cursor_id)
            cursor_user = await self._users.get_by_id(cursor_id)
            if cursor_user is None:
                return False
            cursor_id = cursor_user.id_parent
        return False

    def _can_manage_node_sync(
        self,
        *,
        current_user: CurrentUser,
        plan_owner_user_id: str,
        user_meta_by_id: dict[str, dict[str, str | None]],
    ) -> bool:
        if current_user.role_id == settings.superadmin_role_id:
            return True
        cursor_id: str | None = plan_owner_user_id
        visited: set[str] = set()
        while cursor_id is not None and cursor_id not in visited:
            if cursor_id == current_user.user_id:
                return True
            visited.add(cursor_id)
            user_meta = user_meta_by_id.get(cursor_id)
            cursor_id = user_meta.get("id_parent") if user_meta else None
        return False
