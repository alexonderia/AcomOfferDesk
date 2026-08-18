from __future__ import annotations

import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator


class TokenExchangeRequest(BaseModel):
    code: str = Field(min_length=20, max_length=512)
    code_verifier: str = Field(min_length=43, max_length=128)
    redirect_uri: str = Field(min_length=8, max_length=2048)
    ip_address: str | None = Field(default=None, max_length=64)
    user_agent: str | None = Field(default=None, max_length=1024)


class TokenBundleResponse(BaseModel):
    access_token: str
    access_token_expires_at: int
    refresh_token: str
    refresh_token_expires_at: int


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=1024)


class LogoutRequest(RefreshRequest):
    reason: str = Field(default="logout", min_length=1, max_length=128)


class AccountPutRequest(BaseModel):
    login: str = Field(min_length=3, max_length=128)
    role: str = Field(min_length=2, max_length=128)
    auth_status: Literal["pending", "active", "blocked", "disabled"] = "pending"

    @field_validator("login", "role")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()


class AccountResponse(BaseModel):
    id: uuid.UUID
    login: str
    role: str
    auth_status: str
    created: bool = False


class RegistrationCredentialsPutRequest(BaseModel):
    login: str = Field(min_length=3, max_length=128)
    role: str = Field(min_length=2, max_length=128)
    auth_status: Literal["pending"] = "pending"
    password: str = Field(min_length=12, max_length=128)
    replace_password: bool = False

    @field_validator("login")
    @classmethod
    def _strip_login(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 3:
            raise ValueError("login is too short")
        return normalized

    @field_validator("role")
    @classmethod
    def _strip_role(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("role is too short")
        return normalized


class AccountCredentialStateResponse(BaseModel):
    id: uuid.UUID
    login: str
    role: str
    auth_status: str
    password_set: bool
    required_actions: list[str] = Field(default_factory=list)


class RegistrationCredentialsResponse(AccountCredentialStateResponse):
    created: bool = False


class AccountPermissionGrantsPutRequest(BaseModel):
    permissions: list[Annotated[str, Field(min_length=2, max_length=128)]] = Field(
        max_length=10_000
    )

    @field_validator("permissions")
    @classmethod
    def _normalize_permissions(cls, values: list[str]) -> list[str]:
        normalized = {value.strip() for value in values}
        if any(not value for value in normalized):
            raise ValueError("permission name cannot be empty")
        return sorted(normalized)


class AccountPermissionsResponse(BaseModel):
    permissions_from_role: list[str]
    individually_granted_permissions: list[str]
    effective_permissions: list[str]


class AccountRolePatchRequest(BaseModel):
    role: str = Field(min_length=2, max_length=128)
    actor_account_id: uuid.UUID | None = None
    actor_session_id: uuid.UUID | None = None


class AccountStatusPatchRequest(BaseModel):
    auth_status: Literal["pending", "active", "blocked", "disabled"]
    actor_account_id: uuid.UUID | None = None
    actor_session_id: uuid.UUID | None = None


class RevokeAllRequest(BaseModel):
    reason: str = Field(default="revoke_all", min_length=1, max_length=128)
    actor_account_id: uuid.UUID | None = None
    actor_session_id: uuid.UUID | None = None


class ActionTokenRequest(BaseModel):
    purpose: Literal[
        "password_setup",
        "password_reset",
        "verify_email",
        "first_access",
        "profile_change",
    ]
    context: dict[str, str] | None = None


class ActionTokenResponse(BaseModel):
    token: str
    expires_at: int
    purpose: str


class ActionTokenConsumeRequest(BaseModel):
    token: str = Field(min_length=20, max_length=512)
    purpose: Literal[
        "password_setup",
        "password_reset",
        "verify_email",
        "first_access",
        "profile_change",
    ]
    new_password: str | None = Field(default=None, min_length=12, max_length=128)


class ActionTokenConsumeResponse(BaseModel):
    account_id: uuid.UUID
    purpose: str
    auth_status: str
    context: dict | None = None


class RbacRoleInput(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    permissions: list[str]


class RbacSeedRequest(BaseModel):
    roles: list[RbacRoleInput]


class RbacReportResponse(BaseModel):
    roles: dict[str, list[str]]


class ReconciliationRequest(BaseModel):
    account_ids: list[uuid.UUID] = Field(max_length=100_000)


class ReconciliationResponse(BaseModel):
    orphan_iam_account_ids: list[uuid.UUID]
    missing_iam_account_ids: list[uuid.UUID]
