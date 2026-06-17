from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.repositories.user_contact_channels import UserContactChannelRepository


@pytest.mark.asyncio
async def test_upsert_channel_resets_verification_when_value_changes() -> None:
    repository = UserContactChannelRepository(session=AsyncMock())
    existing = SimpleNamespace(
        channel_value="old-max-id",
        is_primary=False,
        is_active=False,
        updated_at=None,
        is_verified=True,
        verified_at="2026-06-11T10:00:00",
    )
    repository.get_primary_by_type = AsyncMock(return_value=existing)  # type: ignore[method-assign]

    result = await repository.upsert_channel(
        user_id="user-1",
        channel_type="max",
        channel_value="new-max-id",
        is_verified=False,
        is_primary=True,
    )

    assert result is existing
    assert existing.channel_value == "new-max-id"
    assert existing.is_primary is True
    assert existing.is_active is True
    assert existing.is_verified is False
    assert existing.verified_at is None


@pytest.mark.asyncio
async def test_upsert_channel_keeps_existing_verification_for_same_value() -> None:
    repository = UserContactChannelRepository(session=AsyncMock())
    existing = SimpleNamespace(
        channel_value="same-max-id",
        is_primary=False,
        is_active=False,
        updated_at=None,
        is_verified=True,
        verified_at="2026-06-11T10:00:00",
    )
    repository.get_primary_by_type = AsyncMock(return_value=existing)  # type: ignore[method-assign]

    await repository.upsert_channel(
        user_id="user-1",
        channel_type="max",
        channel_value="same-max-id",
        is_verified=False,
        is_primary=True,
    )

    assert existing.is_verified is True
    assert existing.verified_at == "2026-06-11T10:00:00"
