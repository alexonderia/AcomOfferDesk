from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.contractor_validation import (
    validate_inn,
    validate_optional_email,
    validate_ru_phone,
)
from app.schemas.actions import ChatActionsSchema, OfferActionsSchema, RequestActionsSchema
from app.schemas.links import LinkSet
from app.schemas.requests import RequestFileSchema


class ContractorInfoSchema(BaseModel):
    user_id: str
    full_name: str | None
    phone: str | None
    mail: str | None
    company_name: str | None
    inn: str | None
    company_phone: str | None
    company_mail: str | None
    address: str | None
    note: str | None


class ContractorInfoResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: ContractorInfoSchema
    links: LinkSet = Field(alias="_links")


class OfferMessageReadBySchema(BaseModel):
    user_id: str
    user_full_name: str | None
    read_at: datetime


class OfferMessageSchema(BaseModel):
    id: int
    user_id: str
    user_full_name: str | None
    text: str
    type: str
    status: str
    created_at: datetime
    updated_at: datetime
    read_by: list[OfferMessageReadBySchema] = Field(default_factory=list)
    attachments: list[RequestFileSchema] = Field(default_factory=list)


class ExistingOfferPreviewSchema(BaseModel):
    offer_id: int
    status: str
    status_label: str
    files: list[RequestFileSchema]
    actions: OfferActionsSchema = Field(default_factory=OfferActionsSchema)


class ContractorRequestViewSchema(BaseModel):
    request_id: int
    description: str | None
    status: str
    status_label: str
    deadline_at: datetime
    owner_user_id: str
    files: list[RequestFileSchema]
    owner_full_name: str | None
    existing_offer: ExistingOfferPreviewSchema | None
    actions: RequestActionsSchema = Field(default_factory=RequestActionsSchema)


class ContractorRequestViewResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: ContractorRequestViewSchema
    links: LinkSet = Field(alias="_links")


class OfferWorkspaceRequestSchema(BaseModel):
    request_id: int
    description: str | None
    status: str
    status_label: str
    initial_amount: float | None
    final_amount: float | None
    deadline_at: datetime
    owner_user_id: str
    owner_full_name: str | None
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    files: list[RequestFileSchema]
    actions: RequestActionsSchema = Field(default_factory=RequestActionsSchema)


class OfferWorkspaceOfferSchema(BaseModel):
    offer_id: int
    status: str
    status_label: str
    offer_amount: float | None
    created_at: datetime
    updated_at: datetime
    files: list[RequestFileSchema]
    actions: OfferActionsSchema = Field(default_factory=OfferActionsSchema)


class OfferWorkspaceOfferListItemSchema(BaseModel):
    offer_id: int
    status: str
    status_label: str
    offer_amount: float | None
    created_at: datetime
    updated_at: datetime
    files: list[RequestFileSchema]
    actions: OfferActionsSchema = Field(default_factory=OfferActionsSchema)


class OfferWorkspaceSchema(BaseModel):
    request: OfferWorkspaceRequestSchema
    offer: OfferWorkspaceOfferSchema
    offers: list[OfferWorkspaceOfferListItemSchema]
    contractor: ContractorInfoSchema
    chat_actions: ChatActionsSchema = Field(default_factory=ChatActionsSchema)


class OfferWorkspaceResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: OfferWorkspaceSchema
    links: LinkSet = Field(alias="_links")


class OfferCreateResponseData(BaseModel):
    offer_id: int
    request_id: int


class OfferCreateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: OfferCreateResponseData
    links: LinkSet = Field(alias="_links")


class OfferFileMutationResponseData(BaseModel):
    offer_id: int
    file_id: int


class OfferFileMutationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: OfferFileMutationResponseData
    links: LinkSet = Field(alias="_links")


class OfferMessageListData(BaseModel):
    offer_id: int
    items: list[OfferMessageSchema]
    actions: ChatActionsSchema = Field(default_factory=ChatActionsSchema)


class OfferMessageListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: OfferMessageListData
    links: LinkSet = Field(alias="_links")


class OfferMessageCreatePayload(BaseModel):
    text: str


class OfferMessageCreateResponseData(BaseModel):
    offer_id: int
    message_id: int


class OfferMessageCreateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: OfferMessageCreateResponseData
    links: LinkSet = Field(alias="_links")


class OfferMessageStatusUpdatePayload(BaseModel):
    message_ids: list[int] | None = None
    up_to_message_id: int | None = None


class OfferMessageStatusUpdateResponseData(BaseModel):
    offer_id: int
    updated_count: int


class OfferMessageStatusUpdateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: OfferMessageStatusUpdateResponseData
    links: LinkSet = Field(alias="_links")


class OfferMessageFileUploadResponseData(BaseModel):
    offer_id: int
    file_id: int
    name: str
    path: str
    upload_token: str
    download_url: str


class OfferMessageFileUploadResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: OfferMessageFileUploadResponseData
    links: LinkSet = Field(alias="_links")


class OfferStatusUpdatePayload(BaseModel):
    status: str


class OfferStatusMutationResponseData(BaseModel):
    offer_id: int
    status: str


class OfferStatusMutationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: OfferStatusMutationResponseData
    links: LinkSet = Field(alias="_links")


class OfferCreatePayload(BaseModel):
    offer_amount: float | None = None


class ManualContractorCreatePayload(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=256)
    inn: str = Field(..., min_length=1, max_length=32)
    company_phone: str = Field(..., min_length=1, max_length=64)
    company_mail: str | None = Field(default=None, max_length=256)
    address: str | None = Field(default=None, max_length=256)
    note: str | None = Field(default=None, max_length=1024)

    @field_validator("company_name", "inn", "company_phone", mode="before")
    @classmethod
    def _strip_required(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Значение должно быть строкой")
        normalized = value.strip()
        if not normalized:
            raise ValueError("Поле обязательно для заполнения")
        return normalized

    @field_validator("company_mail", "address", "note", mode="before")
    @classmethod
    def _strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("company_phone")
    @classmethod
    def _validate_phone(cls, value: str) -> str:
        return validate_ru_phone(value)

    @field_validator("inn")
    @classmethod
    def _validate_inn(cls, value: str) -> str:
        return validate_inn(value)

    @field_validator("company_mail")
    @classmethod
    def _validate_company_mail(cls, value: str | None) -> str | None:
        return validate_optional_email(value, allow_placeholder=True)


class ManualOfferCreateResponseData(BaseModel):
    offer_id: int
    request_id: int
    contractor_user_id: str
    contractor_created: bool


class ManualOfferCreateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: ManualOfferCreateResponseData
    links: LinkSet = Field(alias="_links")


class OfferEditPayload(BaseModel):
    offer_amount: float


class OfferEditResponseData(BaseModel):
    offer_id: int
    offer_amount: float


class OfferEditResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: OfferEditResponseData
    links: LinkSet = Field(alias="_links")
