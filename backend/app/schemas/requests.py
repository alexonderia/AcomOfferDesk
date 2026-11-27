from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.actions import OfferActionsSchema, RequestActionsSchema


class RequestFileSchema(BaseModel):
    id: int
    path: str
    name: str
    download_url: str


class RequestHiddenFileSchema(RequestFileSchema):
    is_specification_source: bool | None
    can_delete: bool = False


class RequestHiddenFilesResponse(BaseModel):
    files: list[RequestHiddenFileSchema]


class RequestSpecificationPreviewResponse(BaseModel):
    name: str
    mime_type: str
    content_base64: str
    confirmation: str
    item_count: int
    used_ocr: bool


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
    contractor_status: str | None = None
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
    owner_phone: str | None = None
    owner_mail: str | None = None
    owner_warning: str | None = None
    chosen_offer_id: int | None
    id_plan: int | None = None
    stats: RequestStatsSchema
    unread_messages_count: int
    files: list[RequestFileSchema]
    actions: RequestActionsSchema = Field(default_factory=RequestActionsSchema)


class RequestDetailsSchema(RequestItemSchema):
    plan_name: str | None = None
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
    owner_phone: str | None = None
    owner_mail: str | None = None
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


class EligibleRequestOwnerSchema(BaseModel):
    user_id: str
    full_name: str | None = None
    role: str
    unavailable_period: dict[str, object] | None = None


class EligibleRequestOwnerListData(BaseModel):
    items: list[EligibleRequestOwnerSchema] = Field(default_factory=list)


class EligibleRequestOwnerListResponse(BaseModel):
    data: EligibleRequestOwnerListData


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


class RequestEmailPreviewUpload(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(ge=0)


class RequestDraftEmailPreviewPayload(RequestEmailNotificationPayload):
    request_id: str = Field(min_length=1)
    description: str | None = Field(default=None, max_length=3000)
    deadline_at: datetime
    normative_file_id: int = Field(gt=0)
    files: list[RequestEmailPreviewUpload] = Field(min_length=1)
    hidden_contractor_ids: list[str] = Field(default_factory=list)


class RequestEmailPreviewAttachment(BaseModel):
    name: str
    size_bytes: int
    download_url: str | None = None
    upload_index: int | None = None


class RequestEmailPreviewMessage(BaseModel):
    to_email: str
    kind: str
    subject: str
    html_content: str
    text_content: str
    attachments: list[RequestEmailPreviewAttachment]


class RequestEmailPreviewData(BaseModel):
    messages: list[RequestEmailPreviewMessage]
    warnings: list[str]


class RequestEmailPreviewResponse(BaseModel):
    data: RequestEmailPreviewData


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
