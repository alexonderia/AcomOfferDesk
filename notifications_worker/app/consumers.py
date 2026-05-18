from __future__ import annotations

import json
import logging
import os

from aio_pika.abc import AbstractIncomingMessage

from .email_sender import send_email
from .tg_sender import send_tg
from shared.broker import RK_EMAIL, RK_TG

logger = logging.getLogger(__name__)


def _is_telegram_legacy_enabled() -> bool:
    return os.getenv("LEGACY_TELEGRAM_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}


async def handle_message(message: AbstractIncomingMessage) -> None:
    async with message.process(requeue=False):
        try:
            payload = json.loads(message.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            logger.warning("Skip notification payload: invalid JSON")
            return

        if not isinstance(payload, dict):
            logger.warning("Skip notification payload: expected JSON object")
            return

        try:
            if message.routing_key == RK_EMAIL:
                await send_email(payload)
                return
            if message.routing_key == RK_TG:
                if not _is_telegram_legacy_enabled():
                    logger.info("Skip legacy Telegram notification: feature is disabled")
                    return
                await send_tg(payload)
                return
            logger.info("Skip notification payload: unsupported routing key %s", message.routing_key)
        except Exception:
            logger.exception("Failed to process notification payload for routing key %s", message.routing_key)
