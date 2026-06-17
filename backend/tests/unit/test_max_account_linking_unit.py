from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.domain.exceptions import Conflict
from app.services.max_account_linking import link_max_account
from app.services.max_registration_links import create_max_existing_link_token, resolve_max_existing_link_token


@pytest.mark.asyncio
async def test_resolve_max_existing_link_token_roundtrip() -> None:
    token = create_max_existing_link_token(max_user_id="max-123")

    resolved = await resolve_max_existing_link_token(token)

    assert resolved == "max-123"


@pytest.mark.asyncio
async def test_link_max_account_rejects_conflicting_inactive_binding() -> None:
    user_auth_accounts = AsyncMock()
    user_contact_channels = AsyncMock()
    user_auth_accounts.get_conflicting_subject.return_value = SimpleNamespace(id_user="other-user")

    with pytest.raises(Conflict, match="MAX account is already linked to another user"):
        await link_max_account(
            user_auth_accounts=user_auth_accounts,
            user_contact_channels=user_contact_channels,
            user_id="user-1",
            max_user_id="max-123",
            is_verified=True,
        )


@pytest.mark.asyncio
async def test_link_max_account_rejects_conflicting_channel() -> None:
    user_auth_accounts = AsyncMock()
    user_contact_channels = AsyncMock()
    user_auth_accounts.get_conflicting_subject.return_value = None
    user_contact_channels.get_by_value.return_value = [SimpleNamespace(id_user="other-user")]

    with pytest.raises(Conflict, match="MAX channel is already linked to another user"):
        await link_max_account(
            user_auth_accounts=user_auth_accounts,
            user_contact_channels=user_contact_channels,
            user_id="user-1",
            max_user_id="max-123",
            is_verified=True,
        )


@pytest.mark.asyncio
async def test_link_max_account_marks_channel_verified_for_existing_account_flow() -> None:
    user_auth_accounts = AsyncMock()
    user_contact_channels = AsyncMock()
    user_auth_accounts.get_conflicting_subject.return_value = None
    user_contact_channels.get_by_value.return_value = []
    user_auth_accounts.get_by_user_provider.return_value = None

    await link_max_account(
        user_auth_accounts=user_auth_accounts,
        user_contact_channels=user_contact_channels,
        user_id="user-1",
        max_user_id="max-123",
        is_verified=True,
    )

    user_contact_channels.upsert_channel.assert_awaited_once_with(
        user_id="user-1",
        channel_type="max",
        channel_value="max-123",
        is_verified=True,
        is_primary=True,
    )
