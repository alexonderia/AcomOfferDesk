from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth_models import UserAuthAccount


class UserAuthAccountRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_provider_subject(
        self,
        *,
        provider: str,
        subject: str,
        include_inactive: bool = False,
    ) -> UserAuthAccount | None:
        stmt = select(UserAuthAccount).where(
            UserAuthAccount.provider == provider,
            UserAuthAccount.external_subject_id == subject,
        )
        if not include_inactive:
            stmt = stmt.where(UserAuthAccount.is_active.is_(True))
        stmt = stmt.order_by(UserAuthAccount.is_active.desc(), UserAuthAccount.id.asc()).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_provider(
        self,
        *,
        user_id: str,
        provider: str,
        include_inactive: bool = False,
    ) -> UserAuthAccount | None:
        stmt = select(UserAuthAccount).where(
            UserAuthAccount.id_user == user_id,
            UserAuthAccount.provider == provider,
        )
        if not include_inactive:
            stmt = stmt.where(UserAuthAccount.is_active.is_(True))
        stmt = stmt.order_by(UserAuthAccount.is_active.desc(), UserAuthAccount.id.asc()).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(self, *, user_id: str) -> list[UserAuthAccount]:
        stmt = select(UserAuthAccount).where(UserAuthAccount.id_user == user_id).order_by(UserAuthAccount.id.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, account: UserAuthAccount) -> None:
        self._session.add(account)

    async def get_conflicting_subject(
        self,
        *,
        provider: str,
        subject: str,
        exclude_user_id: str | None = None,
    ) -> UserAuthAccount | None:
        stmt = select(UserAuthAccount).where(
            and_(
                UserAuthAccount.provider == provider,
                UserAuthAccount.external_subject_id == subject,
            )
        )
        if exclude_user_id:
            stmt = stmt.where(UserAuthAccount.id_user != exclude_user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def touch_login(
        self,
        *,
        account: UserAuthAccount,
        username: str | None,
        email: str | None,
    ) -> None:
        account.external_username = username
        account.external_email = email
        account.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
        account.is_active = True
