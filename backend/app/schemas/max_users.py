from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MaxStartRequest(BaseModel):
    max_user_id: str
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class MaxOpenRequestItem(BaseModel):
    id: str
    description: str | None = None
    deadline_at: datetime | None = None
    url: str | None = None


class MaxStartResponse(BaseModel):
    action: Literal["register", "pending", "open_requests", "blocked"]
    registration_url: str | None = None
    existing_account_link_token: str | None = None
    requests: list[MaxOpenRequestItem] = Field(default_factory=list)


class MaxLinkRequest(BaseModel):
    max_user_id: str


class MaxLinkData(BaseModel):
    url: str


class MaxLinkResponse(BaseModel):
    data: MaxLinkData
