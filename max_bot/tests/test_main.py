from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

os.environ.setdefault("MAX_BOT_TOKEN", "test-token")
os.environ.setdefault("BACKEND_BASE_URL", "http://backend:8000")

from app.main import run_bot
from app.services.bot_commands import MAX_BOT_COMMANDS, register_bot_commands


def _mock_http_client(*, patch_method: AsyncMock) -> MagicMock:
    client = MagicMock()
    client.patch = patch_method
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


@pytest.mark.asyncio
async def test_register_bot_commands_patches_me() -> None:
    response = SimpleNamespace(raise_for_status=Mock())
    client = _mock_http_client(patch_method=AsyncMock(return_value=response))

    with patch("app.services.bot_commands.httpx.AsyncClient", return_value=client):
        await register_bot_commands(token="secret-token")

    client.patch.assert_awaited_once()
    call_kwargs = client.patch.await_args.kwargs
    assert call_kwargs["headers"]["Authorization"] == "secret-token"
    assert call_kwargs["json"]["commands"] == list(MAX_BOT_COMMANDS)


@pytest.mark.asyncio
async def test_register_bot_commands_swallows_api_errors() -> None:
    client = _mock_http_client(patch_method=AsyncMock(side_effect=RuntimeError("api down")))

    with patch("app.services.bot_commands.httpx.AsyncClient", return_value=client):
        await register_bot_commands(token="secret-token")


@pytest.mark.asyncio
async def test_run_bot_registers_commands_before_polling(monkeypatch) -> None:
    monkeypatch.setattr("app.main.settings.max_polling_enabled", True)

    bot = SimpleNamespace(delete_webhook=AsyncMock(), close=AsyncMock())
    dispatcher = SimpleNamespace(start_polling=AsyncMock(return_value=None))
    register_commands = AsyncMock()
    bot_factory = Mock(return_value=bot)
    dispatcher_factory = Mock(return_value=dispatcher)

    await run_bot(
        bot_factory=bot_factory,
        dispatcher_factory=dispatcher_factory,
        register_commands=register_commands,
        sleep=AsyncMock(),
        retry_delay_seconds=0,
    )

    register_commands.assert_awaited_once()
    dispatcher.start_polling.assert_awaited_once_with(bot)
