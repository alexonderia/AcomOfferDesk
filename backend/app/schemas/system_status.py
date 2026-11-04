from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ServiceStatusSchema(BaseModel):
    key: str
    name: str
    status: Literal["up", "down", "degraded", "disabled"]
    response_ms: float | None
    detail: str


class RuntimeSettingsSchema(BaseModel):
    environment: str
    email_enabled: bool
    smtp_configured: bool
    imap_configured: bool
    file_guard_enabled: bool
    secure_cookies: bool
    cookie_samesite: str
    signed_file_link_ttl_seconds: int
    websocket_ticket_ttl_seconds: int


class SystemStatusData(BaseModel):
    checked_at: datetime
    overall: Literal["healthy", "degraded"]
    uptime_seconds: int
    cache_ttl_seconds: int
    probe_timeout_seconds: float
    settings: RuntimeSettingsSchema
    services: list[ServiceStatusSchema]


class SystemStatusResponse(BaseModel):
    data: SystemStatusData
