from __future__ import annotations

from app.models.auth_models import UserAuthAccount
from app.repositories.max_compat import max_subject_value
from app.repositories.user_auth_accounts import UserAuthAccountRepository
from app.repositories.user_contact_channels import UserContactChannelRepository
from app.domain.exceptions import Conflict


async def link_max_account(
    *,
    user_auth_accounts: UserAuthAccountRepository,
    user_contact_channels: UserContactChannelRepository,
    user_id: str,
    max_user_id: str,
    is_verified: bool,
) -> None:
    subject = max_subject_value(max_user_id)
    conflicting = await user_auth_accounts.get_conflicting_subject(
        provider="max",
        subject=subject,
        exclude_user_id=user_id,
    )
    if conflicting is not None:
        raise Conflict("MAX account is already linked to another user")

    existing_channels = await user_contact_channels.get_by_value(
        channel_type="max",
        channel_value=subject,
    )
    if any(channel.id_user != user_id for channel in existing_channels):
        raise Conflict("MAX channel is already linked to another user")

    max_account = await user_auth_accounts.get_by_user_provider(
        user_id=user_id,
        provider="max",
        include_inactive=True,
    )
    if max_account is None:
        await user_auth_accounts.add(
            UserAuthAccount(
                id_user=user_id,
                provider="max",
                external_subject_id=subject,
                external_username=None,
                external_email=None,
                is_active=True,
            )
        )
    else:
        max_account.external_subject_id = subject
        max_account.is_active = True

    await user_contact_channels.upsert_channel(
        user_id=user_id,
        channel_type="max",
        channel_value=subject,
        is_verified=is_verified,
        is_primary=True,
    )
