from __future__ import annotations

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm_models import UserNotification


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, notification: UserNotification) -> UserNotification:
        self._session.add(notification)
        await self._session.flush()
        return notification

    async def list_for_user(self, *, user_id: str, limit: int, offset: int) -> list[UserNotification]:
        stmt: Select[tuple[UserNotification]] = (
            select(UserNotification)
            .where(UserNotification.user_id == user_id)
            .order_by(UserNotification.created_at.desc(), UserNotification.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_unread(self, *, user_id: str) -> int:
        stmt = select(func.count(UserNotification.id)).where(
            UserNotification.user_id == user_id,
            UserNotification.read_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def mark_as_read(self, *, user_id: str, notification_id: int) -> UserNotification | None:
        stmt = select(UserNotification).where(
            UserNotification.id == notification_id,
            UserNotification.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        notification = result.scalar_one_or_none()
        if notification is None:
            return None
        if notification.read_at is None:
            await self._session.execute(
                update(UserNotification)
                .where(UserNotification.id == notification.id)
                .values(read_at=func.now())
            )
            await self._session.refresh(notification)
        return notification

    async def mark_all_as_read(self, *, user_id: str) -> int:
        stmt = (
            update(UserNotification)
            .where(
                UserNotification.user_id == user_id,
                UserNotification.read_at.is_(None),
            )
            .values(read_at=func.now())
        )
        result = await self._session.execute(stmt)
        return int(result.rowcount or 0)

