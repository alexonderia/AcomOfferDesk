from __future__ import annotations

from pydantic import BaseModel, Field


class FeedBackCreateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=3000)


class FeedBackCreateData(BaseModel):
    feedback_id: int


class FeedBackItemData(BaseModel):
    id: int
    text: str


class FeedBackListData(BaseModel):
    items: list[FeedBackItemData]


class FeedBackCreateResponse(BaseModel):
    data: FeedBackCreateData


class FeedBackListResponse(BaseModel):
    data: FeedBackListData
