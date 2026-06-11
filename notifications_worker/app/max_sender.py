from __future__ import annotations

import asyncio
import json
import logging
import os
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

_DEFAULT_MAX_API_BASE_URL = "https://platform-api.max.ru"


async def send_max(payload: dict) -> None:
    token = (os.getenv("MAX_BOT_TOKEN") or "").strip()
    if not token:
        logger.warning("MAX_BOT_TOKEN is not configured. Skip MAX delivery")
        return

    user_id = payload.get("user_id")
    text = payload.get("text")
    if user_id is None or not text:
        logger.warning("MAX payload is missing user_id or text")
        return

    body: dict = {"text": str(text)}

    button_text = payload.get("button_text")
    button_url = payload.get("button_url")
    if button_text and button_url:
        body["attachments"] = [
            {
                "type": "inline_keyboard",
                "payload": {
                    "buttons": [
                        [
                            {
                                "type": "link",
                                "text": str(button_text),
                                "url": str(button_url),
                            }
                        ]
                    ]
                },
            }
        ]

    api_base_url = (os.getenv("MAX_API_BASE_URL") or _DEFAULT_MAX_API_BASE_URL).rstrip("/")
    query = urllib.parse.urlencode({"user_id": str(user_id)})
    request = urllib.request.Request(
        url=f"{api_base_url}/messages?{query}",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": token,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        await asyncio.to_thread(_send_request, request)
        logger.info("MAX notification sent to user_id=%s", user_id)
    except Exception:
        logger.exception("Failed to send MAX notification to user_id=%s", user_id)


def _send_request(request: urllib.request.Request) -> None:
    with urllib.request.urlopen(request, timeout=15):
        return None
