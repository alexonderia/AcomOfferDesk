from datetime import datetime

from pydantic import BaseModel, Field


class TgUserStartRequest(BaseModel):
    tg_id: int


class TgUserStartData(BaseModel):
    tg_id: int
    status: str


class TgUserStartResponse(BaseModel):
    data: TgUserStartData

class TgStartRequest(BaseModel):
    tg_id: int


class TgOpenRequestItem(BaseModel):
    request_id: str
    description: str | None
    deadline_at: datetime
    link: str


class TgStartData(BaseModel):
    tg_id: int
    tg_status: str
    action: str
    registration_link: str | None = None
    requests: list[TgOpenRequestItem] = Field(default_factory=list)
    user_status: str | None = None


class TgStartResponse(BaseModel):
    data: TgStartData
