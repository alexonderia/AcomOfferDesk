from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.exceptions import Conflict, NotFound
from app.domain.policies import UserPolicy
from app.repositories.profiles import ProfileRepository
from app.repositories.users import UserRepository
from app.services.users import UserListItem, UserStatusService, UserStatusUpdateResult

@dataclass(frozen=True, slots=True)
class ContractorProfileResult:
    user_id: str
    role_id: int
    status: str
    full_name: str | None
    phone: str | None
    mail: str | None
    company_name: str | None
    inn: str | None
    company_phone: str | None
    company_mail: str | None
    address: str | None
    note: str | None
    created_at: str | None


class ContractorService:
    def __init__(
        self,
        users: UserRepository,
        profiles: ProfileRepository,
    ) -> None:
        self._users = users
        self._profiles = profiles

    async def list_contractors(self, *, current_user: CurrentUser) -> list[UserListItem]:
        UserPolicy.ensure_can_list_contractors(current_user)

        rows = await self._users.list_contractors(contractor_role_id=settings.contractor_role_id)
        return [
            UserListItem(
                user_id=user.id,
                role_id=user.id_role,
                id_parent=user.id_parent,
                status=user.status,
                full_name=profile.full_name if profile else None,
                phone=profile.phone if profile else None,
                mail=profile.mail if profile else None,
                company_name=company.company_name if company else None,
                inn=company.inn if company else None,
                company_phone=company.phone if company else None,
                company_mail=company.mail if company else None,
                address=company.address if company else None,
                note=company.note if company else None,
            )
            for user, profile, company, _tg_user in rows
        ]

    async def get_contractor(
        self,
        *,
        current_user: CurrentUser,
        contractor_id: str,
    ) -> ContractorProfileResult:
        UserPolicy.ensure_can_read_contractor_profile(current_user)
        row = await self._users.get_with_profile_and_company_contacts(user_id=contractor_id)
        if row is None:
            raise NotFound("Контрагент не найден")
        user, profile, company = row
        if user.id_role != settings.contractor_role_id:
            raise Conflict("Пользователь не является контрагентом")

        created_at = str(user.created_at) if user.created_at is not None else None
        return ContractorProfileResult(
            user_id=user.id,
            role_id=user.id_role,
            status=user.status,
            full_name=profile.full_name if profile is not None else None,
            phone=profile.phone if profile is not None else None,
            mail=profile.mail if profile is not None else None,
            company_name=company.company_name if company is not None else None,
            inn=company.inn if company is not None else None,
            company_phone=company.phone if company is not None else None,
            company_mail=company.mail if company is not None else None,
            address=company.address if company is not None else None,
            note=company.note if company is not None else None,
            created_at=created_at,
        )

    async def update_contractor_status(
        self,
        *,
        current_user: CurrentUser,
        contractor_id: str,
        user_status: str,
        status_service: UserStatusService,
    ) -> UserStatusUpdateResult:
        return await status_service.update_statuses(
            current_user=current_user,
            user_id=contractor_id,
            user_status=user_status,
            tg_status=None,
            contractor_only=True,
        )
