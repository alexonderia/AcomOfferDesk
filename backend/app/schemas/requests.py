from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.actions import OfferActionsSchema, RequestActionsSchema


class RequestFileSchema(BaseModel):
    id: int
    path: str
    name: str
    download_url: str


class RequestStatsSchema(BaseModel):
    count_submitted: int
    count_deleted_alert: int
    count_accepted_total: int
    count_rejected_total: int


class OfferItemSchema(BaseModel):
    offer_id: int
    contractor_user_id: str
    status: str
    status_label: str
    offer_amount: float | None
    created_at: datetime
    updated_at: datetime
    offer_workspace_url: str
    contractor_full_name: str | None
    contractor_phone: str | None
    contractor_mail: str | None
    contractor_inn: str | None
    contractor_company_name: str | None
    contractor_company_phone: str | None
    contractor_company_mail: str | None
    contractor_contact_phone: str | None
    contractor_contact_mail: str | None
    contractor_address: str | None
    contractor_note: str | None
    files: list[RequestFileSchema]
    unread_messages_count: int
    actions: OfferActionsSchema = Field(default_factory=OfferActionsSchema)


class RequestIdAvailabilityResponse(BaseModel):
    available: bool
    detail: str | None = None
    reason: str | None = None


class RequestItemSchema(BaseModel):
    request_id: str
    description: str | None
    status: str
    status_label: str
    initial_amount: float | None = None
    final_amount: float | None = None
    deadline_at: datetime
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    owner_user_id: str
    owner_full_name: str | None
    chosen_offer_id: int | None
    id_plan: int | None = None
    stats: RequestStatsSchema
    unread_messages_count: int
    files: list[RequestFileSchema]
    actions: RequestActionsSchema = Field(default_factory=RequestActionsSchema)


class RequestDetailsSchema(RequestItemSchema):
    offers: list[OfferItemSchema]


class OfferedRequestOfferSchema(BaseModel):
    id: int = Field(alias="offer_id")
    status: str
    unread_messages_count: int
    actions: OfferActionsSchema = Field(default_factory=OfferActionsSchema)

class OpenRequestItemSchema(BaseModel):
    request_id: str
    description: str | None
    status: str
    status_label: str
    deadline_at: datetime
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    owner_user_id: str
    owner_full_name: str | None
    chosen_offer_id: int | None
    id_plan: int | None = None
    files: list[RequestFileSchema]
    offers: list[OfferedRequestOfferSchema] = Field(default_factory=list)
    actions: RequestActionsSchema = Field(default_factory=RequestActionsSchema)


class OpenRequestListData(BaseModel):
    items: list[OpenRequestItemSchema]


class RequestListData(BaseModel):
    items: list[RequestItemSchema]


class RequestDetailsResponseData(BaseModel):
    item: RequestDetailsSchema


class RequestListResponse(BaseModel):
    data: RequestListData


class RequestDetailsResponse(BaseModel):
    data: RequestDetailsResponseData


class OpenRequestListResponse(BaseModel):
    data: OpenRequestListData


class RequestCreateResponseData(BaseModel):
    request_id: str
    file_ids: list[int]


class RequestCreateResponse(BaseModel):
    data: RequestCreateResponseData


class DeletedAlertViewed(BaseModel):
    request_id: str


class RequestOfferStatsSchema(BaseModel):
    request_id: str
    count_deleted_alert: int
    updated_at: datetime


class DeletedAlertViewedResponseData(BaseModel):
    status: str
    request_offer_stats: RequestOfferStatsSchema


class DeletedAlertViewedResponse(BaseModel):
    data: DeletedAlertViewedResponseData
    

class RequestEditPayload(BaseModel):
    status: str | None = None
    deadline_at: datetime | None = None
    owner_user_id: str | None = None
    initial_amount: float | None = None
    final_amount: float | None = None
    id_plan: int | None = None


class RequestEmailNotificationPayload(BaseModel):
    additional_emails: list[str]


class RequestFileMutationResponseData(BaseModel):
    request_id: str
    file_id: int


class RequestMutationResponseData(BaseModel):
    request_id: str


class RequestEmailNotificationResponseData(BaseModel):
    request_id: str
    sent_to: list[str]


class RequestMutationResponse(BaseModel):
    data: RequestMutationResponseData


class RequestEmailNotificationResponse(BaseModel):
    data: RequestEmailNotificationResponseData


class RequestFileMutationResponse(BaseModel):
    data: RequestFileMutationResponseData
