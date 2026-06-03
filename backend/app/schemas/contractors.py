from pydantic import BaseModel, Field

from app.schemas.actions import UserActionsSchema


class ContractorListItemSchema(BaseModel):
    user_id: str
    role_id: int
    status: str
    full_name: str | None = None
    phone: str | None = None
    mail: str | None = None
    company_name: str | None = None
    inn: str | None = None
    company_phone: str | None = None
    company_mail: str | None = None
    address: str | None = None
    note: str | None = None
    actions: UserActionsSchema = Field(default_factory=UserActionsSchema)


class ContractorListData(BaseModel):
    items: list[ContractorListItemSchema]


class ContractorListResponse(BaseModel):
    data: ContractorListData


class ContractorProfileData(BaseModel):
    user_id: str
    role_id: int
    status: str
    full_name: str | None = None
    phone: str | None = None
    mail: str | None = None
    company_name: str | None = None
    inn: str | None = None
    company_phone: str | None = None
    company_mail: str | None = None
    address: str | None = None
    note: str | None = None
    created_at: str | None = None
    actions: UserActionsSchema = Field(default_factory=UserActionsSchema)


class ContractorProfileResponse(BaseModel):
    data: ContractorProfileData


class ContractorStatusUpdateRequest(BaseModel):
    user_status: str


class ContractorStatusUpdateData(BaseModel):
    user_id: str
    user_status: str


class ContractorStatusUpdateResponse(BaseModel):
    data: ContractorStatusUpdateData


class ContractorInviteRequest(BaseModel):
    emails: list[str]
    normative_file_id: int = Field(..., ge=1)


class ContractorInviteFailure(BaseModel):
    email: str
    reason: str


class ContractorInviteData(BaseModel):
    sent: list[str]
    failed: list[ContractorInviteFailure]
    invalid: list[str]


class ContractorInviteResponse(BaseModel):
    data: ContractorInviteData
