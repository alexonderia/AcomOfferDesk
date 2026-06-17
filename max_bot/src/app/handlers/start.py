from __future__ import annotations

import logging

from maxapi.dispatcher import Router
from maxapi.filters.command import CommandStart
from maxapi.types.updates.message_created import MessageCreated

from app.services.backend_client import BackendClientError, get_backend_client
from app.ui import keyboards, messages

router = Router(router_id="start")
logger = logging.getLogger(__name__)


def _extract_max_user_id(event: MessageCreated) -> str | None:
    sender = getattr(event.message, "sender", None)
    if sender is None:
        return None
    user_id = getattr(sender, "user_id", None)
    if user_id is None:
        return None
    return str(user_id)


def _format_deadline(deadline_at) -> str | None:
    if deadline_at is None:
        return None
    return deadline_at.strftime("%d.%m.%Y, %H:%M")


@router.message_created(CommandStart())
async def handle_start(event: MessageCreated) -> None:
    max_user_id = _extract_max_user_id(event)
    if max_user_id is None:
        return

    logger.info("Processing /start for MAX user")
    try:
        client = get_backend_client()
        sender = event.message.sender
        result = await client.start(
            max_user_id,
            username=getattr(sender, "username", None),
            first_name=getattr(sender, "first_name", None),
            last_name=getattr(sender, "last_name", None),
        )
    except BackendClientError:
        logger.warning("Backend client error during /start", exc_info=True)
        await event.message.answer(messages.SERVICE_UNAVAILABLE)
        return

    logger.info("Backend /start action=%s", result.action)

    if result.action == "blocked":
        await event.message.answer(messages.BLOCKED_ACCESS)
        return

    if result.action == "pending":
        await event.message.answer(messages.PENDING_REVIEW)
        return

    if result.action == "register":
        keyboard = keyboards.registration_keyboard(result.registration_url)
        attachments = [keyboard] if keyboard is not None else None
        await event.message.answer(
            messages.format_register_intro(existing_account_link_token=result.existing_account_link_token),
            attachments=attachments,
        )
        return

    if result.action == "open_requests":
        if not result.requests:
            await event.message.answer(messages.NO_OPEN_REQUESTS)
            return
        await event.message.answer(messages.OPEN_REQUESTS_HEADER)
        for request in result.requests:
            keyboard = keyboards.request_keyboard(request.url)
            attachments = [keyboard] if keyboard is not None else None
            await event.message.answer(
                messages.format_request_message(
                    request_id=request.id,
                    description=request.description,
                    deadline_at=_format_deadline(request.deadline_at),
                ),
                attachments=attachments,
            )
        return

    await event.message.answer(messages.SERVICE_UNAVAILABLE)
