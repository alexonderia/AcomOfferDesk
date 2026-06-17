from __future__ import annotations

import json
import logging

import aio_pika

from app.core.config import settings
from app.services.contractor_outbound_notifications import send_unread_chat_email_if_needed
from shared.broker import EXCHANGE, QUEUE_NOTIFICATION_DELAYED, RK_NOTIFICATION_DELAYED, RK_NOTIFICATION_DELAYED_READY
from shared.normalization import as_optional_int as _as_optional_int
from shared.normalization import normalize_optional_str as _normalize_optional_str

logger = logging.getLogger(__name__)

_DELAYED_QUEUE_ARGUMENTS = {
    "x-dead-letter-exchange": EXCHANGE,
    "x-dead-letter-routing-key": RK_NOTIFICATION_DELAYED_READY,
}


class DelayedNotificationConsumerRuntime:
    def __init__(self) -> None:
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._consume_tag: str | None = None
        self._queue: aio_pika.abc.AbstractQueue | None = None

    async def start(self) -> None:
        self._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=20)
        exchange = await self._channel.declare_exchange(EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
        delayed_queue = await self._channel.declare_queue(
            QUEUE_NOTIFICATION_DELAYED,
            durable=True,
            arguments=_DELAYED_QUEUE_ARGUMENTS,
        )
        await delayed_queue.bind(exchange, routing_key=RK_NOTIFICATION_DELAYED)
        self._queue = await self._channel.declare_queue(
            f"{RK_NOTIFICATION_DELAYED_READY}.backend",
            durable=True,
        )
        await self._queue.bind(exchange, routing_key=RK_NOTIFICATION_DELAYED_READY)

        async def _consume(message: aio_pika.abc.AbstractIncomingMessage) -> None:
            async with message.process(requeue=False):
                try:
                    payload = json.loads(message.body.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    logger.warning("Skip invalid delayed notification payload")
                    return
                if not isinstance(payload, dict):
                    logger.warning("Skip non-object delayed notification payload")
                    return
                try:
                    await self._handle(payload=payload)
                except Exception:
                    logger.exception("Failed to handle delayed notification payload")

        self._consume_tag = await self._queue.consume(_consume)
        logger.info("Delayed notification consumer started")

    async def stop(self) -> None:
        if self._queue is not None and self._consume_tag is not None:
            try:
                await self._queue.cancel(self._consume_tag)
            except Exception:
                logger.exception("Failed to cancel delayed notification consumer")
        if self._channel is not None:
            try:
                await self._channel.close()
            except Exception:
                logger.exception("Failed to close delayed notification channel")
        if self._connection is not None:
            try:
                await self._connection.close()
            except Exception:
                logger.exception("Failed to close delayed notification connection")
        self._consume_tag = None
        self._queue = None
        self._channel = None
        self._connection = None

    async def _handle(self, *, payload: dict) -> None:
        kind = _normalize_optional_str(payload.get("kind"))
        if kind == "chat.unread_email":
            message_id = _as_optional_int(payload.get("message_id"))
            recipient_user_id = _normalize_optional_str(payload.get("recipient_user_id"))
            request_id = _normalize_optional_str(payload.get("request_id"))
            offer_id = _as_optional_int(payload.get("offer_id"))
            if message_id is None or recipient_user_id is None or request_id is None or offer_id is None:
                logger.warning("Skip chat.unread_email delayed payload with missing fields")
                return
            await send_unread_chat_email_if_needed(
                message_id=message_id,
                recipient_user_id=recipient_user_id,
                request_id=request_id,
                offer_id=offer_id,
            )
            return
        logger.warning("Skip delayed notification payload with unsupported kind: %s", kind)
