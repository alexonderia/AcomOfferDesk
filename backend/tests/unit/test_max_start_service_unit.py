from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.services.max_start import MaxStartService


@pytest.fixture
def service() -> MaxStartService:
    return MaxStartService(
        max_users=AsyncMock(),
        users=AsyncMock(),
        requests=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_new_max_user_returns_register(service: MaxStartService) -> None:
    service._max_users.get_or_create.return_value = SimpleNamespace(id="123", status="review")
    service._users.get_by_max_user_id.return_value = None

    result = await service.handle_start("123")

    assert result.action == "register"
    assert result.registration_url is not None
    assert result.existing_account_link_token == "123"
    assert "max_token=" in result.registration_url


@pytest.mark.asyncio
async def test_review_user_returns_pending(service: MaxStartService) -> None:
    service._max_users.get_or_create.return_value = SimpleNamespace(id="123", status="review")
    service._users.get_by_max_user_id.return_value = SimpleNamespace(
        id="contractor-1",
        status="review",
        id_role=settings.contractor_role_id,
    )

    result = await service.handle_start("123")

    assert result.action == "pending"


@pytest.mark.asyncio
async def test_active_contractor_with_approved_max_returns_open_requests(service: MaxStartService) -> None:
    service._max_users.get_or_create.return_value = SimpleNamespace(id="123", status="approved")
    service._users.get_by_max_user_id.return_value = SimpleNamespace(
        id="contractor-1",
        status="active",
        id_role=settings.contractor_role_id,
    )
    deadline = datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc)
    service._requests.list_open_for_contractor.return_value = [
        SimpleNamespace(id="req-1", description="Test request", deadline_at=deadline),
    ]

    result = await service.handle_start("123")

    assert result.action == "open_requests"
    assert len(result.requests) == 1
    assert result.requests[0].url.startswith("http://localhost:8080/login?next=")


@pytest.mark.asyncio
async def test_active_non_contractor_returns_pending(service: MaxStartService) -> None:
    service._max_users.get_or_create.return_value = SimpleNamespace(id="123", status="approved")
    service._users.get_by_max_user_id.return_value = SimpleNamespace(
        id="staff-1",
        status="active",
        id_role=settings.economist_role_id,
    )

    result = await service.handle_start("123")

    assert result.action == "pending"
    assert result.requests == []


@pytest.mark.asyncio
async def test_inactive_user_returns_blocked(service: MaxStartService) -> None:
    service._max_users.get_or_create.return_value = SimpleNamespace(id="123", status="approved")
    service._users.get_by_max_user_id.return_value = SimpleNamespace(
        id="contractor-1",
        status="inactive",
        id_role=settings.contractor_role_id,
    )

    result = await service.handle_start("123")

    assert result.action == "blocked"


@pytest.mark.asyncio
async def test_blacklist_user_returns_blocked(service: MaxStartService) -> None:
    service._max_users.get_or_create.return_value = SimpleNamespace(id="123", status="approved")
    service._users.get_by_max_user_id.return_value = SimpleNamespace(
        id="contractor-1",
        status="blacklist",
        id_role=settings.contractor_role_id,
    )

    result = await service.handle_start("123")

    assert result.action == "blocked"


@pytest.mark.asyncio
async def test_disapproved_max_channel_returns_blocked(service: MaxStartService) -> None:
    service._max_users.get_or_create.return_value = SimpleNamespace(id="123", status="disapproved")
    service._users.get_by_max_user_id.return_value = SimpleNamespace(
        id="contractor-1",
        status="active",
        id_role=settings.contractor_role_id,
    )

    result = await service.handle_start("123")

    assert result.action == "blocked"


@pytest.mark.asyncio
async def test_no_open_requests_returns_empty_list(service: MaxStartService) -> None:
    service._max_users.get_or_create.return_value = SimpleNamespace(id="123", status="approved")
    service._users.get_by_max_user_id.return_value = SimpleNamespace(
        id="contractor-1",
        status="active",
        id_role=settings.contractor_role_id,
    )
    service._requests.list_open_for_contractor.return_value = []

    result = await service.handle_start("123")

    assert result.action == "open_requests"
    assert result.requests == []
