from __future__ import annotations

from maxapi.dispatcher import Router
from maxapi.filters.command import Command
from maxapi.types.updates.message_created import MessageCreated

from app.ui import messages

router = Router(router_id="info")


@router.message_created(Command("info"))
async def handle_info(event: MessageCreated) -> None:
    await event.message.answer(messages.INFO_TEXT)
