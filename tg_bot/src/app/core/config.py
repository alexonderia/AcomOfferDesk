from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str
    backend_base_url: str
    public_backend_base_url: str | None = None
    request_timeout_seconds: float = 5.0
    bot_api_shared_secret: str | None = None


settings = Settings()