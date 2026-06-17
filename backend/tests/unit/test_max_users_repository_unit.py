from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.orm_models import User
from app.repositories.max_users import MaxUserRepository


@pytest.mark.asyncio
async def test_get_by_id_uses_linked_user_status_for_approval() -> None:
    session = AsyncMock()
    account = SimpleNamespace(is_active=True, id_user="user-1")
    channel = SimpleNamespace(is_verified=True, is_active=True)
    user = SimpleNamespace(status="active")

    account_result = MagicMock()
    account_result.scalar_one_or_none.return_value = account
    channel_result = MagicMock()
    channel_result.scalar_one_or_none.return_value = channel
    session.execute = AsyncMock(side_effect=[account_result, channel_result])
    session.get = AsyncMock(return_value=user)

    repo = MaxUserRepository(session)
    max_user = await repo.get_by_id("155719326")

    assert max_user is not None
    assert max_user.status == "approved"
    session.get.assert_awaited_once_with(User, "user-1")
