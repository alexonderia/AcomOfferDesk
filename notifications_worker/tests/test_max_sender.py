from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("MAX_BOT_TOKEN", "test-token")

from app.max_sender import send_max


@pytest.mark.asyncio
async def test_send_max_skips_without_token(monkeypatch):
    monkeypatch.delenv("MAX_BOT_TOKEN", raising=False)

    with patch("app.max_sender.urllib.request.urlopen") as urlopen:
        await send_max({"user_id": "123", "text": "hello"})
        urlopen.assert_not_called()


@pytest.mark.asyncio
async def test_send_max_posts_message_with_inline_button(monkeypatch):
    monkeypatch.setenv("MAX_BOT_TOKEN", "secret-token")

    captured: dict = {}

    def _fake_urlopen(request, timeout=15):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return MagicMock()

    with patch("app.max_sender.urllib.request.urlopen", side_effect=_fake_urlopen):
        await send_max(
            {
                "user_id": "482403059838",
                "text": "Новая заявка",
                "button_text": "Открыть",
                "button_url": "https://example.com/login",
            }
        )

    assert "user_id=482403059838" in captured["url"]
    assert captured["url"].startswith("https://platform-api.max.ru/messages")
    assert captured["headers"]["Authorization"] == "secret-token"
    assert captured["body"]["text"] == "Новая заявка"
    assert captured["body"]["attachments"][0]["type"] == "inline_keyboard"
