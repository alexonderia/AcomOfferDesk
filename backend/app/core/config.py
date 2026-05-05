from __future__ import annotations

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_int_list(value: str | list[int] | None) -> list[int]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if not value:
        return []
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def _parse_str_list(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [item.strip() for item in value if item and item.strip()]
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    app_env: str = Field(default="development", validation_alias=AliasChoices("APP_ENV", "ENVIRONMENT"))
    database_url: str = Field(..., validation_alias="DATABASE_URL")
    jwt_secret: str = Field(..., validation_alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_exp_minutes: int = Field(default=60, validation_alias="JWT_EXP_MINUTES")
    access_token_ttl_seconds: int = Field(default=300, validation_alias="ACCESS_TOKEN_TTL_SECONDS")
    refresh_token_idle_ttl_seconds: int = Field(default=1800, validation_alias="REFRESH_TOKEN_IDLE_TTL_SECONDS")
    refresh_token_max_ttl_seconds: int = Field(default=43200, validation_alias="REFRESH_TOKEN_MAX_TTL_SECONDS")
    refresh_cookie_name: str = Field(default="acom_refresh_token", validation_alias="REFRESH_COOKIE_NAME")
    refresh_cookie_secure: bool = Field(default=False, validation_alias="REFRESH_COOKIE_SECURE")
    refresh_cookie_samesite: str = Field(default="lax", validation_alias="REFRESH_COOKIE_SAMESITE")
    refresh_cookie_domain: str | None = Field(default=None, validation_alias="REFRESH_COOKIE_DOMAIN")
    refresh_token_secret: str | None = Field(default=None, validation_alias="REFRESH_TOKEN_SECRET")

    keycloak_enabled: bool = Field(default=False, validation_alias="KEYCLOAK_ENABLED")
    keycloak_realm: str = Field(default="acom-offerdesk", validation_alias="KEYCLOAK_REALM")
    keycloak_client_id: str = Field(default="acom-offerdesk-web", validation_alias="KEYCLOAK_CLIENT_ID")
    keycloak_internal_base_url: str = Field(
        default="http://keycloak:8080/iam",
        validation_alias="KEYCLOAK_INTERNAL_BASE_URL",
    )
    keycloak_public_base_url: str | None = Field(default=None, validation_alias="KEYCLOAK_PUBLIC_BASE_URL")
    keycloak_issuer_url: str | None = Field(default=None, validation_alias="KEYCLOAK_ISSUER_URL")
    keycloak_jwks_cache_ttl_seconds: int = Field(
        default=300,
        validation_alias="KEYCLOAK_JWKS_CACHE_TTL_SECONDS",
    )
    keycloak_http_timeout_seconds: float = Field(
        default=10.0,
        validation_alias="KEYCLOAK_HTTP_TIMEOUT_SECONDS",
    )
    keycloak_refresh_cookie_name: str = Field(
        default="acom_oidc_refresh",
        validation_alias="KEYCLOAK_REFRESH_COOKIE_NAME",
    )
    keycloak_state_cookie_name: str = Field(
        default="acom_oidc_state",
        validation_alias="KEYCLOAK_STATE_COOKIE_NAME",
    )
    keycloak_bootstrap_binding_enabled: bool = Field(
        default=True,
        validation_alias="KEYCLOAK_BOOTSTRAP_BINDING_ENABLED",
    )
    keycloak_bootstrap_app_username: str = Field(
        default="superadmin",
        validation_alias="KEYCLOAK_BOOTSTRAP_APP_USERNAME",
    )
    keycloak_admin_realm: str = Field(
        default="master",
        validation_alias=AliasChoices("KEYCLOAK_ADMIN_REALM", "KC_BOOTSTRAP_ADMIN_REALM"),
    )
    keycloak_admin_client_id: str = Field(
        default="admin-cli",
        validation_alias="KEYCLOAK_ADMIN_CLIENT_ID",
    )
    keycloak_admin_username: str | None = Field(
        default=None,
        validation_alias=AliasChoices("KEYCLOAK_ADMIN_USERNAME", "KC_BOOTSTRAP_ADMIN_USERNAME"),
    )
    keycloak_admin_password: str | None = Field(
        default=None,
        validation_alias=AliasChoices("KEYCLOAK_ADMIN_PASSWORD", "KC_BOOTSTRAP_ADMIN_PASSWORD"),
    )
    keycloak_dev_auto_link_by_username_enabled: bool = Field(
        default=False,
        validation_alias="KEYCLOAK_DEV_AUTO_LINK_BY_USERNAME_ENABLED",
    )
    keycloak_prod_auto_link_by_verified_email_enabled: bool = Field(
        default=False,
        validation_alias="KEYCLOAK_PROD_AUTO_LINK_BY_VERIFIED_EMAIL_ENABLED",
    )

    superadmin_role_id: int = 1
    admin_role_id: int = 2
    contractor_role_id: int = 3
    project_manager_role_id: int = 4
    lead_economist_role_id: int = 5
    economist_role_id: int = 6
    operator_role_id: int = 7
    telegram_legacy_enabled: bool = Field(
        default=False,
        validation_alias="LEGACY_TELEGRAM_ENABLED",
    )
    tg_link_secret: str | None = Field(
        default=None,
        validation_alias=AliasChoices("TG_LINK_SECRET", "TG_LINK_SALT"),
    )
    public_backend_base_url: str | None = Field(default=None, validation_alias="PUBLIC_BACKEND_BASE_URL")
    web_base_url: str | None = Field(default=None, validation_alias="WEB_BASE_URL")
    tg_bot_public_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("TG_BOT_PUBLIC_URL", "TG_BOT_LINK"),
    )
    email_address: str = Field(..., validation_alias="EMAIL_ADDRESS")
    email_from_name: str = Field(default="AcomOfferDesk", validation_alias="EMAIL_FROM_NAME")
    email_app_password: str = Field(..., validation_alias="EMAIL_APP_PASSWORD")
    smtp_host: str = Field(..., validation_alias="SMTP_HOST")
    smtp_port: int = Field(default=465, validation_alias="SMTP_PORT")
    rabbitmq_url: str = Field(default="amqp://guest:guest@rabbitmq:5672/", validation_alias="RABBITMQ_URL")
    email_verification_secret: str = Field(..., validation_alias="EMAIL_VERIFICATION_SECRET")
    email_verification_ttl_seconds: int = Field(default=3600, validation_alias="EMAIL_VERIFICATION_TTL_SECONDS")
    reply_email_token_secret: str | None = Field(
        default=None,
        validation_alias=AliasChoices("REPLY_EMAIL_TOKEN_SECRET", "EMAIL_REPLY_SECRET"),
    )
    reply_email_ttl_seconds: int = Field(
        default=604800,
        validation_alias=AliasChoices("REPLY_EMAIL_TTL_SECONDS", "EMAIL_REPLY_TTL_SECONDS"),
    )
    imap_host: str | None = Field(default=None, validation_alias="IMAP_HOST")
    imap_port: int = Field(default=993, validation_alias="IMAP_PORT")
    imap_username: str | None = Field(
        default=None,
        validation_alias=AliasChoices("IMAP_USERNAME", "EMAIL_ADDRESS"),
    )
    imap_password: str | None = Field(
        default=None,
        validation_alias=AliasChoices("IMAP_PASSWORD", "EMAIL_APP_PASSWORD"),
    )
    imap_mailbox: str = Field(default="INBOX", validation_alias="IMAP_MAILBOX")
    request_mailbox_poll_limit: int = Field(default=20, validation_alias="REQUEST_MAILBOX_POLL_LIMIT")
    request_mailbox_poll_interval_seconds: int = Field(
        default=60,
        validation_alias="REQUEST_MAILBOX_POLL_INTERVAL_SECONDS",
    )
    s3_endpoint: str = Field(..., validation_alias="S3_ENDPOINT")
    s3_public_endpoint: str | None = Field(default=None, validation_alias="S3_PUBLIC_ENDPOINT")
    s3_access_key: str = Field(..., validation_alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field(..., validation_alias="S3_SECRET_KEY")
    s3_bucket: str = Field(..., validation_alias="S3_BUCKET")
    s3_secure: bool = Field(default=False, validation_alias="S3_SECURE")
    s3_presigned_get_ttl_seconds: int = Field(default=300, validation_alias="S3_PRESIGNED_GET_TTL_SECONDS")
    max_upload_size_bytes: int = Field(default=10 * 1024 * 1024, validation_alias="MAX_UPLOAD_SIZE_BYTES")
    tg_register_ttl_seconds: int = Field(default=86400, validation_alias="TG_REGISTER_TTL_SECONDS")
    tg_auth_ttl_seconds: int = Field(default=600, validation_alias="TG_AUTH_TTL_SECONDS")
    tg_request_ttl_seconds: int = Field(default=604800, validation_alias="TG_REQUEST_TTL_SECONDS")
    allowed_creation_role_ids: list[int] = Field(default_factory=lambda: [2, 3, 4, 5, 6, 7])
    cors_allow_origins: list[str] = Field(
        default_factory=list,
        validation_alias="CORS_ALLOW_ORIGINS",
    )

    @field_validator("allowed_creation_role_ids", mode="before")
    @classmethod
    def _validate_allowed_creation_role_ids(cls, value: str | list[int] | None) -> list[int]:
        return _parse_int_list(value)

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _validate_cors_allow_origins(cls, value: str | list[str] | None) -> list[str]:
        return _parse_str_list(value)

    @model_validator(mode="after")
    def _normalize(self) -> "Settings":
        self.app_env = self.app_env.strip().lower() or "development"
        self.superadmin_role_id = 1
        self.admin_role_id = 2
        self.contractor_role_id = 3
        self.project_manager_role_id = 4
        self.lead_economist_role_id = 5
        self.economist_role_id = 6
        self.operator_role_id = 7

        self.refresh_cookie_samesite = self.refresh_cookie_samesite.lower().strip() or "lax"
        if self.refresh_cookie_samesite not in {"lax", "strict", "none"}:
            self.refresh_cookie_samesite = "lax"

        public_bases = [self.public_backend_base_url, self.web_base_url, self.keycloak_public_base_url, self.keycloak_issuer_url]
        if any((base or "").strip().lower().startswith("https://") for base in public_bases):
            self.refresh_cookie_secure = True

        if not self.refresh_token_secret:
            self.refresh_token_secret = self.jwt_secret

        self.s3_endpoint = self.s3_endpoint.strip()
        if self.s3_public_endpoint is not None:
            self.s3_public_endpoint = self.s3_public_endpoint.strip() or None
        self.s3_bucket = self.s3_bucket.strip()
        if not self.s3_endpoint:
            raise ValueError("S3_ENDPOINT must not be blank")
        if not self.s3_bucket:
            raise ValueError("S3_BUCKET must not be blank")
        if self.s3_presigned_get_ttl_seconds <= 0:
            self.s3_presigned_get_ttl_seconds = 300
        if self.max_upload_size_bytes <= 0:
            self.max_upload_size_bytes = 10 * 1024 * 1024

        self.keycloak_internal_base_url = self.keycloak_internal_base_url.rstrip("/")
        if self.keycloak_public_base_url is not None:
            self.keycloak_public_base_url = self.keycloak_public_base_url.rstrip("/") or None
        if self.keycloak_issuer_url is not None:
            self.keycloak_issuer_url = self.keycloak_issuer_url.rstrip("/") or None
        self.keycloak_admin_realm = self.keycloak_admin_realm.strip() or "master"
        self.keycloak_admin_client_id = self.keycloak_admin_client_id.strip() or "admin-cli"
        if self.keycloak_admin_username is not None:
            self.keycloak_admin_username = self.keycloak_admin_username.strip() or None
        if self.keycloak_admin_password is not None:
            self.keycloak_admin_password = self.keycloak_admin_password.strip() or None
        self.keycloak_bootstrap_app_username = self.keycloak_bootstrap_app_username.strip() or "superadmin"
        if self.keycloak_jwks_cache_ttl_seconds <= 0:
            self.keycloak_jwks_cache_ttl_seconds = 300
        if self.keycloak_http_timeout_seconds <= 0:
            self.keycloak_http_timeout_seconds = 10.0
        if self.keycloak_dev_auto_link_by_username_enabled and self.keycloak_prod_auto_link_by_verified_email_enabled:
            raise ValueError(
                "KEYCLOAK_DEV_AUTO_LINK_BY_USERNAME_ENABLED and "
                "KEYCLOAK_PROD_AUTO_LINK_BY_VERIFIED_EMAIL_ENABLED cannot be enabled together"
            )
        if self.app_env == "production" and self.keycloak_dev_auto_link_by_username_enabled:
            raise ValueError("KEYCLOAK_DEV_AUTO_LINK_BY_USERNAME_ENABLED cannot be enabled in production")
        return self

    @property
    def resolved_cors_allow_origins(self) -> list[str]:
        origins = list(self.cors_allow_origins)
        if self.web_base_url and self.web_base_url not in origins:
            origins.append(self.web_base_url)
        return origins

    @property
    def resolved_refresh_token_secret(self) -> str:
        return self.refresh_token_secret or self.jwt_secret

    @property
    def resolved_keycloak_public_base_url(self) -> str:
        if self.keycloak_public_base_url:
            return self.keycloak_public_base_url
        if self.web_base_url:
            return f"{self.web_base_url.rstrip('/')}/iam"
        return "http://localhost:8080/iam"

    @property
    def resolved_keycloak_issuer_url(self) -> str:
        if self.keycloak_issuer_url:
            return self.keycloak_issuer_url
        return f"{self.resolved_keycloak_public_base_url}/realms/{self.keycloak_realm}"

    @property
    def keycloak_internal_realm_base_url(self) -> str:
        return f"{self.keycloak_internal_base_url}/realms/{self.keycloak_realm}"

    @property
    def keycloak_token_endpoint(self) -> str:
        return f"{self.keycloak_internal_realm_base_url}/protocol/openid-connect/token"

    @property
    def keycloak_authorization_endpoint(self) -> str:
        return f"{self.resolved_keycloak_issuer_url}/protocol/openid-connect/auth"

    @property
    def keycloak_logout_endpoint(self) -> str:
        return f"{self.keycloak_internal_realm_base_url}/protocol/openid-connect/logout"

    @property
    def keycloak_jwks_uri(self) -> str:
        return f"{self.keycloak_internal_realm_base_url}/protocol/openid-connect/certs"

    @property
    def keycloak_userinfo_endpoint(self) -> str:
        return f"{self.keycloak_internal_realm_base_url}/protocol/openid-connect/userinfo"

    @property
    def keycloak_callback_url(self) -> str:
        base = (self.public_backend_base_url or self.web_base_url or "http://localhost:8080").rstrip("/")
        return f"{base}/api/v1/auth/callback"


settings = Settings()
