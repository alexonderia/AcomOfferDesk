from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings
from app.realtime.contracts import OutboundEnvelope
from app.realtime.manager import WebSocketConnectionManager
from app.realtime.pubsub import RabbitMQRealtimePubSub
from app.services.chat_realtime import ChatRealtimeService


logger = logging.getLogger(__name__)

_runtime: "ChatRealtimeRuntime | None" = None


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
        delivered_user_ids = await self.manager.broadcast_to_chat(
            chat_id=chat_id,
            event=event,
            exclude_user_ids=exclude_user_ids,
        )
        await self._process_local_side_effects(chat_id=chat_id, event=event, delivered_user_ids=delivered_user_ids)
        if publish_remote:
            await self.pubsub.publish(
                {
                    "chat_id": chat_id,
                    "exclude_user_ids": sorted(exclude_user_ids or []),
                    "event": event.model_dump(mode="json"),
                }
            )

    async def _handle_pubsub_payload(self, payload: dict[str, Any]) -> None:
        chat_id = int(payload["chat_id"])
        event_payload = payload["event"]
        exclude_user_ids = set(payload.get("exclude_user_ids") or [])
        event = OutboundEnvelope.model_validate(event_payload)
        delivered_user_ids = await self.manager.broadcast_to_chat(
            chat_id=chat_id,
            event=event,
            exclude_user_ids=exclude_user_ids,
        )
        await self._process_local_side_effects(chat_id=chat_id, event=event, delivered_user_ids=delivered_user_ids)

    async def _process_local_side_effects(
        self,
        *,
        chat_id: int,
        event: OutboundEnvelope,
        delivered_user_ids: set[str],
    ) -> None:
        if event.type != "message.created":
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
                type="message.delivered",
                data={
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "message_ids": ack.updated_message_ids,
                },
            )
            await self.publish_chat_event(chat_id=chat_id, event=delivered_event, publish_remote=True)


def set_chat_runtime(runtime: ChatRealtimeRuntime) -> None:
    global _runtime
    _runtime = runtime


def get_chat_runtime() -> ChatRealtimeRuntime:
    if _runtime is None:
        raise RuntimeError("Chat realtime runtime is not initialized")
    return _runtime
