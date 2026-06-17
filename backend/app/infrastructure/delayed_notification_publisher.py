from __future__ import annotations

import json
import logging

import aio_pika

from app.core.config import settings
from shared.broker import EXCHANGE, QUEUE_NOTIFICATION_DELAYED, RK_NOTIFICATION_DELAYED, RK_NOTIFICATION_DELAYED_READY

logger = logging.getLogger(__name__)

_DELAYED_QUEUE_ARGUMENTS = {
    "x-dead-letter-exchange": EXCHANGE,
    "x-dead-letter-routing-key": RK_NOTIFICATION_DELAYED_READY,
}


async def _ensure_delayed_queue(channel: aio_pika.abc.AbstractChannel) -> aio_pika.abc.AbstractExchange:
    exchange = await channel.declare_exchange(EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
    delayed_queue = await channel.declare_queue(
        QUEUE_NOTIFICATION_DELAYED,
        durable=True,
        arguments=_DELAYED_QUEUE_ARGUMENTS,
    )
    await delayed_queue.bind(exchange, routing_key=RK_NOTIFICATION_DELAYED)
    return exchange


async def publish_delayed_notification(*, payload: dict, delay_seconds: int) -> None:
    normalized_delay = max(1, int(delay_seconds))
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    try:
        channel = await connection.channel()
        exchange = await _ensure_delayed_queue(channel)
        message = aio_pika.Message(
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            expiration=str(normalized_delay * 1000),
        )
        await exchange.publish(message, routing_key=RK_NOTIFICATION_DELAYED)
    finally:
        await connection.close()


async def schedule_unread_chat_email_notification(
    *,
    message_id: int,
    recipient_user_id: str,
    request_id: str,
    offer_id: int,
    delay_seconds: int,
) -> None:
    await publish_delayed_notification(
        payload={
            "kind": "chat.unread_email",
            "message_id": message_id,
            "recipient_user_id": recipient_user_id,
            "request_id": request_id,
            "offer_id": offer_id,
        },
        delay_seconds=delay_seconds,
    )
