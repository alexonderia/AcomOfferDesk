from __future__ import annotations

import os
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

os.environ.setdefault("MAX_BOT_TOKEN", "test-token")
os.environ.setdefault("BACKEND_BASE_URL", "http://backend:8000")

from app.handlers.info import handle_info
from app.handlers.start import handle_start
from app.services.backend_client import BackendClientError, MaxOpenRequestItem, MaxStartResponse
from app.ui import messages


def _build_event(*, text: str = "/start", user_id: int = 123) -> SimpleNamespace:
    sender = SimpleNamespace(
        user_id=user_id,
        username="max_user",
        first_name="Иван",
        last_name="Иванов",
    )
    message = SimpleNamespace(
        sender=sender,
        answer=AsyncMock(),
    )
    return SimpleNamespace(message=message)


@pytest.mark.asyncio
async def test_start_register_action() -> None:
    event = _build_event()
    response = MaxStartResponse(
        action="register",
        registration_url="https://example.com/register",
        existing_account_link_token="123456789",
        requests=[],
    )

    with patch("app.handlers.start.get_backend_client") as get_client:
        get_client.return_value.start = AsyncMock(return_value=response)
        await handle_start(event)

    event.message.answer.assert_awaited_once()
    answer_text = event.message.answer.await_args.args[0]
    assert "123456789" in answer_text
    assert "MAX ID" in answer_text


@pytest.mark.asyncio
async def test_start_pending_action() -> None:
    event = _build_event()
    response = MaxStartResponse(action="pending", registration_url=None, existing_account_link_token=None, requests=[])

    with patch("app.handlers.start.get_backend_client") as get_client:
        get_client.return_value.start = AsyncMock(return_value=response)
        await handle_start(event)

    assert messages.PENDING_REVIEW in event.message.answer.await_args.args[0]


@pytest.mark.asyncio
async def test_start_open_requests_action() -> None:
    event = _build_event()
    response = MaxStartResponse(
        action="open_requests",
        registration_url=None,
        existing_account_link_token=None,
        requests=[
            MaxOpenRequestItem(
                id="1",
                description="Заявка",
                deadline_at=datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc),
                url="https://example.com/requests/1",
            )
        ],
    )

    with patch("app.handlers.start.get_backend_client") as get_client:
        get_client.return_value.start = AsyncMock(return_value=response)
        await handle_start(event)

    assert event.message.answer.await_count == 2
    first_call = event.message.answer.await_args_list[0].args[0]
    second_call = event.message.answer.await_args_list[1].args[0]
    assert messages.OPEN_REQUESTS_HEADER in first_call
    assert "Заявка №1" in second_call


@pytest.mark.asyncio
async def test_start_blocked_action() -> None:
    event = _build_event()
    response = MaxStartResponse(action="blocked", registration_url=None, existing_account_link_token=None, requests=[])

    with patch("app.handlers.start.get_backend_client") as get_client:
        get_client.return_value.start = AsyncMock(return_value=response)
        await handle_start(event)

    assert messages.BLOCKED_ACCESS in event.message.answer.await_args.args[0]


@pytest.mark.asyncio
async def test_start_backend_error_shows_safe_message() -> None:
    event = _build_event()

    with patch("app.handlers.start.get_backend_client") as get_client:
        get_client.return_value.start = AsyncMock(side_effect=BackendClientError("fail"))
        await handle_start(event)

    assert event.message.answer.await_args.args[0] == messages.SERVICE_UNAVAILABLE


@pytest.mark.asyncio
async def test_info_shows_instruction() -> None:
    event = _build_event(text="/info")

    await handle_info(event)

    assert event.message.answer.await_args.args[0] == messages.INFO_TEXT
