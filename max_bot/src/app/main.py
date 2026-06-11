from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from maxapi import Bot

from app.core.config import settings
from app.handlers import setup_dispatcher
from app.services.bot_commands import register_bot_commands

RETRY_DELAY_SECONDS = 10
_DEFAULT_MAX_API_BASE_URL = "https://platform-api.max.ru"


async def run_bot(
    *,
    bot_factory: Callable[..., Bot] = Bot,
    dispatcher_factory: Callable[[], object] = setup_dispatcher,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    retry_delay_seconds: float = RETRY_DELAY_SECONDS,
    register_commands: Callable[..., Awaitable[None]] = register_bot_commands,
) -> None:
    logger = logging.getLogger(__name__)
    dispatcher = dispatcher_factory()

    while True:
        bot = bot_factory(token=settings.max_bot_token)
        try:
            if settings.max_polling_enabled:
                try:
                    await bot.delete_webhook()
                except Exception:
                    logger.warning("Failed to delete MAX webhook before polling", exc_info=True)
                await register_commands(
                    token=settings.max_bot_token,
                    api_base_url=_DEFAULT_MAX_API_BASE_URL,
                    timeout_seconds=settings.max_bot_timeout_seconds,
                )
                await dispatcher.start_polling(bot)
            return
        except Exception:
            logger.warning(
                "MAX polling failed. Retry in %s seconds",
                retry_delay_seconds,
                exc_info=True,
            )
        finally:
            close = getattr(bot, "close", None)
            if callable(close):
                await close()
        await sleep(retry_delay_seconds)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    await run_bot()


if __name__ == "__main__":
    asyncio.run(main())
