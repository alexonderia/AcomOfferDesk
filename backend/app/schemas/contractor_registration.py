from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.contractor_validation import (
    NOT_SPECIFIED_TEXT,
    validate_inn,
    validate_optional_email,
    validate_password_bcrypt_bytes,
    validate_ru_phone,
)
from app.schemas.links import LinkSet

class ContractorEmailVerificationRequest(BaseModel):
    token: str = Field(..., min_length=1, description="Signed Telegram token for contractor registration")
    mail: str = Field(..., min_length=1, max_length=256)

    @field_validator("mail")
    @classmethod
    def _validate_mail(cls, value: str) -> str:
        return validate_optional_email(value, allow_placeholder=False) or value

class ContractorRegistrationRequest(BaseModel):
    token: str = Field(..., min_length=1, description="Signed Telegram token for contractor registration")
    login: str = Field(..., min_length=3, max_length=128)
    password: str = Field(..., min_length=6, max_length=72)
    password_confirm: str = Field(..., min_length=6, max_length=72)
    full_name: str = Field(..., min_length=1, max_length=256)
    phone: str = Field(..., min_length=1, max_length=64)
    company_name: str = Field(..., min_length=1, max_length=256)
    mail: str = Field(default=NOT_SPECIFIED_TEXT, max_length=256)
    inn: str = Field(..., min_length=1, max_length=32)
    company_phone: str = Field(..., min_length=1, max_length=64)
    company_mail: str = Field(default=NOT_SPECIFIED_TEXT, max_length=256)
    address: str = Field(default=NOT_SPECIFIED_TEXT, max_length=256)
    note: str = Field(default=NOT_SPECIFIED_TEXT, max_length=1024)

    @field_validator("password")
    @classmethod
    def _validate_password_bytes(cls, value: str) -> str:
        return validate_password_bcrypt_bytes(value)

    @field_validator("password_confirm")
    @classmethod
    def _validate_password_confirm_bytes(cls, value: str) -> str:
        return validate_password_bcrypt_bytes(value)

    @field_validator("password_confirm")
    @classmethod
    def _validate_password_match(cls, value: str, info) -> str:
        if "password" in info.data and value != info.data["password"]:
            raise ValueError("Пароли не совпадают")
        return value

    @field_validator("phone", "company_phone")
    @classmethod
    def _validate_ru_phone(cls, value: str) -> str:
        return validate_ru_phone(value)


    @field_validator("mail", "company_mail")
    @classmethod
    def _validate_optional_mail(cls, value: str) -> str:
        return validate_optional_email(value, allow_placeholder=True) or value

    @field_validator("inn")
    @classmethod
    def _validate_inn(cls, value: str) -> str:
        return validate_inn(value)


class ContractorRegistrationData(BaseModel):
    user_id: str
    status: str
    tg_user_id: int


class ContractorRegistrationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: ContractorRegistrationData
    links: LinkSet = Field(alias="_links")
