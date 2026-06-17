from __future__ import annotations

import logging

from maxapi.dispatcher import Router
from maxapi.types.updates.bot_started import BotStarted

from app.ui import messages

router = Router(router_id="bot_started")
logger = logging.getLogger(__name__)


@router.bot_started()
async def handle_bot_started(event: BotStarted) -> None:
    logger.info("MAX bot started by user_id=%s", event.user.user_id)
    await event.bot.send_message(
        chat_id=event.chat_id,
        text=messages.BOT_WELCOME,
    )
