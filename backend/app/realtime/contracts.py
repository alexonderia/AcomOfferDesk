from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, TypeAdapter, model_validator


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OutboundEnvelope(BaseModel):
    type: str
    event_id: str = Field(default_factory=lambda: uuid4().hex)
    ts: datetime = Field(default_factory=utcnow)
    request_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class ChatFileRefPayload(BaseModel):
    file_id: int = Field(..., ge=1)
    upload_token: str = Field(..., min_length=10)


class ChatSubscribePayload(BaseModel):
    chat_id: int = Field(..., ge=1)


class ChatUnsubscribePayload(BaseModel):
    chat_id: int = Field(..., ge=1)


class MessageSendPayload(BaseModel):
    chat_id: int = Field(..., ge=1)
    text: str = ""
    reply_to_id: int | None = Field(default=None, ge=1)
    files: list[ChatFileRefPayload] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_content(self) -> "MessageSendPayload":
        if not self.text.strip() and not self.files:
            raise ValueError("Message text cannot be empty")
        return self


class MessageReadPayload(BaseModel):
    chat_id: int = Field(..., ge=1)
    message_ids: list[int] | None = None
    up_to_message_id: int | None = Field(default=None, ge=1)


class ChatSyncPayload(BaseModel):
    chat_id: int = Field(..., ge=1)
    last_known_message_id: int | None = Field(default=None, ge=1)


class TypingPayload(BaseModel):
    chat_id: int = Field(..., ge=1)


class ChatSubscribeEvent(BaseModel):
    type: Literal["chat.subscribe"]
    request_id: str | None = None
    data: ChatSubscribePayload


class ChatUnsubscribeEvent(BaseModel):
    type: Literal["chat.unsubscribe"]
    request_id: str | None = None
    data: ChatUnsubscribePayload


class MessageSendEvent(BaseModel):
    type: Literal["message.send"]
    request_id: str | None = None
    data: MessageSendPayload


class MessageReadEvent(BaseModel):
    type: Literal["message.read"]
    request_id: str | None = None
    data: MessageReadPayload


class TypingStartEvent(BaseModel):
    type: Literal["typing.start"]
    request_id: str | None = None
    data: TypingPayload


class TypingStopEvent(BaseModel):
    type: Literal["typing.stop"]
    request_id: str | None = None
    data: TypingPayload


class ChatSyncEvent(BaseModel):
    type: Literal["chat.sync"]
    request_id: str | None = None
    data: ChatSyncPayload


ClientEvent = Annotated[
    ChatSubscribeEvent
    | ChatUnsubscribeEvent
    | MessageSendEvent
    | MessageReadEvent
    | TypingStartEvent
    | TypingStopEvent
    | ChatSyncEvent,
    Field(discriminator="type"),
]

client_event_adapter = TypeAdapter(ClientEvent)
