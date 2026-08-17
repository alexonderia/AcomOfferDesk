from __future__ import annotations

import json

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="IAM_", extra="ignore")

    app_env: str = Field(default="development", validation_alias="APP_ENV")
    database_url: str
    public_base_url: str = "http://localhost:8080/iam"
    issuer: str = "http://localhost:8080/iam"
    audience: str = "acomofferdesk"
    allowed_redirect_uris_csv: str = Field(
        default="http://localhost:8080/api/v1/auth/callback",
        validation_alias="IAM_ALLOWED_REDIRECT_URIS",
    )
    internal_service_token: str
    signing_private_key: str
    signing_public_key: str
    signing_kid: str = "iam-signing-1"
    signing_verification_keys: dict[str, str] = Field(default_factory=dict)
    auth_request_secret: str
    token_hash_secret: str
    access_token_ttl_seconds: int = 300
    authorization_code_ttl_seconds: int = 60
    action_token_ttl_seconds: int = 3600
    refresh_idle_ttl_seconds: int = 1800
    refresh_max_ttl_seconds: int = 43200
    login_max_failures: int = 5
    login_lock_seconds: int = 900
    login_rate_limit_attempts: int = 20
    login_rate_limit_window_seconds: int = 60
    auth_request_cookie_name: str = "iam_auth_request"
    browser_session_cookie_name: str = "iam_browser_session"
    browser_session_ttl_seconds: int = 43200
    cookie_secure: bool = False

    @field_validator("signing_private_key", "signing_public_key", mode="before")
    @classmethod
    def _normalize_pem(cls, value: str) -> str:
        return value.replace("\\n", "\n").strip()

    @field_validator("signing_verification_keys", mode="before")
    @classmethod
    def _normalize_verification_keys(cls, value: object) -> dict[str, str]:
        if value is None or value == "":
            return {}
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    "IAM_SIGNING_VERIFICATION_KEYS must be a JSON object"
                ) from exc
        if not isinstance(value, dict):
            raise ValueError("IAM_SIGNING_VERIFICATION_KEYS must be a JSON object")
        return {
            str(kid).strip(): str(public_key).replace("\\n", "\n").strip()
            for kid, public_key in value.items()
        }

    @model_validator(mode="after")
    def _validate_security_settings(self) -> "Settings":
        self.public_base_url = self.public_base_url.rstrip("/")
        self.issuer = self.issuer.rstrip("/")
        self.signing_kid = self.signing_kid.strip()
        if not self.signing_kid:
            raise ValueError("IAM_SIGNING_KID must not be empty")
        if self.app_env.strip().lower() == "production" or self.public_base_url.startswith("https://"):
            self.cookie_secure = True
        if not self.allowed_redirect_uris:
            raise ValueError("IAM_ALLOWED_REDIRECT_URIS must not be empty")
        for name in (
            "internal_service_token",
            "auth_request_secret",
            "token_hash_secret",
        ):
            if len(getattr(self, name)) < 32:
                raise ValueError(f"IAM_{name.upper()} must contain at least 32 characters")
        if "BEGIN PRIVATE KEY" not in self.signing_private_key:
            raise ValueError("IAM_SIGNING_PRIVATE_KEY must be a PEM private key")
        if "BEGIN PUBLIC KEY" not in self.signing_public_key:
            raise ValueError("IAM_SIGNING_PUBLIC_KEY must be a PEM public key")
        try:
            private_key = serialization.load_pem_private_key(
                self.signing_private_key.encode("utf-8"),
                password=None,
            )
            public_key = serialization.load_pem_public_key(
                self.signing_public_key.encode("utf-8")
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("IAM signing keys must contain valid PEM data") from exc
        if not isinstance(private_key, RSAPrivateKey) or not isinstance(public_key, RSAPublicKey):
            raise ValueError("IAM signing keys must be RSA keys")
        if private_key.public_key().public_numbers() != public_key.public_numbers():
            raise ValueError("IAM signing private/public keys do not match")
        for kid, verification_key_pem in self.signing_verification_keys.items():
            if not kid:
                raise ValueError("IAM signing verification key ids must not be empty")
            if kid == self.signing_kid and verification_key_pem != self.signing_public_key:
                raise ValueError(
                    "IAM active signing key conflicts with IAM_SIGNING_VERIFICATION_KEYS"
                )
            try:
                verification_key = serialization.load_pem_public_key(
                    verification_key_pem.encode("utf-8")
                )
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"IAM verification key {kid!r} must contain valid PEM data"
                ) from exc
            if not isinstance(verification_key, RSAPublicKey):
                raise ValueError(f"IAM verification key {kid!r} must be an RSA public key")
        if not 60 <= self.access_token_ttl_seconds <= 900:
            raise ValueError("IAM access token TTL must be between 60 and 900 seconds")
        if not 60 <= self.browser_session_ttl_seconds <= self.refresh_max_ttl_seconds:
            raise ValueError("IAM browser session TTL must not exceed refresh session TTL")
        return self

    @property
    def allowed_redirect_uris(self) -> list[str]:
        return [
            item.strip()
            for item in self.allowed_redirect_uris_csv.split(",")
            if item.strip()
        ]

    @property
    def verification_public_keys(self) -> dict[str, str]:
        return {
            **self.signing_verification_keys,
            self.signing_kid: self.signing_public_key,
        }

    def signing_configuration_is_ready(self) -> bool:
        try:
            private_key = serialization.load_pem_private_key(
                self.signing_private_key.encode("utf-8"),
                password=None,
            )
            public_keys = {
                kid: serialization.load_pem_public_key(public_key.encode("utf-8"))
                for kid, public_key in self.verification_public_keys.items()
            }
            active_public_key = public_keys[self.signing_kid]
        except (KeyError, TypeError, ValueError):
            return False
        return (
            isinstance(private_key, RSAPrivateKey)
            and isinstance(active_public_key, RSAPublicKey)
            and all(isinstance(public_key, RSAPublicKey) for public_key in public_keys.values())
            and private_key.public_key().public_numbers()
            == active_public_key.public_numbers()
        )


settings = Settings()
