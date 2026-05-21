from __future__ import annotations

import asyncio
import json
import logging

import aio_pika

from app.core.config import settings
from app.services.email_delivery_events import EmailDeliveryEventHandler
from shared.broker import EXCHANGE, QUEUE_EMAIL_DELIVERY, RK_EMAIL_DELIVERY_FAILED, RK_EMAIL_DELIVERY_SUCCEEDED

logger = logging.getLogger(__name__)


class EmailDeliveryConsumerRuntime:
    def __init__(self) -> None:
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._consume_tag: str | None = None
        self._queue: aio_pika.abc.AbstractQueue | None = None
        self._handler = EmailDeliveryEventHandler()

    async def start(self) -> None:
        self._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=20)
        exchange = await self._channel.declare_exchange(EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
        self._queue = await self._channel.declare_queue(QUEUE_EMAIL_DELIVERY, durable=True)
        await self._queue.bind(exchange, routing_key=RK_EMAIL_DELIVERY_SUCCEEDED)
        await self._queue.bind(exchange, routing_key=RK_EMAIL_DELIVERY_FAILED)

        async def _consume(message: aio_pika.abc.AbstractIncomingMessage) -> None:
            async with message.process(requeue=False):
                try:
                    payload = json.loads(message.body.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    logger.warning("Skip invalid email delivery event payload")
                    return
                if not isinstance(payload, dict):
                    logger.warning("Skip non-object email delivery event payload")
                    return
                try:
                    await self._handler.handle(routing_key=message.routing_key, payload=payload)
                except Exception:
                    logger.exception("Failed to handle email delivery event")

        self._consume_tag = await self._queue.consume(_consume)
        logger.info("Email delivery consumer started")

    async def stop(self) -> None:
        if self._queue is not None and self._consume_tag is not None:
            try:
                await self._queue.cancel(self._consume_tag)
            except Exception:
                logger.exception("Failed to cancel email delivery consumer")
        if self._channel is not None:
            try:
                await self._channel.close()
            except Exception:
                logger.exception("Failed to close email delivery channel")
        if self._connection is not None:
            try:
                await self._connection.close()
            except Exception:
                logger.exception("Failed to close email delivery connection")
        self._consume_tag = None
        self._queue = None
        self._channel = None
        self._connection = None

