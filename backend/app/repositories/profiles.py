from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import BigInteger, and_, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth_models import UserAuthAccount
from app.models.orm_models import CompanyContact, Profile, User

_INVALID_NOTIFICATION_EMAILS = frozenset({"не указано", "none", "null"})


@dataclass(frozen=True, slots=True)
class ActiveContractorEmailRecipient:
    user_id: str
    email: str
    tg_id: int | None


class ProfileRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, profile: Profile) -> None:
        self._session.add(profile)

    async def get_by_id(self, user_id: str) -> Profile | None:
        result = await self._session.execute(select(Profile).where(Profile.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_ids(self, user_ids: list[str]) -> list[Profile]:
        if not user_ids:
            return []
        result = await self._session.execute(select(Profile).where(Profile.id.in_(user_ids)))
        return list(result.scalars().all())

    async def update_mail_after_verification(self, user_id: str, email: str) -> bool:
        profile = await self.get_by_id(user_id)
        if profile is None:
            return False

        candidate = email.strip()
        if profile.mail and profile.mail.strip().lower() == candidate.lower():
            return True

        profile.mail = candidate
        return True

    async def list_active_contractor_emails(self, *, contractor_role_id: int) -> list[str]:
        stmt = (
            select(Profile.mail)
            .join(User, User.id == Profile.id)
            .join(
                UserAuthAccount,
                and_(
                    UserAuthAccount.id_user == User.id,
                    UserAuthAccount.provider == "keycloak",
                    UserAuthAccount.is_active.is_(True),
                ),
            )
            .where(User.id_role == contractor_role_id)
            .where(User.status == "active")
            .order_by(User.id)
        )
        result = await self._session.execute(stmt)

        emails: list[str] = []
        for mail in result.scalars().all():
            normalized_mail = (mail or "").strip()
            if not normalized_mail or normalized_mail.lower() in {"не указано", "none", "null"}:
                continue
            emails.append(normalized_mail)
        return list(dict.fromkeys(emails))

    async def list_active_contractors(self, *, contractor_role_id: int) -> list[Profile]:
        stmt = (
            select(Profile)
            .join(User, User.id == Profile.id)
            .join(
                UserAuthAccount,
                and_(
                    UserAuthAccount.id_user == User.id,
                    UserAuthAccount.provider == "keycloak",
                    UserAuthAccount.is_active.is_(True),
                ),
            )
            .where(User.id_role == contractor_role_id)
            .where(User.status == "active")
            .order_by(User.id)
        )
        result = await self._session.execute(stmt)

        profiles: list[Profile] = []
        for profile in result.scalars().all():
            normalized_mail = (profile.mail or "").strip()
            if not normalized_mail or normalized_mail.lower() in {"не указано", "none", "null"}:
                continue
            profiles.append(profile)
        return profiles

    async def list_active_contractor_email_recipients(
        self,
        *,
        contractor_role_id: int,
    ) -> list[ActiveContractorEmailRecipient]:
        stmt = (
            select(User.id, cast(None, BigInteger), Profile.mail)
            .join(Profile, Profile.id == User.id)
            .join(
                UserAuthAccount,
                and_(
                    UserAuthAccount.id_user == User.id,
                    UserAuthAccount.provider == "keycloak",
                    UserAuthAccount.is_active.is_(True),
                ),
            )
            .where(User.id_role == contractor_role_id)
            .where(User.status == "active")
            .order_by(User.id)
        )
        result = await self._session.execute(stmt)

        recipients: list[ActiveContractorEmailRecipient] = []
        for user_id, tg_id, mail in result.all():
            normalized_mail = (mail or "").strip()
            if not normalized_mail or normalized_mail.lower() in {"не указано", "none", "null"}:
                continue
            recipients.append(
                ActiveContractorEmailRecipient(
                    user_id=user_id,
                    email=normalized_mail,
                    tg_id=tg_id,
                )
            )
        return recipients

    async def find_contractor_user_id_by_notification_email(
        self,
        *,
        email: str,
        contractor_role_id: int,
    ) -> str | None:
        normalized_email = email.strip().lower()
        if not normalized_email or normalized_email in _INVALID_NOTIFICATION_EMAILS:
            return None

        stmt = (
            select(User.id)
            .outerjoin(Profile, Profile.id == User.id)
            .outerjoin(CompanyContact, CompanyContact.id == User.id)
            .join(
                UserAuthAccount,
                and_(
                    UserAuthAccount.id_user == User.id,
                    UserAuthAccount.provider == "keycloak",
                ),
            )
            .where(User.id_role == contractor_role_id)
            .where(
                or_(
                    func.lower(Profile.mail) == normalized_email,
                    func.lower(CompanyContact.mail) == normalized_email,
                )
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_contractor_by_mail(self, *, email: str, contractor_role_id: int) -> Profile | None:
        normalized_email = email.strip().lower()
        if not normalized_email:
            return None

        stmt = (
            select(Profile)
            .join(User, User.id == Profile.id)
            .where(User.id_role == contractor_role_id, User.status == "active")
            .where(Profile.mail.ilike(normalized_email))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_by_mail(self, *, email: str, exclude_user_id: str | None = None) -> bool:
        normalized_email = email.strip().lower()
        if not normalized_email:
            return False

        stmt = select(Profile.id).where(Profile.mail.ilike(normalized_email))
        if exclude_user_id:
            stmt = stmt.where(Profile.id != exclude_user_id)
        result = await self._session.execute(stmt.limit(1))
        return result.scalar_one_or_none() is not None
