from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.user_notification_preferences import UserNotificationPreferencesService


@pytest.mark.asyncio
async def test_get_state_defaults_to_all_when_both_channels_available() -> None:
    channels = AsyncMock()
    preferences = AsyncMock()
    profiles = AsyncMock()
    channels.list_by_user.return_value = [
        SimpleNamespace(
            id=1,
            channel_type="email",
            channel_value="user@example.com",
            is_active=True,
            is_verified=True,
        ),
        SimpleNamespace(
            id=2,
            channel_type="max",
            channel_value="max-user-1",
            is_active=True,
            is_verified=True,
        ),
    ]
    preferences.list_by_channel_ids.return_value = []
    profiles.get_by_id.return_value = SimpleNamespace(mail="user@example.com")
    service = UserNotificationPreferencesService(channels, preferences, profiles=profiles)

    state = await service.get_state(user_id="user-1")

    assert state.mode == "all"
    assert state.email_available is True
    assert state.max_available is True
    assert state.email == "user@example.com"
    assert state.max_user_id == "max-user-1"


@pytest.mark.asyncio
async def test_update_mode_creates_email_channel_for_profile_only_email() -> None:
    channels = AsyncMock()
    preferences = AsyncMock()
    profiles = AsyncMock()
    email_channel = SimpleNamespace(
        id=10,
        channel_type="email",
        channel_value="user@example.com",
        is_active=True,
        is_verified=False,
    )
    channels.list_by_user.side_effect = [
        [],
        [email_channel],
    ]
    channels.upsert_channel.return_value = email_channel
    preferences.list_by_channel_ids.return_value = []
    profiles.get_by_id.return_value = SimpleNamespace(mail="user@example.com")
    service = UserNotificationPreferencesService(channels, preferences, profiles=profiles)

    state = await service.update_mode(user_id="user-1", mode="none")

    channels.upsert_channel.assert_awaited_once_with(
        user_id="user-1",
        channel_type="email",
        channel_value="user@example.com",
        is_verified=False,
        is_primary=True,
    )
    assert preferences.upsert.await_count == 4
    for call in preferences.upsert.await_args_list:
        assert call.kwargs["channel_id"] == 10
        assert call.kwargs["is_enabled"] is False
    assert state.mode == "none"
    assert state.email_available is True


@pytest.mark.asyncio
async def test_is_channel_enabled_respects_saved_max_preference() -> None:
    channels = AsyncMock()
    preferences = AsyncMock()
    profiles = AsyncMock()
    channels.get_primary_by_type.return_value = SimpleNamespace(
        id=20,
        channel_type="max",
        channel_value="max-user-2",
        is_active=True,
        is_verified=True,
    )
    preferences.get_by_channel_id_and_type.return_value = SimpleNamespace(is_enabled=False)
    service = UserNotificationPreferencesService(channels, preferences, profiles=profiles)

    is_enabled = await service.is_channel_enabled(
        user_id="user-2",
        channel_type="max",
        notification_type="offer",
    )

    assert is_enabled is False
