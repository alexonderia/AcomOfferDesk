from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable

import aio_pika


logger = logging.getLogger(__name__)


class RabbitMQRealtimePubSub:
    def __init__(self, *, url: str, exchange_name: str) -> None:
        self._url = url
        self._exchange_name = exchange_name
        self._handler: Callable[[dict], Awaitable[None]] | None = None
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None
        self._queue: aio_pika.abc.AbstractQueue | None = None
        self._connect_task: asyncio.Task[None] | None = None
        self._stopping = False

    async def start(self, *, handler: Callable[[dict], Awaitable[None]]) -> None:
        self._handler = handler
        self._stopping = False
        await self._ensure_connected()
        if self._exchange is None:
            logger.warning(
                "Realtime pubsub is unavailable on startup; continuing in local-only mode until RabbitMQ becomes reachable"
            )
            self._connect_task = asyncio.create_task(self._reconnect_loop())

    async def _ensure_connected(self) -> bool:
        if self._handler is None:
            raise RuntimeError("Realtime pubsub handler is not configured")
        if self._exchange is not None:
            return True

        try:
            self._connection = await aio_pika.connect_robust(self._url)
            self._channel = await self._connection.channel()
            self._exchange = await self._channel.declare_exchange(
                self._exchange_name,
                aio_pika.ExchangeType.FANOUT,
                durable=True,
            )
            self._queue = await self._channel.declare_queue(exclusive=True, auto_delete=True)
            await self._queue.bind(self._exchange)

            async def consume(message: aio_pika.abc.AbstractIncomingMessage) -> None:
                async with message.process():
                    try:
                        payload = json.loads(message.body.decode("utf-8"))
                    except json.JSONDecodeError:
                        logger.warning("Skipping malformed realtime payload")
                        return
                    await self._handler(payload)

            await self._queue.consume(consume)
            logger.info("Realtime pubsub connected to RabbitMQ")
            return True
        except Exception as exc:
            await self._reset_connection()
            if self._connect_task is None:
                logger.exception("Failed to connect realtime pubsub to RabbitMQ")
            else:
                logger.warning("Realtime pubsub reconnect failed: %s", exc)
            return False

    async def _reconnect_loop(self) -> None:
        try:
            while not self._stopping and self._exchange is None:
                await asyncio.sleep(5)
                connected = await self._ensure_connected()
                if connected:
                    return
        except asyncio.CancelledError:
            raise

    async def publish(self, payload: dict) -> None:
        if self._exchange is None:
            logger.warning("Skipping remote realtime publish because RabbitMQ pubsub is unavailable")
            return

        message = aio_pika.Message(
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.NOT_PERSISTENT,
        )
        await self._exchange.publish(message, routing_key="")

    async def close(self) -> None:
        self._stopping = True
        if self._connect_task is not None:
            self._connect_task.cancel()
            try:
                await self._connect_task
            except asyncio.CancelledError:
                pass
        self._connect_task = None
        await self._reset_connection()

    async def _reset_connection(self) -> None:
        if self._channel is not None and not self._channel.is_closed:
            await self._channel.close()
        self._channel = None
        self._exchange = None
        self._queue = None
        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()
        self._connection = None
