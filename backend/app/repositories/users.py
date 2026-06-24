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
    Unit,
    UnitMember,
    User,
    UserStatusPeriod,
)
from app.repositories.max_compat import max_subject_value
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

    def _build_contractors_stmt(
        self,
        *,
        contractor_role_id: int,
    ):
        telegram_account = aliased(UserAuthAccount)
        telegram_channel = aliased(UserContactChannel)
        max_account = aliased(UserAuthAccount)
        max_channel = aliased(UserContactChannel)
        stmt = (
            select(
                User,
                Profile,
                CompanyContact,
                telegram_account.is_active,
                telegram_channel.is_verified,
                telegram_channel.is_active,
                max_account.external_subject_id,
                max_channel.channel_value,
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
            .outerjoin(
                max_account,
                and_(
                    max_account.id_user == User.id,
                    max_account.provider == "max",
                    max_account.is_active.is_(True),
                ),
            )
            .outerjoin(
                max_channel,
                and_(
                    max_channel.id_user == User.id,
                    max_channel.channel_type == "max",
                    max_channel.is_active.is_(True),
                    max_channel.is_primary.is_(True),
                ),
            )
            .where(User.id_role == contractor_role_id)
        )
        return stmt, max_account.external_subject_id, max_channel.channel_value

    def _apply_contractors_filters(
        self,
        stmt,
        *,
        search: str | None,
        status: str | None,
        max_subject_column=None,
        max_channel_column=None,
    ):
        normalized_search = (search or "").strip().lower()
        if normalized_search:
            like_value = f"%{normalized_search}%"
            search_clauses = [
                func.lower(User.id).like(like_value),
                func.lower(func.coalesce(Profile.full_name, "")).like(like_value),
                func.lower(func.coalesce(Profile.phone, "")).like(like_value),
                func.lower(func.coalesce(Profile.mail, "")).like(like_value),
                func.lower(func.coalesce(CompanyContact.company_name, "")).like(like_value),
                func.lower(func.coalesce(CompanyContact.inn, "")).like(like_value),
                func.lower(func.coalesce(CompanyContact.phone, "")).like(like_value),
                func.lower(func.coalesce(CompanyContact.mail, "")).like(like_value),
            ]
            if max_subject_column is not None:
                search_clauses.append(
                    func.lower(func.coalesce(max_subject_column, "")).like(like_value)
                )
            if max_channel_column is not None:
                search_clauses.append(
                    func.lower(func.coalesce(max_channel_column, "")).like(like_value)
                )
            stmt = stmt.where(
                or_(*search_clauses)
            )
        normalized_status = (status or "").strip().lower()
        if normalized_status:
            stmt = stmt.where(User.status == normalized_status)
        return stmt

    @staticmethod
    def _map_contractor_rows(
        result_rows,
    ) -> list[tuple[User, Profile | None, CompanyContact | None, TgUser | None, str | None]]:
        rows: list[tuple[User, Profile | None, CompanyContact | None, TgUser | None, str | None]] = []
        for (
            user,
            profile,
            company_contact,
            account_is_active,
            channel_is_verified,
            channel_is_active,
            max_subject_id,
            max_channel_value,
        ) in result_rows:
            linked_max_user_id: str | None = None
            for candidate in (max_subject_id, max_channel_value):
                if candidate is None:
                    continue
                normalized_candidate = str(candidate).strip()
                if normalized_candidate:
                    linked_max_user_id = normalized_candidate
                    break
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
                    linked_max_user_id,
                )
            )
        return rows

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

    async def get_linked_max_user_id(self, user_id: str) -> str | None:
        stmt = (
            select(UserAuthAccount.external_subject_id)
            .where(
                UserAuthAccount.id_user == user_id,
                UserAuthAccount.provider == "max",
            )
            .order_by(UserAuthAccount.is_active.desc(), UserAuthAccount.id.asc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        value = result.scalar_one_or_none()
        if value is not None:
            normalized = str(value).strip()
            if normalized:
                return normalized

        channel_stmt = (
            select(UserContactChannel.channel_value)
            .where(
                UserContactChannel.id_user == user_id,
                UserContactChannel.channel_type == "max",
                UserContactChannel.is_active.is_(True),
            )
            .order_by(UserContactChannel.is_primary.desc(), UserContactChannel.id.asc())
            .limit(1)
        )
        channel_result = await self._session.execute(channel_stmt)
        channel_value = channel_result.scalar_one_or_none()
        if channel_value is None:
            return None
        normalized_channel = str(channel_value).strip()
        return normalized_channel or None

    async def get_by_max_user_id(self, max_user_id: int | str) -> User | None:
        subject = max_subject_value(max_user_id)
        account_stmt = (
            select(User)
            .join(
                UserAuthAccount,
                and_(
                    UserAuthAccount.id_user == User.id,
                    UserAuthAccount.provider == "max",
                    UserAuthAccount.external_subject_id == subject,
                ),
            )
            .order_by(UserAuthAccount.is_active.desc(), UserAuthAccount.id.asc())
            .limit(1)
        )
        account_result = await self._session.execute(account_stmt)
        linked_user = account_result.scalar_one_or_none()
        if linked_user is not None:
            return linked_user

        channel_stmt = (
            select(User)
            .join(
                UserContactChannel,
                and_(
                    UserContactChannel.id_user == User.id,
                    UserContactChannel.channel_type == "max",
                    UserContactChannel.channel_value == subject,
                    UserContactChannel.is_active.is_(True),
                ),
            )
            .order_by(UserContactChannel.is_primary.desc(), UserContactChannel.id.asc())
            .limit(1)
        )
        channel_result = await self._session.execute(channel_stmt)
        return channel_result.scalar_one_or_none()

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
    ) -> list[tuple[User, Profile | None, CompanyContact | None, TgUser | None, str | None]]:
        stmt, _, _ = self._build_contractors_stmt(contractor_role_id=contractor_role_id)
        stmt = stmt.order_by(User.id)
        result = await self._session.execute(stmt)
        return self._map_contractor_rows(result.all())

    async def list_contractors_page(
        self,
        *,
        contractor_role_id: int,
        search: str | None = None,
        status: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[tuple[User, Profile | None, CompanyContact | None, TgUser | None, str | None]], int]:
        stmt, max_subject_column, max_channel_column = self._build_contractors_stmt(
            contractor_role_id=contractor_role_id
        )
        stmt = self._apply_contractors_filters(
            stmt,
            search=search,
            status=status,
            max_subject_column=max_subject_column,
            max_channel_column=max_channel_column,
        )

        sort_columns = {
            "user_id": User.id,
            "max_user_id": func.coalesce(max_subject_column, max_channel_column),
            "status": User.status,
            "full_name": Profile.full_name,
            "phone": Profile.phone,
            "mail": Profile.mail,
            "company_name": CompanyContact.company_name,
            "inn": CompanyContact.inn,
            "company_phone": CompanyContact.phone,
            "company_mail": CompanyContact.mail,
            "address": CompanyContact.address,
            "created_at": User.created_at,
            "updated_at": User.updated_at,
        }
        sort_column = sort_columns.get(sort_by, User.created_at)
        if (sort_order or "").lower() == "asc":
            stmt = stmt.order_by(sort_column.asc(), User.id.asc())
        else:
            stmt = stmt.order_by(sort_column.desc(), User.id.asc())
        stmt = stmt.limit(limit).offset(offset)

        count_max_account = aliased(UserAuthAccount)
        count_max_channel = aliased(UserContactChannel)
        count_stmt = (
            select(func.count(func.distinct(User.id)))
            .select_from(User)
            .outerjoin(Profile, Profile.id == User.id)
            .outerjoin(CompanyContact, CompanyContact.id == User.id)
            .outerjoin(
                count_max_account,
                and_(
                    count_max_account.id_user == User.id,
                    count_max_account.provider == "max",
                    count_max_account.is_active.is_(True),
                ),
            )
            .outerjoin(
                count_max_channel,
                and_(
                    count_max_channel.id_user == User.id,
                    count_max_channel.channel_type == "max",
                    count_max_channel.is_active.is_(True),
                    count_max_channel.is_primary.is_(True),
                ),
            )
            .where(User.id_role == contractor_role_id)
        )
        count_stmt = self._apply_contractors_filters(
            count_stmt,
            search=search,
            status=status,
            max_subject_column=count_max_account.external_subject_id,
            max_channel_column=count_max_channel.channel_value,
        )

        total_result = await self._session.execute(count_stmt)
        rows_result = await self._session.execute(stmt)
        return self._map_contractor_rows(rows_result.all()), int(total_result.scalar_one() or 0)

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

    async def list_active_units(self) -> list[tuple[int, int | None]]:
        """Active units as (unit_id, parent_unit_id) pairs for org-scope resolution."""
        stmt = select(Unit.id, Unit.id_parent).where(Unit.is_active.is_(True))
        result = await self._session.execute(stmt)
        return [
            (int(unit_id), int(parent_id) if parent_id is not None else None)
            for unit_id, parent_id in result.all()
        ]

    async def list_active_unit_memberships(self) -> list[tuple[str, int]]:
        """Active unit memberships (in active units) as (user_id, unit_id) pairs."""
        stmt = (
            select(UnitMember.id_user, UnitMember.id_unit)
            .join(Unit, Unit.id == UnitMember.id_unit)
            .where(UnitMember.is_active.is_(True), Unit.is_active.is_(True))
        )
        result = await self._session.execute(stmt)
        return [(str(user_id), int(unit_id)) for user_id, unit_id in result.all()]

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

    async def get_active_approved_contractor_max_id(self, *, user_id: str, contractor_role_id: int) -> str | None:
        stmt = (
            select(UserAuthAccount.external_subject_id)
            .join(User, User.id == UserAuthAccount.id_user)
            .join(
                UserContactChannel,
                and_(
                    UserContactChannel.id_user == User.id,
                    UserContactChannel.channel_type == "max",
                    UserContactChannel.channel_value == UserAuthAccount.external_subject_id,
                    UserContactChannel.is_active.is_(True),
                    UserContactChannel.is_verified.is_(True),
                ),
            )
            .where(User.id == user_id)
            .where(User.id_role == contractor_role_id)
            .where(User.status == "active")
            .where(UserAuthAccount.provider == "max")
            .where(UserAuthAccount.is_active.is_(True))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        value = result.scalar_one_or_none()
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    async def list_active_approved_contractor_max_ids(
        self,
        *,
        contractor_role_id: int,
        exclude_user_ids: list[str] | None = None,
    ) -> list[str]:
        stmt = (
            select(UserAuthAccount.external_subject_id)
            .join(User, User.id == UserAuthAccount.id_user)
            .join(
                UserContactChannel,
                and_(
                    UserContactChannel.id_user == User.id,
                    UserContactChannel.channel_type == "max",
                    UserContactChannel.channel_value == UserAuthAccount.external_subject_id,
                    UserContactChannel.is_active.is_(True),
                    UserContactChannel.is_verified.is_(True),
                ),
            )
            .where(User.id_role == contractor_role_id)
            .where(User.status == "active")
            .where(UserAuthAccount.provider == "max")
            .where(UserAuthAccount.is_active.is_(True))
            .order_by(User.id.asc())
        )
        if exclude_user_ids:
            stmt = stmt.where(User.id.not_in(exclude_user_ids))
        result = await self._session.execute(stmt)
        return [str(value).strip() for value in result.scalars().all() if str(value).strip()]

    async def list_active_approved_contractor_max_recipients(
        self,
        *,
        contractor_role_id: int,
        exclude_user_ids: list[str] | None = None,
    ) -> list[tuple[str, str]]:
        stmt = (
            select(User.id, UserAuthAccount.external_subject_id)
            .join(User, User.id == UserAuthAccount.id_user)
            .join(
                UserContactChannel,
                and_(
                    UserContactChannel.id_user == User.id,
                    UserContactChannel.channel_type == "max",
                    UserContactChannel.channel_value == UserAuthAccount.external_subject_id,
                    UserContactChannel.is_active.is_(True),
                    UserContactChannel.is_verified.is_(True),
                ),
            )
            .where(User.id_role == contractor_role_id)
            .where(User.status == "active")
            .where(UserAuthAccount.provider == "max")
            .where(UserAuthAccount.is_active.is_(True))
            .order_by(User.id.asc())
        )
        if exclude_user_ids:
            stmt = stmt.where(User.id.not_in(exclude_user_ids))
        result = await self._session.execute(stmt)

        recipients: list[tuple[str, str]] = []
        for user_id, value in result.all():
            normalized = str(value).strip()
            if not normalized:
                continue
            recipients.append((user_id, normalized))
        return recipients

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
