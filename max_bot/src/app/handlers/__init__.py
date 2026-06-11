from __future__ import annotations

from maxapi import Dispatcher

from app.handlers.bot_started import router as bot_started_router
from app.handlers.info import router as info_router
from app.handlers.start import router as start_router


def setup_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_routers(bot_started_router, start_router, info_router)
    return dispatcher
