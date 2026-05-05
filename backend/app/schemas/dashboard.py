from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.links import LinkSet


class DashboardStatusCounterSchema(BaseModel):
    status: str
    status_label: str
    count: int


class DashboardEconomistNodeSchema(BaseModel):
    user_id: str
    full_name: str | None
    role_id: int
    role_name: str
    parent_user_id: str | None
    in_progress_total: int
    statuses: list[DashboardStatusCounterSchema]
    children: list["DashboardEconomistNodeSchema"] = Field(default_factory=list)


class DashboardRequestItemSchema(BaseModel):
    request_id: int
    description: str | None
    status: str
    status_label: str
    deadline_at: datetime
    created_at: datetime
    updated_at: datetime
    owner_user_id: str
    owner_full_name: str | None


class UpcomingUnavailabilityItemSchema(BaseModel):
    user_id: str
    full_name: str | None
    role_name: str
    status: str
    started_at: datetime
    ended_at: datetime


class DashboardSavingsItemSchema(BaseModel):
    request_id: int
    owner_user_id: str
    owner_full_name: str | None
    initial_amount: float
    offer_amount: float
    final_amount: float
    savings_amount: float
    closed_at: datetime | None
    plan_id: int | None = None
    plan_name: str | None = None


class DashboardClosedRequestItemSchema(BaseModel):
    request_id: int
    owner_user_id: str
    owner_full_name: str | None
    initial_amount: float | None
    offer_amount: float | None
    final_amount: float | None
    savings_amount: float | None
    closed_at: datetime | None
    plan_id: int | None = None
    plan_name: str | None = None


class DashboardSavingsSummarySchema(BaseModel):
    total_closed_requests: int
    total_with_savings: int
    total_savings_amount: float
    closed_items: list[DashboardClosedRequestItemSchema]
    items: list[DashboardSavingsItemSchema]


class ResponsibilityDashboardData(BaseModel):
    tree: list[DashboardEconomistNodeSchema]
    unassigned_requests: list[DashboardRequestItemSchema]
    my_requests: list[DashboardRequestItemSchema]
    assigned_requests: list[DashboardRequestItemSchema]
    active_unavailability: list[UpcomingUnavailabilityItemSchema]
    upcoming_unavailability: list[UpcomingUnavailabilityItemSchema]
    savings: DashboardSavingsSummarySchema


class ResponsibilityDashboardResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: ResponsibilityDashboardData
    links: LinkSet = Field(alias="_links")
