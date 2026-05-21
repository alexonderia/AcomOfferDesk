from __future__ import annotations

import json
import logging

import aio_pika

from app.core.config import settings
from app.services.process_notification_events import ProcessNotificationEventHandler
from shared.broker import EXCHANGE, QUEUE_NOTIFY_PROCESS, RK_NOTIFICATION_PROCESS

logger = logging.getLogger(__name__)


class ProcessNotificationConsumerRuntime:
    def __init__(self) -> None:
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._consume_tag: str | None = None
        self._queue: aio_pika.abc.AbstractQueue | None = None
        self._handler = ProcessNotificationEventHandler()

    async def start(self) -> None:
        self._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=20)
        exchange = await self._channel.declare_exchange(EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
        self._queue = await self._channel.declare_queue(QUEUE_NOTIFY_PROCESS, durable=True)
        await self._queue.bind(exchange, routing_key=RK_NOTIFICATION_PROCESS)

        async def _consume(message: aio_pika.abc.AbstractIncomingMessage) -> None:
            async with message.process(requeue=False):
                try:
                    payload = json.loads(message.body.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    logger.warning("Skip invalid process notification event payload")
                    return
                if not isinstance(payload, dict):
                    logger.warning("Skip non-object process notification event payload")
                    return
                try:
                    await self._handler.handle(payload=payload)
                except Exception:
                    logger.exception("Failed to handle process notification event")

        self._consume_tag = await self._queue.consume(_consume)
        logger.info("Process notification consumer started")

    async def stop(self) -> None:
        if self._queue is not None and self._consume_tag is not None:
            try:
                await self._queue.cancel(self._consume_tag)
            except Exception:
                logger.exception("Failed to cancel process notification consumer")
        if self._channel is not None:
            try:
                await self._channel.close()
            except Exception:
                logger.exception("Failed to close process notification channel")
        if self._connection is not None:
            try:
                await self._connection.close()
            except Exception:
                logger.exception("Failed to close process notification connection")
        self._consume_tag = None
        self._queue = None
        self._channel = None
        self._connection = None
