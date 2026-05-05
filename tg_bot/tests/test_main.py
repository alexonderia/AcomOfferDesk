from __future__ import annotations

import os
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock

from aiogram.exceptions import TelegramNetworkError

os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("BACKEND_BASE_URL", "http://backend:8000")

from app.main import run_bot


class RunBotTests(IsolatedAsyncioTestCase):
    async def test_retries_polling_after_telegram_network_error(self) -> None:
        first_bot = SimpleNamespace(
            set_my_commands=AsyncMock(),
            session=SimpleNamespace(close=AsyncMock()),
        )
        second_bot = SimpleNamespace(
            set_my_commands=AsyncMock(),
            session=SimpleNamespace(close=AsyncMock()),
        )
        bot_factory = Mock(side_effect=[first_bot, second_bot])

        first_dispatcher = SimpleNamespace(
            start_polling=AsyncMock(
                side_effect=TelegramNetworkError(
                    method=Mock(),
                    message="Request timeout error",
                )
            )
        )
        second_dispatcher = SimpleNamespace(start_polling=AsyncMock(return_value=None))
        dispatcher_factory = Mock(side_effect=[first_dispatcher, second_dispatcher])
        sleep = AsyncMock()

        await run_bot(
            bot_factory=bot_factory,
            dispatcher_factory=dispatcher_factory,
            sleep=sleep,
            retry_delay_seconds=0,
        )

        self.assertEqual(bot_factory.call_count, 2)
        self.assertEqual(dispatcher_factory.call_count, 2)
        sleep.assert_awaited_once_with(0)
        first_bot.session.close.assert_awaited_once()
        second_bot.session.close.assert_awaited_once()
