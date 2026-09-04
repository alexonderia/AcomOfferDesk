from pydantic import BaseModel, Field, field_validator

from app.domain.contractor_validation import validate_optional_email


class RegistrationInviteRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    unit_id: int | None = Field(default=None, ge=1)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return validate_optional_email(value.strip().lower(), allow_placeholder=False) or value.strip().lower()


class RegistrationInviteData(BaseModel):
    email: str
    expires_in_seconds: int


class RegistrationInviteResponse(BaseModel):
    data: RegistrationInviteData


class RegistrationInspectData(BaseModel):
    status: str
    email: str | None = None
    role_id: int | None = None
    expires_at: str | None = None
    login: str | None = None
    full_name: str | None = None
    phone: str | None = None
    company_name: str | None = None
    inn: str | None = None
    company_phone: str | None = None


class RegistrationInspectResponse(BaseModel):
    data: RegistrationInspectData


class RegistrationSubmitRequest(BaseModel):
    token: str = Field(..., min_length=20, max_length=4096)
    login: str = Field(..., min_length=3, max_length=128)
    password: str | None = Field(default=None, min_length=12, max_length=128)
    password_confirmation: str | None = Field(default=None, min_length=12, max_length=128)
    email: str = Field(..., min_length=5, max_length=255)
    full_name: str = Field(..., min_length=1, max_length=256)
    phone: str = Field(..., min_length=1, max_length=64)
    company_name: str = Field(..., min_length=1, max_length=256)
    inn: str = Field(..., min_length=10, max_length=12)
    company_phone: str = Field(..., min_length=1, max_length=64)
    company_mail: str | None = Field(default=None, max_length=255)
    address: str | None = Field(default=None, max_length=256)
    note: str | None = Field(default=None, max_length=1024)


class RegistrationSubmitData(BaseModel):
    user_id: str
    status: str
    email: str


class RegistrationSubmitResponse(BaseModel):
    data: RegistrationSubmitData
    detail: str
