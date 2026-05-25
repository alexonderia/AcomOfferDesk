from __future__ import annotations

import logging
from typing import Any

from fastapi import WebSocket

from app.core.config import settings
from app.realtime.contracts import OutboundEnvelope
from app.realtime.manager import WebSocketConnectionManager
from app.realtime.pubsub import RabbitMQRealtimePubSub
from app.services.chat_realtime import ChatRealtimeService


logger = logging.getLogger(__name__)

_runtime: "ChatRealtimeRuntime | None" = None
_realtime_runtime: "UnifiedRealtimeRuntime | None" = None

_CHAT_EVENT_TYPE_NORMALIZATION: dict[str, str] = {
    "message.created": "chat.message.created",
    "message.delivered": "chat.message.delivered",
    "message.read": "chat.message.read",
    "typing.start": "chat.typing.started",
    "typing.stop": "chat.typing.stopped",
}


class ChatRealtimeRuntime:
    def __init__(self) -> None:
        self.manager = WebSocketConnectionManager()
        self.service = ChatRealtimeService()
        self.pubsub = RabbitMQRealtimePubSub(
            url=settings.rabbitmq_url,
            exchange_name="chat.realtime",
        )

    async def start(self) -> None:
        await self.pubsub.start(handler=self._handle_pubsub_payload)

    async def stop(self) -> None:
        await self.pubsub.close()

    async def send_to_connection(self, *, connection_id: str, event: OutboundEnvelope) -> None:
        await self.manager.send_to_connection(connection_id=connection_id, event=event)

    async def publish_chat_event(
        self,
        *,
        chat_id: int,
        event: OutboundEnvelope,
        exclude_user_ids: set[str] | None = None,
        publish_remote: bool = True,
    ) -> None:
        canonical_event = _normalize_chat_event(event)
        delivered_user_ids = await self._broadcast_to_chat(
            chat_id=chat_id,
            event=canonical_event,
            exclude_user_ids=exclude_user_ids,
        )
        await self._process_local_side_effects(
            chat_id=chat_id,
            event=canonical_event,
            delivered_user_ids=delivered_user_ids,
        )
        if publish_remote:
            await self.pubsub.publish(
                {
                    "chat_id": chat_id,
                    "exclude_user_ids": sorted(exclude_user_ids or []),
                    "event": canonical_event.model_dump(mode="json"),
                }
            )

    async def _handle_pubsub_payload(self, payload: dict[str, Any]) -> None:
        chat_id = int(payload["chat_id"])
        event_payload = payload["event"]
        exclude_user_ids = set(payload.get("exclude_user_ids") or [])
        event = _normalize_chat_event(OutboundEnvelope.model_validate(event_payload))
        delivered_user_ids = await self._broadcast_to_chat(
            chat_id=chat_id,
            event=event,
            exclude_user_ids=exclude_user_ids,
        )
        await self._process_local_side_effects(chat_id=chat_id, event=event, delivered_user_ids=delivered_user_ids)

    async def _broadcast_to_chat(
        self,
        *,
        chat_id: int,
        event: OutboundEnvelope,
        exclude_user_ids: set[str] | None = None,
    ) -> set[str]:
        delivered_user_ids = await self.manager.broadcast_to_chat(
            chat_id=chat_id,
            event=event,
            exclude_user_ids=exclude_user_ids,
        )
        return delivered_user_ids

    async def _process_local_side_effects(
        self,
        *,
        chat_id: int,
        event: OutboundEnvelope,
        delivered_user_ids: set[str],
    ) -> None:
        if event.type != "chat.message.created":
            return

        message_payload = event.data.get("message")
        if not isinstance(message_payload, dict):
            return
        sender_user_id = str(message_payload.get("user_id") or "")
        message_id = int(message_payload.get("id") or 0)
        if message_id <= 0:
            return

        recipient_user_ids = {user_id for user_id in delivered_user_ids if user_id != sender_user_id}
        for user_id in recipient_user_ids:
            ack = await self.service.mark_delivered_for_online_user(
                offer_id=chat_id,
                user_id=user_id,
                message_ids=[message_id],
            )
            if not ack.updated_message_ids:
                continue
            delivered_event = OutboundEnvelope(
                type="chat.message.delivered",
                data={
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "message_ids": ack.updated_message_ids,
                },
            )
            await self.publish_chat_event(chat_id=chat_id, event=delivered_event, publish_remote=True)


def _normalize_chat_event(event: OutboundEnvelope) -> OutboundEnvelope:
    canonical_type = _CHAT_EVENT_TYPE_NORMALIZATION.get(event.type, event.type)
    if canonical_type == event.type:
        return event
    return OutboundEnvelope(
        type=canonical_type,
        event_id=event.event_id,
        ts=event.ts,
        request_id=event.request_id,
        data=event.data,
    )


class UnifiedRealtimeRuntime:
    def __init__(self, *, manager: WebSocketConnectionManager | None = None) -> None:
        self.manager = manager or WebSocketConnectionManager()

    async def connect(self, *, websocket: WebSocket, user_id: str) -> str:
        return await self.manager.connect(websocket=websocket, user_id=user_id)

    async def disconnect(self, *, connection_id: str) -> None:
        await self.manager.disconnect(connection_id=connection_id)

    async def send_to_user(self, *, user_id: str, event: OutboundEnvelope) -> bool:
        return await self.manager.send_to_user(user_id=user_id, event=event)

    async def broadcast_to_users(self, *, user_ids: set[str], event: OutboundEnvelope) -> set[str]:
        return await self.manager.broadcast_to_users(user_ids=user_ids, event=event)


def set_chat_runtime(runtime: ChatRealtimeRuntime) -> None:
    global _runtime
    _runtime = runtime


def get_chat_runtime() -> ChatRealtimeRuntime:
    global _runtime
    if _runtime is None:
        # Fallback for test scenarios where app lifespan startup is bypassed.
        _runtime = ChatRealtimeRuntime()
    return _runtime


def set_unified_realtime_runtime(runtime: UnifiedRealtimeRuntime) -> None:
    global _realtime_runtime
    _realtime_runtime = runtime


def get_unified_realtime_runtime() -> UnifiedRealtimeRuntime:
    global _realtime_runtime
    if _realtime_runtime is None:
        # Fallback for test scenarios where app lifespan startup is bypassed.
        if _runtime is not None:
            _realtime_runtime = UnifiedRealtimeRuntime(manager=_runtime.manager)
        else:
            _realtime_runtime = UnifiedRealtimeRuntime()
    return _realtime_runtime
