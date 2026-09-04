from pydantic import BaseModel, Field, field_validator

from app.domain.contractor_validation import validate_optional_email


class AuthSessionData(BaseModel):
    user_id: str
    login: str
    role_id: int
    role: str
    status: str
    auth_provider: str = "iam"
    business_access: bool = False
    onboarding_state: str | None = None
    permissions: list[str] = Field(default_factory=list)


class AuthSessionResponse(BaseModel):
    data: AuthSessionData


class RegisterUserRequest(BaseModel):
    login: str = Field(..., min_length=3, max_length=128)
    role_id: int = Field(..., ge=1)
    id_parent: str | None = Field(default=None, min_length=3, max_length=128)
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, min_length=1, max_length=255)
    mail: str | None = Field(default=None, min_length=1, max_length=255)
    unit_id: int | None = Field(default=None, ge=1)

    @field_validator("mail")
    @classmethod
    def _validate_mail(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            return None
        return validate_optional_email(normalized, allow_placeholder=False)


class RegisterUserData(BaseModel):
    user_id: str
    role_id: int
    status: str


class RegisterUserResponse(BaseModel):
    data: RegisterUserData
