from __future__ import annotations

from app.core.datetime_utils import utc_now_naive
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth_models import UserNotificationPreference


class UserNotificationPreferenceRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, preference: UserNotificationPreference) -> None:
        self._session.add(preference)

    async def get_by_channel_id_and_type(
        self,
        *,
        channel_id: int,
        notification_type: str,
    ) -> UserNotificationPreference | None:
        stmt = (
            select(UserNotificationPreference)
            .where(
                UserNotificationPreference.id_contact_channel == channel_id,
                UserNotificationPreference.notification_type == notification_type,
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_channel_ids(self, *, channel_ids: list[int]) -> list[UserNotificationPreference]:
        if not channel_ids:
            return []
        stmt = select(UserNotificationPreference).where(
            UserNotificationPreference.id_contact_channel.in_(channel_ids)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def upsert(
        self,
        *,
        channel_id: int,
        notification_type: str,
        is_enabled: bool,
    ) -> UserNotificationPreference:
        existing = await self.get_by_channel_id_and_type(
            channel_id=channel_id,
            notification_type=notification_type,
        )
        if existing is None:
            preference = UserNotificationPreference(
                id_contact_channel=channel_id,
                notification_type=notification_type,
                is_enabled=is_enabled,
            )
            await self.add(preference)
            return preference

        existing.is_enabled = is_enabled
        existing.updated_at = utc_now_naive()
        return existing
