from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm_models import UserStatusPeriod


class UserStatusPeriodRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, period: UserStatusPeriod) -> None:
        self._session.add(period)

    async def list_for_user(self, *, user_id: str) -> list[UserStatusPeriod]:
        query: Select[tuple[UserStatusPeriod]] = (
            select(UserStatusPeriod)
            .where(UserStatusPeriod.id_user == user_id)
            .order_by(UserStatusPeriod.started_at.desc(), UserStatusPeriod.id.desc())
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_active_for_user(self, *, user_id: str) -> UserStatusPeriod | None:
        query: Select[tuple[UserStatusPeriod]] = (
            select(UserStatusPeriod)
            .where(
                UserStatusPeriod.id_user == user_id,
                UserStatusPeriod.started_at <= func.now(),
                UserStatusPeriod.ended_at >= func.now(),
            )
            .order_by(UserStatusPeriod.ended_at.desc(), UserStatusPeriod.id.desc())
            .limit(1)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_for_users(self, *, user_ids: list[str]) -> dict[str, list[UserStatusPeriod]]:
        if not user_ids:
            return {}

        query: Select[tuple[UserStatusPeriod]] = (
            select(UserStatusPeriod)
            .where(UserStatusPeriod.id_user.in_(user_ids))
            .order_by(
                UserStatusPeriod.id_user.asc(),
                UserStatusPeriod.started_at.desc(),
                UserStatusPeriod.id.desc(),
            )
        )
        result = await self._session.execute(query)
        grouped: dict[str, list[UserStatusPeriod]] = {}
        for period in result.scalars().all():
            grouped.setdefault(period.id_user, []).append(period)
        return grouped

    async def list_active_for_users(self, *, user_ids: list[str]) -> dict[str, UserStatusPeriod]:
        if not user_ids:
            return {}

        query: Select[tuple[UserStatusPeriod]] = (
            select(UserStatusPeriod)
            .where(
                UserStatusPeriod.id_user.in_(user_ids),
                UserStatusPeriod.started_at <= func.now(),
                UserStatusPeriod.ended_at >= func.now(),
            )
            .order_by(
                UserStatusPeriod.id_user.asc(),
                UserStatusPeriod.ended_at.desc(),
                UserStatusPeriod.id.desc(),
            )
        )
        result = await self._session.execute(query)
        active_by_user: dict[str, UserStatusPeriod] = {}
        for period in result.scalars().all():
            if period.id_user not in active_by_user:
                active_by_user[period.id_user] = period
        return active_by_user

    async def get_overlapping_for_user(
        self,
        *,
        user_id: str,
        started_at: datetime,
        ended_at: datetime,
    ) -> UserStatusPeriod | None:
        query: Select[tuple[UserStatusPeriod]] = (
            select(UserStatusPeriod)
            .where(
                UserStatusPeriod.id_user == user_id,
                and_(
                    UserStatusPeriod.started_at <= ended_at,
                    UserStatusPeriod.ended_at >= started_at,
                ),
            )
            .order_by(UserStatusPeriod.started_at.asc(), UserStatusPeriod.id.asc())
            .limit(1)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def list_starting_soon_for_users(
        self,
        *,
        user_ids: list[str],
        window: timedelta,
    ) -> list[UserStatusPeriod]:
        if not user_ids:
            return []

        query: Select[tuple[UserStatusPeriod]] = (
            select(UserStatusPeriod)
            .where(
                UserStatusPeriod.id_user.in_(user_ids),
                UserStatusPeriod.started_at > func.now(),
                UserStatusPeriod.started_at <= func.now() + window,
            )
            .order_by(
                UserStatusPeriod.started_at.asc(),
                UserStatusPeriod.id_user.asc(),
                UserStatusPeriod.id.asc(),
            )
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def list_next_for_users(self, *, user_ids: list[str]) -> list[UserStatusPeriod]:
        if not user_ids:
            return []

        query: Select[tuple[UserStatusPeriod]] = (
            select(UserStatusPeriod)
            .where(
                UserStatusPeriod.id_user.in_(user_ids),
                UserStatusPeriod.started_at > func.now(),
            )
            .order_by(
                UserStatusPeriod.id_user.asc(),
                UserStatusPeriod.started_at.asc(),
                UserStatusPeriod.id.asc(),
            )
        )
        result = await self._session.execute(query)

        periods_by_user: dict[str, UserStatusPeriod] = {}
        for period in result.scalars().all():
            if period.id_user not in periods_by_user:
                periods_by_user[period.id_user] = period

        return list(periods_by_user.values())
