from __future__ import annotations

from dataclasses import dataclass, replace

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.exceptions import Conflict, NotFound
from app.domain.policies import UserPolicy
from app.repositories.profiles import ProfileRepository
from app.repositories.units import UnitRepository
from app.repositories.users import UserRepository
from app.services.contractor_units import ContractorRootUnitBindingsState, ContractorUnitService
from app.services.users import UserStatusService, UserStatusUpdateResult


@dataclass(frozen=True, slots=True)
class ContractorListItemResult:
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
    updated_at: str | None
    is_manual: bool
    email_verified: bool = False
    root_unit_bindings: ContractorRootUnitBindingsState | None = None


@dataclass(frozen=True, slots=True)
class ContractorListResult:
    items: list[ContractorListItemResult]
    total: int
    limit: int
    offset: int

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
        units: UnitRepository | None = None,
    ) -> None:
        self._users = users
        self._profiles = profiles
        self._units = units

    async def list_contractors(
        self,
        *,
        current_user: CurrentUser,
        search: str | None = None,
        status: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 25,
        offset: int = 0,
    ) -> ContractorListResult:
        UserPolicy.ensure_can_list_contractors(current_user)

        rows, total = await self._users.list_contractors_page(
            contractor_role_id=settings.contractor_role_id,
            search=search,
            status=status,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )
        items = [
            ContractorListItemResult(
                user_id=user.id,
                role_id=user.id_role,
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
                created_at=str(user.created_at) if user.created_at is not None else None,
                updated_at=str(user.updated_at) if user.updated_at is not None else None,
                is_manual=legacy_user is None and legacy_account_id is None,
            )
            for user, profile, company, legacy_user, legacy_account_id in rows
        ]
        if self._units is not None:
            items = [
                item
                for item in items
                if await self._contractor_unit_service().can_access_contractor(
                    current_user=current_user,
                    contractor_user_id=item.user_id,
                )
            ]
        if self._units is not None and items:
            bindings_by_user = await self._contractor_unit_service().list_bindings_for_users(
                current_user=current_user,
                contractor_user_ids=[item.user_id for item in items],
            )
            if bindings_by_user:
                items = [
                    replace(item, root_unit_bindings=bindings_by_user.get(item.user_id))
                    for item in items
                ]
        if items:
            verified_by_user_id = await self._users.map_primary_email_verified(
                user_ids=[item.user_id for item in items],
            )
            items = [
                replace(item, email_verified=verified_by_user_id.get(item.user_id, False))
                for item in items
            ]
        return ContractorListResult(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )

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

        if self._units is not None:
            await self._contractor_unit_service().ensure_can_access_contractor(
                current_user=current_user,
                contractor_user_id=contractor_id,
            )

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
        UserPolicy.ensure_can_update_contractor_profile_status(current_user)
        if self._units is not None:
            await self._contractor_unit_service().ensure_can_access_contractor(
                current_user=current_user,
                contractor_user_id=contractor_id,
            )
        return await status_service.update_statuses(
            current_user=current_user,
            user_id=contractor_id,
            user_status=user_status,
            contractor_only=True,
        )

    def _contractor_unit_service(self) -> ContractorUnitService:
        if self._units is None:
            raise RuntimeError("Contractor unit service requires unit repository")
        return ContractorUnitService(users=self._users, units=self._units)

    async def get_contractor_root_unit_bindings(
        self,
        *,
        current_user: CurrentUser,
        contractor_id: str,
    ) -> ContractorRootUnitBindingsState:
        return await self._contractor_unit_service().list_bindings(
            current_user=current_user,
            contractor_user_id=contractor_id,
        )

    async def update_contractor_root_unit_bindings(
        self,
        *,
        current_user: CurrentUser,
        contractor_id: str,
        root_unit_ids: set[int],
    ) -> ContractorRootUnitBindingsState:
        return await self._contractor_unit_service().update_bindings(
            current_user=current_user,
            contractor_user_id=contractor_id,
            root_unit_ids=root_unit_ids,
        )
