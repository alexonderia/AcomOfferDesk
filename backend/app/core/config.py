from __future__ import annotations

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
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
    ws_ticket_ttl_seconds: int = Field(default=30, validation_alias="WS_TICKET_TTL_SECONDS")
    ws_legacy_query_token_enabled: bool = Field(default=False, validation_alias="WS_LEGACY_QUERY_TOKEN_ENABLED")
    refresh_token_idle_ttl_seconds: int = Field(default=1800, validation_alias="REFRESH_TOKEN_IDLE_TTL_SECONDS")
    refresh_token_max_ttl_seconds: int = Field(default=43200, validation_alias="REFRESH_TOKEN_MAX_TTL_SECONDS")
    refresh_cookie_name: str = Field(default="acom_refresh_token", validation_alias="REFRESH_COOKIE_NAME")
    refresh_cookie_secure: bool = Field(default=False, validation_alias="REFRESH_COOKIE_SECURE")
    refresh_cookie_samesite: str = Field(default="lax", validation_alias="REFRESH_COOKIE_SAMESITE")
    refresh_cookie_domain: str | None = Field(default=None, validation_alias="REFRESH_COOKIE_DOMAIN")
    refresh_token_secret: str | None = Field(default=None, validation_alias="REFRESH_TOKEN_SECRET")

    iam_internal_base_url: str = Field(default="http://iam:8100", validation_alias="IAM_INTERNAL_BASE_URL")
    iam_public_base_url: str | None = Field(default=None, validation_alias="IAM_PUBLIC_BASE_URL")
    iam_issuer: str | None = Field(default=None, validation_alias="IAM_ISSUER")
    iam_audience: str = Field(default="acomofferdesk", validation_alias="IAM_AUDIENCE")
    iam_signing_public_key: str | None = Field(default=None, validation_alias="IAM_SIGNING_PUBLIC_KEY")
    iam_signing_kid: str = Field(default="iam-signing-1", validation_alias="IAM_SIGNING_KID")
    iam_internal_service_token: str = Field(
        default="development-only-iam-service-token-change-me",
        validation_alias="IAM_INTERNAL_SERVICE_TOKEN",
    )
    iam_http_timeout_seconds: float = Field(default=10.0, validation_alias="IAM_HTTP_TIMEOUT_SECONDS")
    iam_access_cookie_name: str = Field(default="acom_iam_access", validation_alias="IAM_ACCESS_COOKIE_NAME")
    iam_refresh_cookie_name: str = Field(default="acom_iam_refresh", validation_alias="IAM_REFRESH_COOKIE_NAME")
    iam_state_cookie_name: str = Field(default="acom_iam_flow", validation_alias="IAM_STATE_COOKIE_NAME")
    iam_flow_recovery_cookie_name: str = Field(
        default="acom_iam_flow_recovery",
        validation_alias="IAM_FLOW_RECOVERY_COOKIE_NAME",
    )
    iam_browser_session_cookie_name: str = Field(
        default="iam_browser_session",
        validation_alias="IAM_BROWSER_SESSION_COOKIE_NAME",
    )
    iam_csrf_cookie_name: str = Field(default="acom_csrf", validation_alias="IAM_CSRF_COOKIE_NAME")

    superadmin_role_id: int = 1
    admin_role_id: int = 2
    contractor_role_id: int = 3
    project_manager_role_id: int = 4
    lead_economist_role_id: int = 5
    economist_role_id: int = 6
    operator_role_id: int = 7
    security_officer_role_id: int = 8
    public_backend_base_url: str | None = Field(default=None, validation_alias="PUBLIC_BACKEND_BASE_URL")
    web_base_url: str | None = Field(default=None, validation_alias="WEB_BASE_URL")
    email_address: str = Field(..., validation_alias="EMAIL_ADDRESS")
    email_from_name: str = Field(default="AcomOfferDesk", validation_alias="EMAIL_FROM_NAME")
    email_app_password: str = Field(..., validation_alias="EMAIL_APP_PASSWORD")
    smtp_host: str = Field(..., validation_alias="SMTP_HOST")
    smtp_port: int = Field(default=465, validation_alias="SMTP_PORT")
    smtp_security: str = Field(default="auto", validation_alias="SMTP_SECURITY")
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
    contractor_invite_max_emails_per_request: int = Field(
        default=50,
        validation_alias="CONTRACTOR_INVITE_MAX_EMAILS_PER_REQUEST",
    )
    invitation_portal_url: str | None = Field(
        default=None,
        validation_alias="INVITATION_PORTAL_URL",
    )
    invitation_contact_name: str | None = Field(
        default="Владислав Хлистун",
        validation_alias="INVITATION_CONTACT_NAME",
    )
    invitation_contact_email: str | None = Field(
        default="VKhlistun@alabuga.ru",
        validation_alias="INVITATION_CONTACT_EMAIL",
    )
    invitation_contact_phone: str | None = Field(
        default="+7 927 455-80-89",
        validation_alias="INVITATION_CONTACT_PHONE",
    )
    invitation_contact_text: str | None = Field(
        default=None,
        validation_alias="INVITATION_CONTACT_TEXT",
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
    chat_unread_email_delay_seconds: int = Field(
        default=3600,
        validation_alias="CHAT_UNREAD_EMAIL_DELAY_SECONDS",
    )
    s3_endpoint: str = Field(..., validation_alias="S3_ENDPOINT")
    s3_public_endpoint: str | None = Field(default=None, validation_alias="S3_PUBLIC_ENDPOINT")
    s3_access_key: str = Field(..., validation_alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field(..., validation_alias="S3_SECRET_KEY")
    s3_bucket: str = Field(..., validation_alias="S3_BUCKET")
    s3_secure: bool = Field(default=False, validation_alias="S3_SECURE")
    s3_presigned_get_ttl_seconds: int = Field(default=300, validation_alias="S3_PRESIGNED_GET_TTL_SECONDS")
    max_upload_size_bytes: int = Field(default=5 * 1024 * 1024, validation_alias="MAX_UPLOAD_SIZE_BYTES")
    file_guard_enabled: bool = Field(default=True, validation_alias="FILE_GUARD_ENABLED")
    file_guard_url: str = Field(default="http://file_guard:8080", validation_alias="FILE_GUARD_URL")
    file_guard_timeout_seconds: float = Field(default=10.0, validation_alias="FILE_GUARD_TIMEOUT_SECONDS")
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
        self.security_officer_role_id = 8

        self.refresh_cookie_samesite = self.refresh_cookie_samesite.lower().strip() or "lax"
        if self.refresh_cookie_samesite not in {"lax", "strict", "none"}:
            self.refresh_cookie_samesite = "lax"

        public_bases = [self.public_backend_base_url, self.web_base_url]
        if self.app_env == "production" or any(
            (base or "").strip().lower().startswith("https://") for base in public_bases
        ):
            self.refresh_cookie_secure = True

        if not self.refresh_token_secret:
            self.refresh_token_secret = self.jwt_secret

        self.iam_internal_base_url = self.iam_internal_base_url.rstrip("/") or "http://iam:8100"
        if self.iam_public_base_url is not None:
            self.iam_public_base_url = self.iam_public_base_url.rstrip("/") or None
        if self.iam_issuer is not None:
            self.iam_issuer = self.iam_issuer.rstrip("/") or None
        if self.iam_signing_public_key is not None:
            self.iam_signing_public_key = self.iam_signing_public_key.replace("\\n", "\n").strip() or None
        self.iam_audience = self.iam_audience.strip() or "acomofferdesk"
        self.iam_signing_kid = self.iam_signing_kid.strip() or "iam-signing-1"
        if self.iam_http_timeout_seconds <= 0:
            self.iam_http_timeout_seconds = 10.0
        if self.app_env == "production":
            if not self.iam_signing_public_key:
                raise ValueError("IAM_SIGNING_PUBLIC_KEY is required in production")
            try:
                signing_key = serialization.load_pem_public_key(
                    self.iam_signing_public_key.encode("utf-8")
                )
            except (TypeError, ValueError) as exc:
                raise ValueError("IAM_SIGNING_PUBLIC_KEY must contain valid PEM data") from exc
            if not isinstance(signing_key, RSAPublicKey):
                raise ValueError("IAM_SIGNING_PUBLIC_KEY must be an RSA public key")
            if self.iam_internal_service_token == "development-only-iam-service-token-change-me":
                raise ValueError("IAM_INTERNAL_SERVICE_TOKEN must be configured in production")

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
            self.max_upload_size_bytes = 5 * 1024 * 1024
        self.file_guard_url = self.file_guard_url.rstrip("/") or "http://file_guard:8080"
        if self.file_guard_timeout_seconds <= 0:
            self.file_guard_timeout_seconds = 10.0
        self.smtp_security = self.smtp_security.strip().lower() or "auto"
        if self.smtp_security not in {"auto", "ssl", "starttls", "plain"}:
            raise ValueError("SMTP_SECURITY must be one of: auto, ssl, starttls, plain")
        if self.contractor_invite_max_emails_per_request <= 0:
            self.contractor_invite_max_emails_per_request = 50
        if self.invitation_portal_url is not None:
            self.invitation_portal_url = self.invitation_portal_url.strip() or None
        if self.invitation_contact_name is not None:
            self.invitation_contact_name = self.invitation_contact_name.strip() or None
        if self.invitation_contact_email is not None:
            self.invitation_contact_email = self.invitation_contact_email.strip() or None
        if self.invitation_contact_phone is not None:
            self.invitation_contact_phone = self.invitation_contact_phone.strip() or None
        if self.invitation_contact_text is not None:
            self.invitation_contact_text = self.invitation_contact_text.strip() or None
        if self.ws_ticket_ttl_seconds < 30:
            self.ws_ticket_ttl_seconds = 30
        if self.ws_ticket_ttl_seconds > 60:
            self.ws_ticket_ttl_seconds = 60

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
    def resolved_iam_public_base_url(self) -> str:
        if self.iam_public_base_url:
            return self.iam_public_base_url
        if self.web_base_url:
            return f"{self.web_base_url.rstrip('/')}/iam"
        return "http://localhost:8080/iam"

    @property
    def resolved_iam_issuer(self) -> str:
        return self.iam_issuer or self.resolved_iam_public_base_url

    @property
    def iam_callback_url(self) -> str:
        base = (self.public_backend_base_url or self.web_base_url or "http://localhost:8080").rstrip("/")
        return f"{base}/api/v1/auth/callback"

settings = Settings()
