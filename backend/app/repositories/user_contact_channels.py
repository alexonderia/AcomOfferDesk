from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth_models import UserContactChannel


class UserContactChannelRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, channel: UserContactChannel) -> None:
        self._session.add(channel)

    async def get_primary_by_type(
        self,
        *,
        user_id: str,
        channel_type: str,
        include_inactive: bool = False,
    ) -> UserContactChannel | None:
        stmt = (
            select(UserContactChannel)
            .where(
                UserContactChannel.id_user == user_id,
                UserContactChannel.channel_type == channel_type,
            )
            .order_by(UserContactChannel.is_primary.desc(), UserContactChannel.id.asc())
        )
        if not include_inactive:
            stmt = stmt.where(UserContactChannel.is_active.is_(True))
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_by_value(self, *, channel_type: str, channel_value: str) -> list[UserContactChannel]:
        stmt = select(UserContactChannel).where(
            UserContactChannel.channel_type == channel_type,
            UserContactChannel.channel_value == channel_value,
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def upsert_channel(
        self,
        *,
        user_id: str,
        channel_type: str,
        channel_value: str,
        is_verified: bool,
        is_primary: bool,
    ) -> UserContactChannel:
        # Reuse inactive channel rows to preserve uniqueness by (channel_type, channel_value)
        # and allow clean re-activation of legacy Telegram links.
        existing = await self.get_primary_by_type(
            user_id=user_id,
            channel_type=channel_type,
            include_inactive=True,
        )
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if existing is None:
            channel = UserContactChannel(
                id_user=user_id,
                channel_type=channel_type,
                channel_value=channel_value,
                is_verified=is_verified,
                verified_at=now if is_verified else None,
                is_primary=is_primary,
                is_active=True,
            )
            await self.add(channel)
            return channel

        existing.channel_value = channel_value
        existing.is_primary = is_primary
        existing.is_active = True
        existing.updated_at = now
        if is_verified:
            existing.is_verified = True
            existing.verified_at = now
        return existing
