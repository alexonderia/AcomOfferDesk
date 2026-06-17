from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Select, String, and_, cast, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm_models import UserNotification


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    @staticmethod
    def _payload_text(key_name: str):
        # Use JSON text extraction (->>) so scalar values compare without JSON quotes.
        return cast(UserNotification.payload.op("->>")(key_name), String)

    async def create(self, notification: UserNotification) -> UserNotification:
        self._session.add(notification)
        await self._session.flush()
        return notification

    async def create_many(self, notifications: Sequence[UserNotification]) -> list[UserNotification]:
        if not notifications:
            return []
        self._session.add_all(notifications)
        await self._session.flush()
        return list(notifications)

    async def list_for_user(self, *, user_id: str, limit: int, offset: int) -> list[UserNotification]:
        stmt: Select[tuple[UserNotification]] = (
            select(UserNotification)
            .where(
                UserNotification.user_id == user_id,
                self._visible_notification_predicate(),
            )
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
            self._visible_notification_predicate(),
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

    async def exists_by_type_user_and_correlation_id(
        self,
        *,
        user_id: str,
        notification_type: str,
        correlation_id: str,
    ) -> bool:
        stmt = select(UserNotification.id).where(
            UserNotification.user_id == user_id,
            UserNotification.type == notification_type,
            NotificationRepository._payload_text("correlation_id") == correlation_id,
        ).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def exists_by_type_user_and_payload_key(
        self,
        *,
        user_id: str,
        notification_type: str,
        key_name: str,
        key_value: str,
    ) -> bool:
        stmt = select(UserNotification.id).where(
            UserNotification.user_id == user_id,
            UserNotification.type == notification_type,
            NotificationRepository._payload_text(key_name) == key_value,
        ).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_by_user_and_payload_key(
        self,
        *,
        user_id: str,
        key_name: str,
        key_value: str,
        notification_type: str | None = None,
    ) -> UserNotification | None:
        notifications = await self.list_by_user_and_payload_key(
            user_id=user_id,
            key_name=key_name,
            key_value=key_value,
            notification_type=notification_type,
        )
        if not notifications:
            return None
        return notifications[0]

    async def list_by_user_and_payload_key(
        self,
        *,
        user_id: str,
        key_name: str,
        key_value: str,
        notification_type: str | None = None,
    ) -> list[UserNotification]:
        predicates = [
            UserNotification.user_id == user_id,
            NotificationRepository._payload_text(key_name) == key_value,
        ]
        if notification_type is not None:
            predicates.append(UserNotification.type == notification_type)
        stmt = (
            select(UserNotification)
            .where(and_(*predicates))
            .order_by(UserNotification.id.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_ids(self, notification_ids: Sequence[int]) -> int:
        if not notification_ids:
            return 0
        stmt = delete(UserNotification).where(UserNotification.id.in_(notification_ids))
        result = await self._session.execute(stmt)
        return int(result.rowcount or 0)

    async def save(self, notification: UserNotification) -> UserNotification:
        await self._session.flush()
        await self._session.refresh(notification)
        return notification

    @staticmethod
    def _visible_notification_predicate():
        tracking_flag = NotificationRepository._payload_text("tracking_only")
        return or_(
            UserNotification.payload.is_(None),
            tracking_flag.is_(None),
            tracking_flag != "true",
        )
