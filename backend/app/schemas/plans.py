from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.links import LinkSet


class PlanNodeActionsSchema(BaseModel):
    create_child_plan: bool = False
    create_subplan: bool = False
    delegate_plan: bool = False
    edit_plan: bool = False
    delete_child_plan: bool = False
    activate_plan: bool = False
    close_plan: bool = False
    view_plan: bool = True


class PlanTreeNodeSchema(BaseModel):
    plan_id: int
    plan_name: str
    id_parent_plan: int | None = None
    user_id: str
    user_name: str
    user_role: str
    parent_user_id_snapshot: str | None = None
    period_start: date
    period_end: date
    plan_amount: float
    delegated_amount: float
    personal_plan_amount: float
    unallocated_amount: float
    fact_amount_self: float
    fact_amount_subtree: float
    period_fact_amount: float = 0
    period_progress_percent: float = 0
    in_progress_requests_count: int = 0
    remaining_amount: float
    progress_percent: float
    available_actions: PlanNodeActionsSchema = Field(default_factory=PlanNodeActionsSchema)
    children: list["PlanTreeNodeSchema"] = Field(default_factory=list)


class PlanDashboardSummarySchema(BaseModel):
    total_plan_amount: float
    total_fact_amount: float
    total_period_fact_amount: float = 0
    total_remaining_amount: float
    total_progress_percent: float
    total_period_progress_percent: float = 0


class PlanRequestStatsSchema(BaseModel):
    total_requests: int = 0
    distributed_requests: int = 0
    unallocated_requests: int = 0
    request_fact_amount: float = 0
    unallocated_amount: float = 0
    completion_percent: float = 0


class PlanDashboardDataSchema(BaseModel):
    period: str
    period_start: date
    period_end: date
    can_create_root_plan: bool
    root_plan_exists: bool
    summary: PlanDashboardSummarySchema
    request_stats: PlanRequestStatsSchema = Field(default_factory=PlanRequestStatsSchema)
    tree: PlanTreeNodeSchema | None = None
    trees: list[PlanTreeNodeSchema] = Field(default_factory=list)


class PlanDashboardResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: PlanDashboardDataSchema
    links: LinkSet = Field(alias="_links")


class PlanRequestStatsDataSchema(BaseModel):
    period_start: date
    period_end: date
    plan_id: int | None = None
    stats: PlanRequestStatsSchema


class PlanRequestStatsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: PlanRequestStatsDataSchema
    links: LinkSet = Field(alias="_links")


class PlanTreeDataSchema(BaseModel):
    period: str
    period_start: date
    period_end: date
    tree: PlanTreeNodeSchema


class PlanTreeResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: PlanTreeDataSchema
    links: LinkSet = Field(alias="_links")


class PlanSummaryDataSchema(BaseModel):
    period: str
    period_start: date
    period_end: date
    summary: PlanDashboardSummarySchema


class PlanSummaryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: PlanSummaryDataSchema
    links: LinkSet = Field(alias="_links")


class PlanRootCreateRequest(BaseModel):
    period: str | None = Field(default=None, min_length=7, max_length=7)
    period_start: date | None = None
    period_end: date | None = None
    name: str = Field(min_length=1, max_length=255)
    plan_amount: float = Field(ge=0)

    @model_validator(mode="after")
    def _validate_payload(self) -> "PlanRootCreateRequest":
        if self.period is None and self.period_start is None:
            raise ValueError("Either period or period_start must be provided")
        return self


class PlanSubplanCreateRequest(BaseModel):
    parent_plan_id: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=255)
    period_start: date | None = None
    period_end: date | None = None
    child_user_id: str | None = Field(default=None, min_length=1)
    plan_amount: float = Field(gt=0)


class PlanDelegateRequest(BaseModel):
    parent_plan_id: int = Field(ge=1)
    child_user_id: str = Field(min_length=1)
    child_period_start: date | None = None
    child_plan_amount: float = Field(gt=0)


class PlanUpdateRequest(BaseModel):
    plan_amount: float | None = Field(default=None, ge=0)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    period_end: date | None = None
    status: str | None = None

    @model_validator(mode="after")
    def _validate_payload(self) -> "PlanUpdateRequest":
        if self.plan_amount is None and self.name is None and self.period_end is None and self.status is None:
            raise ValueError("At least one mutable field must be provided")
        return self


class PlanMutationDataSchema(BaseModel):
    plan_id: int
    plan_name: str
    id_parent_plan: int | None = None
    user_id: str
    parent_user_id_snapshot: str | None = None
    period_start: date
    period_end: date
    plan_amount: float


class PlanMutationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: PlanMutationDataSchema
    links: LinkSet = Field(alias="_links")


class PlanDeleteDataSchema(BaseModel):
    deleted_plan_id: int


class PlanDeleteResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: PlanDeleteDataSchema
    links: LinkSet = Field(alias="_links")


class PlanDelegateCandidateSchema(BaseModel):
    user_id: str
    full_name: str | None = None
    role_name: str
    has_plan_for_period: bool
    existing_plan_id: int | None = None


class PlanDelegateCandidatesDataSchema(BaseModel):
    parent_plan_id: int
    items: list[PlanDelegateCandidateSchema] = Field(default_factory=list)


class PlanDelegateCandidatesResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: PlanDelegateCandidatesDataSchema
    links: LinkSet = Field(alias="_links")


class PlanOptionSchema(BaseModel):
    plan_id: int
    plan_name: str
    user_id: str
    user_name: str
    user_role: str
    period_start: date
    period_end: date
    is_closed: bool


class PlanOptionsDataSchema(BaseModel):
    period: str
    items: list[PlanOptionSchema] = Field(default_factory=list)


class PlanOptionsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: PlanOptionsDataSchema
    links: LinkSet = Field(alias="_links")
