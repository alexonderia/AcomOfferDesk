from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.contractor_validation import (
    validate_inn,
    validate_optional_email,
    validate_password_bcrypt_bytes,
    validate_ru_phone,
)
from app.schemas.actions import UserActionsSchema
from app.schemas.links import LinkSet


class UserListItemSchema(BaseModel):
    user_id: str
    role_id: int
    id_parent: str | None = None
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


class UserListData(BaseModel):
    items: list[UserListItemSchema]
    permissions: list[str] = Field(default_factory=list)


class UserListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: UserListData
    links: LinkSet = Field(alias="_links")


class EconomistListItemSchema(BaseModel):
    user_id: str
    status: str
    full_name: str | None = None
    phone: str | None = None
    mail: str | None = None
    actions: UserActionsSchema = Field(default_factory=UserActionsSchema)


class EconomistListData(BaseModel):
    items: list[EconomistListItemSchema]
    permissions: list[str] = Field(default_factory=list)


class EconomistListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: EconomistListData
    links: LinkSet = Field(alias="_links")

    
class UserRoleUpdateRequest(BaseModel):
    role_id: int = Field(ge=1)


class UserRoleUpdateData(BaseModel):
    user_id: str
    role_id: int


class UserRoleUpdateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: UserRoleUpdateData
    links: LinkSet = Field(alias="_links")


class UserManagerUpdateRequest(BaseModel):
    manager_user_id: str = Field(min_length=1)


class UserManagerUpdateData(BaseModel):
    user_id: str
    manager_user_id: str


class UserManagerUpdateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: UserManagerUpdateData
    links: LinkSet = Field(alias="_links")


class UserStatusUpdateRequest(BaseModel):
    user_status: str


class UserStatusUpdateData(BaseModel):
    user_id: str
    user_status: str
    tg_user_id: int | None = None
    tg_status: str | None = None


class UserStatusUpdateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: UserStatusUpdateData
    links: LinkSet = Field(alias="_links")


class RequestEconomistItemSchema(BaseModel):
    user_id: str
    full_name: str | None
    role: str
    unavailable_period: "UserUnavailabilityPeriodSchema | None" = None


class RequestEconomistListData(BaseModel):
    items: list[RequestEconomistItemSchema]
    permissions: list[str] = Field(default_factory=list)


class RequestEconomistListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: RequestEconomistListData
    links: LinkSet = Field(alias="_links")


class RequestContractorItemSchema(BaseModel):
    user_id: str
    full_name: str | None = None
    company_name: str | None = None
    mail: str | None = None
    company_mail: str | None = None


class RequestContractorListData(BaseModel):
    items: list[RequestContractorItemSchema]
    permissions: list[str] = Field(default_factory=list)


class RequestContractorListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: RequestContractorListData
    links: LinkSet = Field(alias="_links")


class UserUnavailabilityPeriodSchema(BaseModel):
    id: int
    status: str
    started_at: datetime
    ended_at: datetime


class MeData(BaseModel):
    user_id: str
    role_id: int
    status: str
    unavailable_period: "UserUnavailabilityPeriodSchema | None" = None
    unavailable_periods: list[UserUnavailabilityPeriodSchema] = Field(default_factory=list)
    full_name: str | None = None
    phone: str | None = None
    mail: str | None = None
    company_name: str | None = None
    inn: str | None = None
    company_phone: str | None = None
    company_mail: str | None = None
    address: str | None = None
    note: str | None = None
    permissions: list[str] = Field(default_factory=list)
    actions: UserActionsSchema = Field(default_factory=UserActionsSchema)


class MeResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: MeData
    links: LinkSet = Field(alias="_links")


class SubordinateProfileData(BaseModel):
    user_id: str
    role_id: int
    id_parent: str | None = None
    status: str
    full_name: str | None = None
    phone: str | None = None
    mail: str | None = None
    unavailable_period: "UserUnavailabilityPeriodSchema | None" = None
    unavailable_periods: list[UserUnavailabilityPeriodSchema] = Field(default_factory=list)
    actions: UserActionsSchema = Field(default_factory=UserActionsSchema)


class SubordinateProfileResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: SubordinateProfileData
    links: LinkSet = Field(alias="_links")


class SetSubordinateUnavailabilityPeriodRequest(BaseModel):
    status: str
    started_at: datetime
    ended_at: datetime


class SetSubordinateUnavailabilityPeriodResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: SubordinateProfileData
    links: LinkSet = Field(alias="_links")


class UpdateMyCredentialsRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=255)
    new_password: str = Field(min_length=8, max_length=255)


class UpdateMyProfileRequest(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    mail: str | None = None


class UpdateMyCompanyContactsRequest(BaseModel):
    company_name: str | None = None
    inn: str | None = None
    company_phone: str | None = None
    company_mail: str | None = None
    address: str | None = None
    note: str | None = None


class SetMyUnavailabilityPeriodRequest(BaseModel):
    status: str
    started_at: datetime
    ended_at: datetime


class SetMyUnavailabilityPeriodResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: MeData
    links: LinkSet = Field(alias="_links")


class ManualContractorCreateRequest(BaseModel):
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


class ManualContractorCreateData(BaseModel):
    user_id: str


class ManualContractorCreateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: ManualContractorCreateData
    links: LinkSet = Field(alias="_links")


class ManualContractorUpdateRequest(BaseModel):
    login: str | None = Field(default=None, min_length=3, max_length=128)
    password: str | None = Field(default=None, min_length=6, max_length=72)
    full_name: str | None = Field(default=None, max_length=256)
    phone: str | None = Field(default=None, max_length=64)
    mail: str | None = Field(default=None, max_length=256)
    company_name: str | None = Field(default=None, max_length=256)
    inn: str | None = Field(default=None, max_length=32)
    company_phone: str | None = Field(default=None, max_length=64)
    company_mail: str | None = Field(default=None, max_length=256)
    address: str | None = Field(default=None, max_length=256)
    note: str | None = Field(default=None, max_length=1024)

    @field_validator(
        "login",
        "password",
        "full_name",
        "phone",
        "mail",
        "company_name",
        "inn",
        "company_phone",
        "company_mail",
        "address",
        "note",
        mode="before",
    )
    @classmethod
    def _strip_optional_values(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Значение должно быть строкой")
        normalized = value.strip()
        if not normalized:
            raise ValueError("Updated value cannot be empty")
        return normalized

    @field_validator("password")
    @classmethod
    def _validate_password(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_password_bcrypt_bytes(value)

    @field_validator("phone", "company_phone")
    @classmethod
    def _validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_ru_phone(value)

    @field_validator("mail", "company_mail")
    @classmethod
    def _validate_mail(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_optional_email(value, allow_placeholder=True)

    @field_validator("inn")
    @classmethod
    def _validate_inn(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_inn(value)


class ManualContractorUpdateData(BaseModel):
    user_id: str


class ManualContractorUpdateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: ManualContractorUpdateData
    links: LinkSet = Field(alias="_links")
