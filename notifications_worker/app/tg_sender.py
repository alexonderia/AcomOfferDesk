from __future__ import annotations

import asyncio
import json
import logging
import os
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)


async def send_tg(payload: dict) -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.warning("BOT_TOKEN is not configured. Skip telegram delivery")
        return

    chat_id = payload.get("chat_id")
    text = payload.get("text")
    if chat_id is None or not text:
        logger.warning("Telegram payload is missing chat_id or text")
        return

    data: dict[str, str | int] = {
        "chat_id": int(chat_id),
        "text": str(text),
    }

    button_text = payload.get("button_text")
    button_url = payload.get("button_url")
    if button_text and button_url:
        data["reply_markup"] = json.dumps(
            {"inline_keyboard": [[{"text": str(button_text), "url": str(button_url)}]]},
            ensure_ascii=False,
        )

    encoded = urllib.parse.urlencode(data).encode("utf-8")
    request = urllib.request.Request(
        url=f"https://api.telegram.org/bot{token}/sendMessage",
        data=encoded,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        await asyncio.to_thread(_send_request, request)
        logger.info("Telegram notification sent to chat_id=%s", chat_id)
    except Exception:
        logger.exception("Failed to send telegram notification to chat_id=%s", chat_id)


def _send_request(request: urllib.request.Request) -> None:
    with urllib.request.urlopen(request, timeout=10):
        return None
