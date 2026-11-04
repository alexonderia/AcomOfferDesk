from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class FeedBackCreateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=3000)

    @field_validator("text")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Введите текст обратной связи")
        return value.strip()


class FeedBackCreateData(BaseModel):
    feedback_id: int


class FeedBackItemData(BaseModel):
    id: int
    text: str
    author_user_id: str | None = None
    author_name: str | None = None
    created_at: datetime | None = None


class FeedBackListData(BaseModel):
    items: list[FeedBackItemData]
    total: int = 0
    limit: int = 50
    offset: int = 0


class FeedBackCreateResponse(BaseModel):
    data: FeedBackCreateData


class FeedBackListResponse(BaseModel):
    data: FeedBackListData
