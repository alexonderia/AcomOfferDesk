from __future__ import annotations

import asyncio
import json
import logging

import aio_pika

from app.core.config import settings
from shared.broker import EXCHANGE, RK_NOTIFICATION_PROCESS
from shared.process_notifications import ProcessNotificationEvent

logger = logging.getLogger(__name__)

_PROCESS_PUBLISH_BACKOFFS_SECONDS = (0.1, 0.3, 1.0)


async def publish_notification(event_type: str, payload: dict) -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    try:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
        message = aio_pika.Message(
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await exchange.publish(message, routing_key=event_type)
    finally:
        await connection.close()


async def publish_process_notification_event(event: ProcessNotificationEvent) -> bool:
    payload = event.to_payload()
    for attempt_index, backoff_seconds in enumerate((0.0, *_PROCESS_PUBLISH_BACKOFFS_SECONDS), start=1):
        if backoff_seconds > 0:
            await asyncio.sleep(backoff_seconds)
        try:
            await publish_notification(RK_NOTIFICATION_PROCESS, payload)
            return True
        except Exception:
            if attempt_index < len(_PROCESS_PUBLISH_BACKOFFS_SECONDS) + 1:
                logger.warning(
                    "Failed to publish process notification event, retrying: attempt=%s event_id=%s event_type=%s entity_id=%s",
                    attempt_index,
                    event.event_id,
                    event.event_type,
                    event.entity_id,
                )
                continue
            logger.exception(
                "Failed to publish process notification event after retries: event_id=%s event_type=%s entity_id=%s",
                event.event_id,
                event.event_type,
                event.entity_id,
            )
            return False
