from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import Conflict
from app.models.auth_models import UserAuthAccount, UserContactChannel
from app.models.orm_models import TgUser
from app.repositories.telegram_compat import build_tg_user, telegram_subject_value


class TgUserRepository:
    """
    Legacy Telegram compatibility repository.
    Works as a logical projection over:
    - user_auth_accounts(provider='telegram')
    - user_contact_channels(channel_type='telegram')
    and intentionally does not read/write any standalone tg_users table.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, tg_id: int) -> TgUser | None:
        subject = telegram_subject_value(tg_id)
        account_stmt = (
            select(UserAuthAccount)
            .where(
                UserAuthAccount.provider == "telegram",
                UserAuthAccount.external_subject_id == subject,
            )
            .order_by(UserAuthAccount.is_active.desc(), UserAuthAccount.id.asc())
            .limit(1)
        )
        channel_stmt = (
            select(UserContactChannel)
            .where(
                UserContactChannel.channel_type == "telegram",
                UserContactChannel.channel_value == subject,
            )
            .order_by(UserContactChannel.is_active.desc(), UserContactChannel.is_primary.desc(), UserContactChannel.id.asc())
            .limit(1)
        )
        account = (await self._session.execute(account_stmt)).scalar_one_or_none()
        channel = (await self._session.execute(channel_stmt)).scalar_one_or_none()
        return build_tg_user(
            tg_id=tg_id,
            account_is_active=account.is_active if account is not None else None,
            channel_is_verified=channel.is_verified if channel is not None else None,
            channel_is_active=channel.is_active if channel is not None else None,
        )

    async def get_or_create(self, tg_id: int, *, default_status: str = "review") -> TgUser:
        existing = await self.get_by_id(tg_id)
        if existing is not None:
            return existing
        return TgUser(id=tg_id, status=default_status)

    async def add(self, tg_user: TgUser) -> None:
        _ = tg_user
        # Unlinked Telegram identities are no longer persisted separately.
        return None

    async def exists(self, tg_id: int) -> bool:
        return await self.get_by_id(tg_id) is not None

    async def update_status(self, tg_user: TgUser, status: str) -> None:
        subject = telegram_subject_value(tg_user.id)
        account_stmt = select(UserAuthAccount).where(
            UserAuthAccount.provider == "telegram",
            UserAuthAccount.external_subject_id == subject,
        )
        channel_stmt = select(UserContactChannel).where(
            UserContactChannel.channel_type == "telegram",
            UserContactChannel.channel_value == subject,
        )

        accounts = list((await self._session.execute(account_stmt)).scalars().all())
        channels = list((await self._session.execute(channel_stmt)).scalars().all())

        if not accounts and not channels:
            if status == "review":
                return
            raise Conflict("Telegram account is not linked")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        is_active = status != "disapproved"
        is_verified = status == "approved"

        for account in accounts:
            account.is_active = is_active

        for channel in channels:
            channel.is_active = is_active
            channel.updated_at = now
            if is_verified:
                channel.is_verified = True
                channel.verified_at = channel.verified_at or now
            elif status == "review":
                channel.is_verified = False
                channel.verified_at = None

        tg_user.status = status
