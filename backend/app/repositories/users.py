from __future__ import annotations

from sqlalchemy import BigInteger, and_, cast, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, with_expression

from app.models.auth_models import UserAuthAccount, UserContactChannel
from app.models.orm_models import (
    ChatParticipant,
    CompanyContact,
    Message,
    MessageReceipt,
    Offer,
    Profile,
    Request,
    RequestHiddenContractor,
    Role,
    TgUser,
    EconomyPlan,
    User,
    UserStatusPeriod,
)
from app.repositories.telegram_compat import build_tg_user, telegram_subject_value


def _telegram_id_expr():
    return (
        select(cast(UserAuthAccount.external_subject_id, BigInteger))
        .where(
            UserAuthAccount.id_user == User.id,
            UserAuthAccount.provider == "telegram",
        )
        .order_by(UserAuthAccount.is_active.desc(), UserAuthAccount.id.asc())
        .limit(1)
        .scalar_subquery()
    )


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: str) -> User | None:
        stmt = (
            select(User)
            .options(with_expression(User.tg_user_id, _telegram_id_expr()))
            .where(User.id == user_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_role_by_id(self, role_id: int) -> Role | None:
        result = await self._session.execute(select(Role).where(Role.id == role_id))
        return result.scalar_one_or_none()

    async def get_by_tg_user_id(self, tg_user_id: int) -> User | None:
        subject = telegram_subject_value(tg_user_id)
        stmt = (
            select(User)
            .join(
                UserAuthAccount,
                and_(
                    UserAuthAccount.id_user == User.id,
                    UserAuthAccount.provider == "telegram",
                    UserAuthAccount.external_subject_id == subject,
                ),
            )
            .options(
                with_expression(
                    User.tg_user_id,
                    cast(UserAuthAccount.external_subject_id, BigInteger),
                )
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists(self, user_id: str) -> bool:
        result = await self._session.execute(select(User.id).where(User.id == user_id))
        return result.scalar_one_or_none() is not None

    async def list_by_email(self, *, email: str) -> list[User]:
        normalized_email = email.strip().lower()
        if not normalized_email:
            return []

        stmt = (
            select(User)
            .options(with_expression(User.tg_user_id, _telegram_id_expr()))
            .outerjoin(Profile, Profile.id == User.id)
            .outerjoin(CompanyContact, CompanyContact.id == User.id)
            .where(
                or_(
                    func.lower(Profile.mail) == normalized_email,
                    func.lower(CompanyContact.mail) == normalized_email,
                )
            )
            .order_by(User.id.asc())
        )
        result = await self._session.execute(stmt)

        users: list[User] = []
        seen_user_ids: set[str] = set()
        for user in result.scalars().all():
            if user.id in seen_user_ids:
                continue
            seen_user_ids.add(user.id)
            users.append(user)
        return users

    async def add(self, user: User) -> None:
        self._session.add(user)

    async def flush(self) -> None:
        await self._session.flush()

    async def delete_by_id(self, *, user_id: str) -> None:
        user = await self.get_by_id(user_id)
        if user is not None:
            await self._session.delete(user)

    async def list_subordinates_with_profiles(self, *, manager_user_id: str) -> list[tuple[User, Profile | None]]:
        stmt = (
            select(User, Profile)
            .options(with_expression(User.tg_user_id, _telegram_id_expr()))
            .outerjoin(Profile, Profile.id == User.id)
            .where(User.id_parent == manager_user_id)
            .order_by(User.id)
        )
        result = await self._session.execute(stmt)
        return list(result.all())

    async def list_direct_subordinates_with_profiles_and_roles(
        self,
        *,
        manager_user_id: str,
        include_inactive: bool = False,
    ) -> list[tuple[User, Profile | None, Role]]:
        stmt = (
            select(User, Profile, Role)
            .options(with_expression(User.tg_user_id, _telegram_id_expr()))
            .join(Role, Role.id == User.id_role)
            .outerjoin(Profile, Profile.id == User.id)
            .where(User.id_parent == manager_user_id)
            .order_by(User.id_role.asc(), User.id.asc())
        )
        if not include_inactive:
            stmt = stmt.where(User.status == "active")
        result = await self._session.execute(stmt)
        return list(result.all())

    async def list_users_with_profiles(self, role_id: int | None = None) -> list[tuple[User, Profile | None]]:
        stmt = (
            select(User, Profile)
            .options(with_expression(User.tg_user_id, _telegram_id_expr()))
            .outerjoin(Profile, Profile.id == User.id)
            .order_by(User.id)
        )
        if role_id is not None:
            stmt = stmt.where(User.id_role == role_id)
        result = await self._session.execute(stmt)
        return list(result.all())

    async def list_contractors(
        self,
        contractor_role_id: int,
    ) -> list[tuple[User, Profile | None, CompanyContact | None, TgUser | None]]:
        telegram_account = aliased(UserAuthAccount)
        telegram_channel = aliased(UserContactChannel)
        stmt = (
            select(
                User,
                Profile,
                CompanyContact,
                telegram_account.is_active,
                telegram_channel.is_verified,
                telegram_channel.is_active,
            )
            .options(
                with_expression(
                    User.tg_user_id,
                    cast(telegram_account.external_subject_id, BigInteger),
                )
            )
            .outerjoin(Profile, Profile.id == User.id)
            .outerjoin(CompanyContact, CompanyContact.id == User.id)
            .outerjoin(
                telegram_account,
                and_(
                    telegram_account.id_user == User.id,
                    telegram_account.provider == "telegram",
                ),
            )
            .outerjoin(
                telegram_channel,
                and_(
                    telegram_channel.id_user == User.id,
                    telegram_channel.channel_type == "telegram",
                    telegram_channel.is_primary.is_(True),
                ),
            )
            .where(User.id_role == contractor_role_id)
            .order_by(User.id)
        )
        result = await self._session.execute(stmt)

        rows: list[tuple[User, Profile | None, CompanyContact | None, TgUser | None]] = []
        for user, profile, company_contact, account_is_active, channel_is_verified, channel_is_active in result.all():
            rows.append(
                (
                    user,
                    profile,
                    company_contact,
                    build_tg_user(
                        tg_id=user.tg_user_id,
                        account_is_active=account_is_active,
                        channel_is_verified=channel_is_verified,
                        channel_is_active=channel_is_active,
                    ),
                )
            )
        return rows

    async def list_by_role_ids_with_profiles_and_roles(
        self,
        *,
        role_ids: list[int],
    ) -> list[tuple[User, Profile | None, Role]]:
        stmt = (
            select(User, Profile, Role)
            .options(with_expression(User.tg_user_id, _telegram_id_expr()))
            .join(Role, Role.id == User.id_role)
            .outerjoin(Profile, Profile.id == User.id)
            .where(User.id_role.in_(role_ids))
            .order_by(User.id_role.asc(), User.id.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.all())

    async def list_by_ids_with_profiles_and_roles(
        self,
        *,
        user_ids: list[str],
    ) -> list[tuple[User, Profile | None, Role]]:
        if not user_ids:
            return []
        stmt = (
            select(User, Profile, Role)
            .options(with_expression(User.tg_user_id, _telegram_id_expr()))
            .join(Role, Role.id == User.id_role)
            .outerjoin(Profile, Profile.id == User.id)
            .where(User.id.in_(user_ids))
            .order_by(User.id_role.asc(), User.id.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.all())

    async def list_active_user_parent_pairs(self) -> list[tuple[str, str | None]]:
        stmt = (
            select(User.id, User.id_parent)
            .where(User.status == "active")
            .order_by(User.id.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.all())

    async def list_staff_with_profiles_and_roles_for_dashboard(
        self,
        *,
        role_ids: list[int],
    ) -> list[tuple[User, Profile | None, Role]]:
        stmt = (
            select(User, Profile, Role)
            .options(with_expression(User.tg_user_id, _telegram_id_expr()))
            .join(Role, Role.id == User.id_role)
            .outerjoin(Profile, Profile.id == User.id)
            .where(User.id_role.in_(role_ids), User.status == "active")
            .order_by(User.id_role.asc(), User.id.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.all())

    async def get_with_profile_and_company_contacts(
        self,
        *,
        user_id: str,
    ) -> tuple[User, Profile | None, CompanyContact | None] | None:
        stmt = (
            select(User, Profile, CompanyContact)
            .options(with_expression(User.tg_user_id, _telegram_id_expr()))
            .outerjoin(Profile, Profile.id == User.id)
            .outerjoin(CompanyContact, CompanyContact.id == User.id)
            .where(User.id == user_id)
        )
        result = await self._session.execute(stmt)
        row = result.one_or_none()
        if row is None:
            return None
        return row

    async def update_status(self, user: User, status: str) -> None:
        user.status = status

    async def update_role(self, user: User, role_id: int) -> None:
        user.id_role = role_id

    async def update_parent(self, user: User, parent_user_id: str | None) -> None:
        user.id_parent = parent_user_id

    async def reassign_user_id(self, *, old_user_id: str, new_user_id: str) -> None:
        await self._session.execute(
            update(Profile).where(Profile.id == old_user_id).values(id=new_user_id)
        )
        await self._session.execute(
            update(CompanyContact).where(CompanyContact.id == old_user_id).values(id=new_user_id)
        )
        await self._session.execute(
            update(UserAuthAccount).where(UserAuthAccount.id_user == old_user_id).values(id_user=new_user_id)
        )
        await self._session.execute(
            update(UserContactChannel).where(UserContactChannel.id_user == old_user_id).values(id_user=new_user_id)
        )
        await self._session.execute(
            update(Request).where(Request.id_user == old_user_id).values(id_user=new_user_id)
        )
        await self._session.execute(
            update(RequestHiddenContractor)
            .where(RequestHiddenContractor.contractor_user_id == old_user_id)
            .values(contractor_user_id=new_user_id)
        )
        await self._session.execute(
            update(Offer).where(Offer.id_user == old_user_id).values(id_user=new_user_id)
        )
        await self._session.execute(
            update(Message).where(Message.id_user == old_user_id).values(id_user=new_user_id)
        )
        await self._session.execute(
            update(ChatParticipant).where(ChatParticipant.id_user == old_user_id).values(id_user=new_user_id)
        )
        await self._session.execute(
            update(MessageReceipt).where(MessageReceipt.id_user == old_user_id).values(id_user=new_user_id)
        )
        await self._session.execute(
            update(UserStatusPeriod).where(UserStatusPeriod.id_user == old_user_id).values(id_user=new_user_id)
        )
        await self._session.execute(
            update(EconomyPlan).where(EconomyPlan.id_user == old_user_id).values(id_user=new_user_id)
        )
        await self._session.execute(
            update(EconomyPlan)
            .where(EconomyPlan.id_parent_user_snapshot == old_user_id)
            .values(id_parent_user_snapshot=new_user_id)
        )
        await self._session.execute(
            update(User).where(User.id_parent == old_user_id).values(id_parent=new_user_id)
        )

    async def get_active_approved_contractor_tg_id(self, *, user_id: str, contractor_role_id: int) -> int | None:
        stmt = (
            select(cast(UserAuthAccount.external_subject_id, BigInteger))
            .join(User, User.id == UserAuthAccount.id_user)
            .join(
                UserContactChannel,
                and_(
                    UserContactChannel.id_user == User.id,
                    UserContactChannel.channel_type == "telegram",
                    UserContactChannel.channel_value == UserAuthAccount.external_subject_id,
                    UserContactChannel.is_active.is_(True),
                    UserContactChannel.is_verified.is_(True),
                ),
            )
            .where(User.id == user_id)
            .where(User.id_role == contractor_role_id)
            .where(User.status == "active")
            .where(UserAuthAccount.provider == "telegram")
            .where(UserAuthAccount.is_active.is_(True))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active_approved_contractor_tg_ids(
        self,
        *,
        contractor_role_id: int,
        exclude_user_ids: list[str] | None = None,
    ) -> list[int]:
        stmt = (
            select(cast(UserAuthAccount.external_subject_id, BigInteger))
            .join(User, User.id == UserAuthAccount.id_user)
            .join(
                UserContactChannel,
                and_(
                    UserContactChannel.id_user == User.id,
                    UserContactChannel.channel_type == "telegram",
                    UserContactChannel.channel_value == UserAuthAccount.external_subject_id,
                    UserContactChannel.is_active.is_(True),
                    UserContactChannel.is_verified.is_(True),
                ),
            )
            .where(User.id_role == contractor_role_id)
            .where(User.status == "active")
            .where(UserAuthAccount.provider == "telegram")
            .where(UserAuthAccount.is_active.is_(True))
            .order_by(User.id.asc())
        )
        if exclude_user_ids:
            stmt = stmt.where(User.id.not_in(exclude_user_ids))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_active_tg_user_ids(self) -> list[int]:
        stmt = (
            select(cast(UserAuthAccount.external_subject_id, BigInteger))
            .join(User, User.id == UserAuthAccount.id_user)
            .join(
                UserContactChannel,
                and_(
                    UserContactChannel.id_user == User.id,
                    UserContactChannel.channel_type == "telegram",
                    UserContactChannel.channel_value == UserAuthAccount.external_subject_id,
                    UserContactChannel.is_active.is_(True),
                ),
            )
            .where(User.status == "active")
            .where(UserAuthAccount.provider == "telegram")
            .where(UserAuthAccount.is_active.is_(True))
            .order_by(User.id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
