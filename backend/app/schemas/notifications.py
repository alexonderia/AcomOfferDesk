from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class NotificationItemSchema(BaseModel):
    id: int
    user_id: str
    type: str
    severity: str
    title: str
    body: str
    entity_type: str | None
    entity_id: int | None
    link_url: str | None
    payload: dict = Field(default_factory=dict)
    read_at: datetime | None
    created_at: datetime


class NotificationListData(BaseModel):
    items: list[NotificationItemSchema]
    limit: int
    offset: int


class NotificationListResponse(BaseModel):
    data: NotificationListData


class NotificationUnreadCountData(BaseModel):
    count: int


class NotificationUnreadCountResponse(BaseModel):
    data: NotificationUnreadCountData


class NotificationMarkReadResponseData(BaseModel):
    notification_id: int
    read_at: datetime


class NotificationMarkReadResponse(BaseModel):
    data: NotificationMarkReadResponseData


class NotificationMarkAllReadResponseData(BaseModel):
    updated_count: int


class NotificationMarkAllReadResponse(BaseModel):
    data: NotificationMarkAllReadResponseData

