from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator

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
    email_enabled: bool = True


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
    password: SecretStr | None = Field(default=None, min_length=12, max_length=128)
    password_confirmation: SecretStr | None = Field(default=None, min_length=12, max_length=128)

    @model_validator(mode="after")
    def _password_confirmation(self):
        self.login = self.login.strip()
        if len(self.login) < 3:
            raise ValueError("Логин должен содержать от 3 до 128 символов")
        if self.password is not None or self.password_confirmation is not None:
            if self.password is None or self.password_confirmation is None or self.password.get_secret_value() != self.password_confirmation.get_secret_value():
                raise ValueError("Пароли не совпадают")
        return self

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
    visible_to_creator: bool = True


class RegisterUserResponse(BaseModel):
    data: RegisterUserData


class PasswordChangeRequest(BaseModel):
    current_password: SecretStr = Field(min_length=1, max_length=128)
    new_password: SecretStr = Field(min_length=12, max_length=128)
    password_confirmation: SecretStr = Field(min_length=12, max_length=128)

    @model_validator(mode="after")
    def _confirmation(self):
        if self.new_password.get_secret_value() != self.password_confirmation.get_secret_value():
            raise ValueError("Пароли не совпадают")
        return self
