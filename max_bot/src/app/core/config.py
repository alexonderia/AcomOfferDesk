from __future__ import annotations

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    max_bot_enabled: bool = Field(default=False, validation_alias="MAX_BOT_ENABLED")
    max_bot_token: str | None = Field(default=None, validation_alias="MAX_BOT_TOKEN")
    backend_base_url: str = Field(validation_alias="BACKEND_BASE_URL")
    public_backend_base_url: str | None = Field(default=None, validation_alias="PUBLIC_BACKEND_BASE_URL")
    max_bot_timeout_seconds: float = Field(default=10.0, validation_alias="MAX_BOT_TIMEOUT_SECONDS")
    max_polling_enabled: bool = Field(default=True, validation_alias="MAX_POLLING_ENABLED")
    bot_api_shared_secret: str | None = Field(default=None, validation_alias="BOT_API_SHARED_SECRET")

    @model_validator(mode="after")
    def _validate_required(self) -> "Settings":
        if self.max_bot_enabled and not (self.max_bot_token or "").strip():
            raise ValueError("MAX_BOT_TOKEN must not be empty")
        if not (self.backend_base_url or "").strip():
            raise ValueError("BACKEND_BASE_URL must not be empty")
        if self.max_bot_timeout_seconds <= 0:
            self.max_bot_timeout_seconds = 10.0
        return self


settings = Settings()
