from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from app.core.config import settings
from app.domain.policies import CurrentUser, UserPolicy
from app.repositories.economy_plans import EconomyPlanRepository
from app.repositories.requests import RequestRepository
from app.repositories.user_status_periods import UserStatusPeriodRepository
from app.repositories.users import UserRepository
from app.services.requests import format_request_status


@dataclass(frozen=True)
class DashboardStatusCounter:
    status: str
    status_label: str
    count: int


@dataclass
class DashboardEconomistNode:
    user_id: str
    full_name: str | None
    role_id: int
    role_name: str
    parent_user_id: str | None
    in_progress_total: int
    statuses: list[DashboardStatusCounter]
    children: list["DashboardEconomistNode"] = field(default_factory=list)


@dataclass(frozen=True)
class DashboardRequestItem:
    request_id: int
    description: str | None
    status: str
    status_label: str
    deadline_at: datetime
    created_at: datetime
    updated_at: datetime
    owner_user_id: str
    owner_full_name: str | None


@dataclass(frozen=True)
class DashboardSavingsItem:
    request_id: int
    owner_user_id: str
    owner_full_name: str | None
    initial_amount: float
    offer_amount: float
    final_amount: float
    savings_amount: float
    closed_at: datetime | None
    plan_id: int | None
    plan_name: str | None


@dataclass(frozen=True)
class DashboardClosedRequestItem:
    request_id: int
    owner_user_id: str
    owner_full_name: str | None
    initial_amount: float | None
    offer_amount: float | None
    final_amount: float | None
    savings_amount: float | None
    closed_at: datetime | None
    plan_id: int | None
    plan_name: str | None


@dataclass(frozen=True)
class DashboardSavingsSummary:
    total_closed_requests: int
    total_with_savings: int
    total_savings_amount: float
    closed_items: list[DashboardClosedRequestItem]
    items: list[DashboardSavingsItem]


@dataclass(frozen=True)
class ResponsibilityDashboard:
    tree: list[DashboardEconomistNode]
    unassigned_requests: list[DashboardRequestItem]
    my_requests: list[DashboardRequestItem]
    assigned_requests: list[DashboardRequestItem]
    active_unavailability: list["UpcomingUnavailabilityItem"]
    upcoming_unavailability: list["UpcomingUnavailabilityItem"]
    savings: DashboardSavingsSummary


@dataclass(frozen=True)
class UpcomingUnavailabilityItem:
    user_id: str
    full_name: str | None
    role_name: str
    status: str
    started_at: datetime
    ended_at: datetime


class DashboardService:
    def __init__(
        self,
        users: UserRepository,
        requests: RequestRepository,
        user_status_periods: UserStatusPeriodRepository,
        plans: EconomyPlanRepository,
    ):
        self._users = users
        self._requests = requests
        self._user_status_periods = user_status_periods
        self._plans = plans

    async def get_responsibility_dashboard(self, *, current_user: CurrentUser) -> ResponsibilityDashboard:
        UserPolicy.ensure_can_view_responsibility_dashboard(current_user)

        staff_rows = await self._users.list_staff_with_profiles_and_roles_for_dashboard(
            role_ids=[settings.lead_economist_role_id, settings.economist_role_id],
        )

        by_id = {user.id: (user, profile, role) for user, profile, role in staff_rows}

        if current_user.role_id == settings.superadmin_role_id:
            descendant_ids = set(by_id.keys())
            staff_owner_ids = list(by_id.keys())
            my_owner_ids: list[str] = []
            assigned_owner_ids = list(by_id.keys())
            hierarchy_scope_owner_ids: list[str] | None = None
        else:
            descendant_ids: set[str] = set()
            for user_id in by_id:
                cursor = user_id
                seen: set[str] = set()
                while cursor and cursor not in seen:
                    seen.add(cursor)
                    if cursor == current_user.user_id:
                        if user_id != current_user.user_id:
                            descendant_ids.add(user_id)
                        break
                    parent = by_id.get(cursor)
                    cursor = parent[0].id_parent if parent else None

            staff_owner_ids = list(descendant_ids)
            if current_user.role_id == settings.lead_economist_role_id and current_user.user_id in by_id:
                staff_owner_ids = [current_user.user_id, *staff_owner_ids]

            my_owner_ids = (
                [current_user.user_id]
                if current_user.role_id in {settings.lead_economist_role_id, settings.project_manager_role_id}
                else []
            )
            assigned_owner_ids = list(descendant_ids)
            hierarchy_scope_owner_ids = await self._resolve_hierarchy_scope_owner_ids(
                current_user_id=current_user.user_id,
            )

        request_counters = await self._requests.count_in_progress_requests_by_owner(
            owner_ids=staff_owner_ids,
        )

        counters_by_user: dict[str, dict[str, int]] = {}
        for owner_id, status, count in request_counters:
            owner_counters = counters_by_user.setdefault(owner_id, {})
            owner_counters[status] = count

        nodes: dict[str, DashboardEconomistNode] = {}
        for user_id in staff_owner_ids:
            user, profile, role = by_id[user_id]
            status_counts = counters_by_user.get(user.id, {})
            statuses = [
                DashboardStatusCounter(
                    status=status,
                    status_label=format_request_status(status),
                    count=count,
                )
                for status, count in sorted(status_counts.items())
            ]
            nodes[user.id] = DashboardEconomistNode(
                user_id=user.id,
                full_name=profile.full_name if profile else None,
                role_id=user.id_role,
                role_name=role.role,
                parent_user_id=user.id_parent,
                in_progress_total=sum(status_counts.values()),
                statuses=statuses,
            )

        tree: list[DashboardEconomistNode] = []
        for node in nodes.values():
            if node.parent_user_id in nodes:
                nodes[node.parent_user_id].children.append(node)
            else:
                tree.append(node)

        tree.sort(key=lambda item: (item.role_id, item.full_name or item.user_id))
        self._sort_children(tree)

        unassigned_owner_ids = hierarchy_scope_owner_ids
        if current_user.role_id == settings.project_manager_role_id:
            unassigned_owner_ids = None

        unassigned_rows = await self._requests.list_unassigned_requests(
            operator_role_id=settings.operator_role_id,
            owner_ids=unassigned_owner_ids,
        )
        unassigned_requests = [
            DashboardRequestItem(
                request_id=request.id,
                description=request.description,
                status=request.status,
                status_label=format_request_status(request.status),
                deadline_at=request.deadline_at,
                created_at=request.created_at,
                updated_at=request.updated_at,
                owner_user_id=request.id_user,
                owner_full_name=None,
            )
            for request in unassigned_rows
        ]

        my_rows = await self._requests.list_in_progress_requests_by_owner_ids(owner_ids=my_owner_ids)
        my_requests = [
            DashboardRequestItem(
                request_id=request.id,
                description=request.description,
                status=request.status,
                status_label=format_request_status(request.status),
                deadline_at=request.deadline_at,
                created_at=request.created_at,
                updated_at=request.updated_at,
                owner_user_id=request.id_user,
                owner_full_name=by_id[request.id_user][1].full_name if request.id_user in by_id and by_id[request.id_user][1] else None,
            )
            for request in my_rows
        ]

        assigned_rows = await self._requests.list_in_progress_requests_by_owner_ids(owner_ids=assigned_owner_ids)
        assigned_requests = [
            DashboardRequestItem(
                request_id=request.id,
                description=request.description,
                status=request.status,
                status_label=format_request_status(request.status),
                deadline_at=request.deadline_at,
                created_at=request.created_at,
                updated_at=request.updated_at,
                owner_user_id=request.id_user,
                owner_full_name=by_id[request.id_user][1].full_name if request.id_user in by_id and by_id[request.id_user][1] else None,
            )
            for request in assigned_rows
        ]

        active_periods_by_user = await self._user_status_periods.list_active_for_users(user_ids=staff_owner_ids)
        active_unavailability = [
            UpcomingUnavailabilityItem(
                user_id=period.id_user,
                full_name=by_id[period.id_user][1].full_name if by_id[period.id_user][1] else None,
                role_name=by_id[period.id_user][2].role,
                status=period.status,
                started_at=period.started_at,
                ended_at=period.ended_at,
            )
            for period in active_periods_by_user.values()
            if period.id_user in by_id
        ]

        soon_periods = await self._user_status_periods.list_next_for_users(user_ids=staff_owner_ids)

        upcoming_unavailability = [
            UpcomingUnavailabilityItem(
                user_id=period.id_user,
                full_name=by_id[period.id_user][1].full_name if by_id[period.id_user][1] else None,
                role_name=by_id[period.id_user][2].role,
                status=period.status,
                started_at=period.started_at,
                ended_at=period.ended_at,
            )
            for period in soon_periods
            if period.id_user in by_id
        ]

        savings_rows = await self._requests.list_closed_requests_with_chosen_offer_by_owner_ids(owner_ids=staff_owner_ids)
        plan_ids = list({int(request.id_plan) for request, _, _ in savings_rows if request.id_plan is not None})
        plans = await self._plans.list_by_ids(plan_ids=plan_ids)
        plan_name_by_id = {plan.id: plan.name for plan in plans}
        savings_items: list[DashboardSavingsItem] = []
        closed_items: list[DashboardClosedRequestItem] = []
        total_savings_amount = Decimal("0")
        for request, chosen_offer, profile in savings_rows:
            savings_amount = self._calculate_savings(
                initial_amount=request.initial_amount,
                offer_amount=(chosen_offer.offer_amount if chosen_offer is not None else None),
                final_amount=request.final_amount,
            )

            closed_items.append(
                DashboardClosedRequestItem(
                    request_id=request.id,
                    owner_user_id=request.id_user,
                    owner_full_name=profile.full_name if profile else None,
                    initial_amount=float(request.initial_amount) if request.initial_amount is not None else None,
                    offer_amount=float(chosen_offer.offer_amount) if chosen_offer and chosen_offer.offer_amount is not None else None,
                    final_amount=float(request.final_amount) if request.final_amount is not None else None,
                    savings_amount=float(savings_amount) if savings_amount is not None else None,
                    closed_at=request.closed_at,
                    plan_id=request.id_plan,
                    plan_name=plan_name_by_id.get(request.id_plan) if request.id_plan is not None else None,
                )
            )

            if savings_amount is None:
                continue

            total_savings_amount += savings_amount
            savings_items.append(
                DashboardSavingsItem(
                    request_id=request.id,
                    owner_user_id=request.id_user,
                    owner_full_name=profile.full_name if profile else None,
                    initial_amount=float(request.initial_amount),
                    offer_amount=float(chosen_offer.offer_amount),
                    final_amount=float(request.final_amount),
                    savings_amount=float(savings_amount),
                    closed_at=request.closed_at,
                    plan_id=request.id_plan,
                    plan_name=plan_name_by_id.get(request.id_plan) if request.id_plan is not None else None,
                )
            )

        return ResponsibilityDashboard(
            tree=tree,
            unassigned_requests=unassigned_requests,
            my_requests=my_requests,
            assigned_requests=assigned_requests,
            active_unavailability=active_unavailability,
            upcoming_unavailability=upcoming_unavailability,
            savings=DashboardSavingsSummary(
                total_closed_requests=len(savings_rows),
                total_with_savings=len(savings_items),
                total_savings_amount=float(total_savings_amount),
                closed_items=closed_items,
                items=savings_items,
            ),
        )

    async def _resolve_hierarchy_scope_owner_ids(self, *, current_user_id: str) -> list[str]:
        pairs = await self._users.list_active_user_parent_pairs()
        children_by_parent: dict[str, list[str]] = {}
        for user_id, parent_id in pairs:
            if parent_id:
                children_by_parent.setdefault(parent_id, []).append(user_id)

        visible_ids: set[str] = {current_user_id}
        stack: list[str] = [current_user_id]
        while stack:
            manager_id = stack.pop()
            for child_id in children_by_parent.get(manager_id, []):
                if child_id in visible_ids:
                    continue
                visible_ids.add(child_id)
                stack.append(child_id)

        return list(visible_ids)

    def _sort_children(self, nodes: list[DashboardEconomistNode]) -> None:
        for node in nodes:
            node.children.sort(key=lambda item: (item.role_id, item.full_name or item.user_id))
            self._sort_children(node.children)

    def _calculate_savings(
        self,
        *,
        initial_amount,
        offer_amount,
        final_amount,
    ) -> Decimal | None:
        if initial_amount is None or offer_amount is None or final_amount is None:
            return None

        initial = Decimal(str(initial_amount))
        offer = Decimal(str(offer_amount))
        final = Decimal(str(final_amount))

        if final == initial:
            return offer - initial
        if final == offer:
            return initial - offer
        return None
