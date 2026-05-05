from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.contractor_validation import validate_optional_email
from app.schemas.links import LinkSet


class LoginRequest(BaseModel):
    login: str = Field(..., min_length=3, max_length=128)
    password: str = Field(..., min_length=1, max_length=72)

    @field_validator("password")
    @classmethod
    def _validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password too long (max 72 bytes)")
        return value


class AuthSessionData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    access_token_expires_at: int
    user_id: str
    login: str
    role_id: int
    status: str
    auth_provider: str = "keycloak"
    business_access: bool = False
    onboarding_state: str | None = None
    permissions: list[str] = Field(default_factory=list)


class AuthSessionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    data: AuthSessionData
    links: LinkSet = Field(alias="_links")


LoginData = AuthSessionData
LoginResponse = AuthSessionResponse


class RegisterUserRequest(BaseModel):
    login: str = Field(..., min_length=3, max_length=128)
    password: str | None = Field(default=None, min_length=6, max_length=72)
    role_id: int = Field(..., ge=1)
    id_parent: str | None = Field(default=None, min_length=3, max_length=128)
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, min_length=1, max_length=255)
    mail: str | None = Field(default=None, min_length=1, max_length=255)

    @field_validator("password")
    @classmethod
    def _validate_password_bytes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password too long (max 72 bytes)")
        return value

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
    model_config = ConfigDict(populate_by_name=True)

    data: RegisterUserData
    links: LinkSet = Field(alias="_links")
