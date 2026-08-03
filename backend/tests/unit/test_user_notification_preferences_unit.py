from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.user_notification_preferences import UserNotificationPreferencesService


@pytest.mark.asyncio
async def test_get_state_defaults_to_email_only_when_email_is_available() -> None:
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
    ]
    preferences.list_by_channel_ids.return_value = []
    profiles.get_by_id.return_value = SimpleNamespace(mail="user@example.com")
    service = UserNotificationPreferencesService(channels, preferences, profiles=profiles)

    state = await service.get_state(user_id="user-1")

    assert state.mode == "email_only"
    assert state.email_available is True
    assert state.email == "user@example.com"
    assert state.preferences["chat"].email is True
    assert state.preferences["system"].email is True


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
        [email_channel],
    ]
    channels.upsert_channel.return_value = email_channel
    preferences.list_by_channel_ids.side_effect = [
        [],
        [
            SimpleNamespace(id_contact_channel=10, notification_type="chat", is_enabled=False),
            SimpleNamespace(id_contact_channel=10, notification_type="request", is_enabled=False),
            SimpleNamespace(id_contact_channel=10, notification_type="offer", is_enabled=False),
            SimpleNamespace(id_contact_channel=10, notification_type="system", is_enabled=False),
        ],
        [
            SimpleNamespace(id_contact_channel=10, notification_type="chat", is_enabled=False),
            SimpleNamespace(id_contact_channel=10, notification_type="request", is_enabled=False),
            SimpleNamespace(id_contact_channel=10, notification_type="offer", is_enabled=False),
            SimpleNamespace(id_contact_channel=10, notification_type="system", is_enabled=False),
        ],
    ]
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
    assert all(item.email is False for item in state.preferences.values())


@pytest.mark.asyncio
async def test_update_preferences_persists_detailed_matrix() -> None:
    channels = AsyncMock()
    preferences = AsyncMock()
    profiles = AsyncMock()
    channels.list_by_user.return_value = [
        SimpleNamespace(
            id=11,
            channel_type="email",
            channel_value="user@example.com",
            is_active=True,
            is_verified=True,
        ),
    ]
    preferences.list_by_channel_ids.side_effect = [
        [],
        [
            SimpleNamespace(id_contact_channel=11, notification_type="chat", is_enabled=True),
            SimpleNamespace(id_contact_channel=11, notification_type="request", is_enabled=True),
            SimpleNamespace(id_contact_channel=11, notification_type="offer", is_enabled=False),
            SimpleNamespace(id_contact_channel=11, notification_type="system", is_enabled=True),
        ],
    ]
    profiles.get_by_id.return_value = SimpleNamespace(mail="user@example.com")
    service = UserNotificationPreferencesService(channels, preferences, profiles=profiles)

    state = await service.update_preferences(
        user_id="user-1",
        preferences={
            "chat": {"email": True},
            "request": {"email": True},
            "offer": {"email": False},
            "system": {"email": True},
        },
    )

    assert preferences.upsert.await_count == 4
    assert state.mode == "custom"
    assert state.preferences["chat"].email is True
    assert state.preferences["offer"].email is False


@pytest.mark.asyncio
async def test_is_channel_enabled_rejects_unsupported_channel() -> None:
    channels = AsyncMock()
    preferences = AsyncMock()
    profiles = AsyncMock()
    service = UserNotificationPreferencesService(channels, preferences, profiles=profiles)

    is_enabled = await service.is_channel_enabled(
        user_id="user-2",
        channel_type="sms",
        notification_type="offer",
    )

    assert is_enabled is False
