from __future__ import annotations

import json
import logging
import os

from aio_pika.abc import AbstractIncomingMessage

from app.email_sender import send_email
from app.tg_sender import send_tg
from shared.broker import RK_EMAIL, RK_TG

logger = logging.getLogger(__name__)


def _is_telegram_legacy_enabled() -> bool:
    return os.getenv("LEGACY_TELEGRAM_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}


async def handle_message(message: AbstractIncomingMessage) -> None:
    async with message.process(requeue=False):
        payload = json.loads(message.body.decode("utf-8"))
        if message.routing_key == RK_EMAIL:
            await send_email(payload)
            return
        if message.routing_key == RK_TG:
            if not _is_telegram_legacy_enabled():
                logger.info("Skip legacy Telegram notification: feature is disabled")
                return
            await send_tg(payload)
