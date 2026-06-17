from __future__ import annotations

from app.core.datetime_utils import utc_now_naive
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import Conflict
from app.models.auth_models import UserAuthAccount, UserContactChannel
from app.models.orm_models import MaxUser, User
from app.repositories.max_compat import build_max_user, max_subject_value


class MaxUserRepository:
    """
    MAX compatibility repository.
    Works as a logical projection over:
    - user_auth_accounts(provider='max')
    - user_contact_channels(channel_type='max')
    and intentionally does not read/write any standalone max_users table.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def _load_linkage(self, max_user_id: int | str) -> tuple[UserAuthAccount | None, UserContactChannel | None]:
        subject = max_subject_value(max_user_id)
        account_stmt = (
            select(UserAuthAccount)
            .where(
                UserAuthAccount.provider == "max",
                UserAuthAccount.external_subject_id == subject,
            )
            .order_by(UserAuthAccount.is_active.desc(), UserAuthAccount.id.asc())
            .limit(1)
        )
        channel_stmt = (
            select(UserContactChannel)
            .where(
                UserContactChannel.channel_type == "max",
                UserContactChannel.channel_value == subject,
            )
            .order_by(
                UserContactChannel.is_active.desc(),
                UserContactChannel.is_primary.desc(),
                UserContactChannel.id.asc(),
            )
            .limit(1)
        )
        account = (await self._session.execute(account_stmt)).scalar_one_or_none()
        channel = (await self._session.execute(channel_stmt)).scalar_one_or_none()
        return account, channel

    async def get_by_id(self, max_user_id: int | str) -> MaxUser | None:
        account, channel = await self._load_linkage(max_user_id)
        user_status: str | None = None
        if account is not None:
            user = await self._session.get(User, account.id_user)
            user_status = user.status if user is not None else None
        return build_max_user(
            max_user_id=max_user_id,
            account_is_active=account.is_active if account is not None else None,
            channel_is_verified=channel.is_verified if channel is not None else None,
            channel_is_active=channel.is_active if channel is not None else None,
            user_status=user_status,
        )

    async def get_or_create(self, max_user_id: int | str, *, default_status: str = "review") -> MaxUser:
        existing = await self.get_by_id(max_user_id)
        if existing is not None:
            return existing
        return MaxUser(id=max_subject_value(max_user_id), status=default_status)

    async def exists(self, max_user_id: int | str) -> bool:
        return await self.get_by_id(max_user_id) is not None

    async def update_status(self, max_user: MaxUser, status: str) -> None:
        subject = max_subject_value(max_user.id)
        account_stmt = select(UserAuthAccount).where(
            UserAuthAccount.provider == "max",
            UserAuthAccount.external_subject_id == subject,
        )
        channel_stmt = select(UserContactChannel).where(
            UserContactChannel.channel_type == "max",
            UserContactChannel.channel_value == subject,
        )

        accounts = list((await self._session.execute(account_stmt)).scalars().all())
        channels = list((await self._session.execute(channel_stmt)).scalars().all())

        if not accounts and not channels:
            if status == "review":
                return
            raise Conflict("MAX account is not linked")

        now = utc_now_naive()
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

        max_user.status = status
