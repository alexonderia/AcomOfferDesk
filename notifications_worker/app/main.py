from __future__ import annotations

import asyncio
import logging
import os

import aio_pika
from aio_pika.abc import AbstractRobustConnection
from aiormq.exceptions import AMQPConnectionError

from app.consumers import handle_message
from shared.broker import EXCHANGE, QUEUE_EMAIL, QUEUE_TG, RK_EMAIL, RK_TG

logger = logging.getLogger(__name__)


def _is_telegram_legacy_enabled() -> bool:
    return os.getenv("LEGACY_TELEGRAM_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}


async def _connect_with_retry(rabbitmq_url: str) -> AbstractRobustConnection:
    delay_seconds = 2
    max_delay_seconds = 15

    while True:
        try:
            connection = await aio_pika.connect_robust(rabbitmq_url)
            logger.info("Connected to RabbitMQ")
            return connection
        except AMQPConnectionError:
            logger.warning(
                "RabbitMQ is not ready yet. Retrying in %s seconds...",
                delay_seconds,
            )
            await asyncio.sleep(delay_seconds)
            delay_seconds = min(delay_seconds + 1, max_delay_seconds)


async def run_worker() -> None:
    logging.basicConfig(level=logging.INFO)
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    telegram_legacy_enabled = _is_telegram_legacy_enabled()
    connection = await _connect_with_retry(rabbitmq_url)

    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    exchange = await channel.declare_exchange(EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)

    email_queue = await channel.declare_queue(QUEUE_EMAIL, durable=True)
    await email_queue.bind(exchange, routing_key=RK_EMAIL)
    await email_queue.consume(handle_message)
    if telegram_legacy_enabled:
        # LEGACY: Telegram queue is disabled by default in production.
        tg_queue = await channel.declare_queue(QUEUE_TG, durable=True)
        await tg_queue.bind(exchange, routing_key=RK_TG)
        await tg_queue.consume(handle_message)
        logger.info("Notifications worker is consuming email and legacy Telegram queues")
    else:
        logger.info("Notifications worker is consuming email queue only (legacy Telegram disabled)")

    try:
        await asyncio.Future()
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(run_worker())
