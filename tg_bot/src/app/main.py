from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from aiogram import Bot
from aiogram.exceptions import TelegramNetworkError
from aiogram.types import BotCommand

from app.core.config import settings
from app.handlers import setup_dispatcher

RETRY_DELAY_SECONDS = 10


async def run_bot(
    *,
    bot_factory: Callable[..., Bot] = Bot,
    dispatcher_factory: Callable[[], object] = setup_dispatcher,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    retry_delay_seconds: float = RETRY_DELAY_SECONDS,
) -> None:
    logger = logging.getLogger(__name__)

    while True:
        bot = bot_factory(token=settings.bot_token)
        try:
            try:
                await bot.set_my_commands(
                    [
                        BotCommand(command="start", description="Registration or open requests"),
                        BotCommand(command="info", description="Service and workflow information"),
                    ]
                )
            except TelegramNetworkError:
                logger.warning(
                    "Telegram API is temporarily unavailable during startup. Skip set_my_commands",
                    exc_info=True,
                )

            dispatcher = dispatcher_factory()
            await dispatcher.start_polling(bot)
            return
        except TelegramNetworkError:
            logger.warning(
                "Telegram API is unavailable during polling startup. Retry in %s seconds",
                retry_delay_seconds,
                exc_info=True,
            )
        finally:
            await bot.session.close()

        await sleep(retry_delay_seconds)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    await run_bot()


if __name__ == "__main__":
    asyncio.run(main())
