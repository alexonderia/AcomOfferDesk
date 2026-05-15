from __future__ import annotations

import json
import logging
import os

import aio_pika

from shared.broker import EXCHANGE
from shared.email_delivery import EmailDeliveryResultEvent

logger = logging.getLogger(__name__)


async def publish_email_delivery_result(event: EmailDeliveryResultEvent) -> None:
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    connection = await aio_pika.connect_robust(rabbitmq_url)
    try:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
        payload = {
            "event_type": event.event_type,
            "correlation_id": event.correlation_id,
            "recipient_user_id": event.recipient_user_id,
            "request_id": event.request_id,
            "offer_id": event.offer_id,
            "to_email": event.to_email,
            "safe_error_code": event.safe_error_code,
            "safe_error_message": event.safe_error_message,
            "occurred_at": event.occurred_at,
        }
        message = aio_pika.Message(
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await exchange.publish(message, routing_key=event.event_type)
    except Exception:
        logger.exception("Failed to publish email delivery result event")
    finally:
        await connection.close()

