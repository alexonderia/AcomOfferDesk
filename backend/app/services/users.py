from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.core.config import settings
from app.domain.contractor_validation import validate_inn, validate_optional_email, validate_ru_phone
from app.domain.exceptions import Conflict, Forbidden, NotFound
from app.models.auth_models import UserAuthAccount, UserContactChannel
from app.domain.policies import CurrentUser, UserPolicy
from app.models.orm_models import CompanyContact, Profile, Role, TgUser, User, UserStatusPeriod
from app.repositories.company_contacts import CompanyContactRepository
from app.repositories.profiles import ProfileRepository
from app.repositories.user_auth_accounts import UserAuthAccountRepository
from app.repositories.user_contact_channels import UserContactChannelRepository
from app.repositories.tg_users import TgUserRepository
from app.repositories.telegram_compat import telegram_subject_value
from app.repositories.user_status_periods import UserStatusPeriodRepository
from app.repositories.users import UserRepository
from app.services.contractor_email_notifications import (
    notify_contractor_access_opened_email,
)
from app.services.keycloak_admin import KeycloakAdminService
from app.services.tg_notifications import (
    notify_access_closed as notify_tg_access_closed,
    notify_access_opened as notify_tg_access_opened,
)

ROLE_NAME_SUPERADMIN = "Суперадмин"
ROLE_NAME_ADMIN = "Администратор"
ROLE_NAME_PROJECT_MANAGER = "Руководитель проекта"
ROLE_NAME_LEAD_ECONOMIST = "Ведущий экономист"
ROLE_NAME_ECONOMIST = "Экономист"
ROLE_NAME_OPERATOR = "Оператор"
PLACEHOLDER_TEXT = "Не указано"
_LOGIN_CLEANUP_PATTERN = re.compile(r"[^a-z0-9_]+")
_LOGIN_COLLAPSE_PATTERN = re.compile(r"_+")
_CYRILLIC_TO_LATIN = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}

def _normalize_db_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


async def _is_descendant_user(
    users: UserRepository,
    *,
    ancestor_user_id: str,
    target_user_id: str,
) -> bool:
    cursor_id: str | None = target_user_id
    visited: set[str] = set()

    while cursor_id is not None and cursor_id not in visited:
        visited.add(cursor_id)
        if cursor_id == ancestor_user_id:
            return True
        cursor_user = await users.get_by_id(cursor_id)
        if cursor_user is None:
            return False
        cursor_id = cursor_user.id_parent

    return False


def _collect_descendant_user_ids(
    *,
    manager_user_id: str,
    rows: list[tuple[User, Profile | None, Role]],
) -> set[str]:
    by_id = {user.id: user for user, _, _ in rows}
    descendant_ids: set[str] = set()

    for user_id in by_id:
        cursor_id: str | None = user_id
        visited: set[str] = set()
        while cursor_id is not None and cursor_id not in visited:
            visited.add(cursor_id)
            if cursor_id == manager_user_id:
                descendant_ids.add(user_id)
                break
            cursor_user = by_id.get(cursor_id)
            cursor_id = cursor_user.id_parent if cursor_user is not None else None

    return descendant_ids


def _can_manage_subordinate_role(*, current_role_id: int, target_role_id: int) -> bool:
    if current_role_id == settings.project_manager_role_id:
        return target_role_id in {settings.lead_economist_role_id, settings.economist_role_id}
    if current_role_id in {settings.lead_economist_role_id, settings.economist_role_id}:
        return target_role_id == settings.economist_role_id
    return False


def _normalize_keycloak_email_value(value: str | None) -> str | None:
    normalized = (value or "").strip()
    if not normalized or normalized == PLACEHOLDER_TEXT:
        return None
    return normalized


def _normalize_notification_email(value: str | None) -> str | None:
    normalized = (value or "").strip()
    if not normalized:
        return None
    if normalized.lower() in {PLACEHOLDER_TEXT.lower(), "none", "null"}:
        return None
    return normalized


async def _bind_keycloak_account(
    *,
    user_auth_accounts: UserAuthAccountRepository,
    user_id: str,
    keycloak_subject_id: str,
    username: str,
    email: str | None,
) -> None:
    conflicting_subject = await user_auth_accounts.get_conflicting_subject(
        provider="keycloak",
        subject=keycloak_subject_id,
        exclude_user_id=user_id,
    )
    if conflicting_subject is not None:
        raise Conflict("Keycloak account is already linked to another local user")

    existing_binding = await user_auth_accounts.get_by_user_provider(
        user_id=user_id,
        provider="keycloak",
        include_inactive=True,
    )
    if existing_binding is None:
        await user_auth_accounts.add(
            UserAuthAccount(
                id_user=user_id,
                provider="keycloak",
                external_subject_id=keycloak_subject_id,
                external_username=username,
                external_email=email,
                is_active=True,
            )
        )
        return

    existing_binding.external_subject_id = keycloak_subject_id
    existing_binding.external_username = username
    existing_binding.external_email = email
    existing_binding.is_active = True

class UserRegistrationService:
    def __init__(
        self,
        users: UserRepository,
        profiles: ProfileRepository,
        user_auth_accounts: UserAuthAccountRepository,
        *,
        keycloak_admin: KeycloakAdminService | None = None,
    ):
        self._users = users
        self._profiles = profiles
        self._user_auth_accounts = user_auth_accounts
        self._keycloak_admin = keycloak_admin or KeycloakAdminService()

    async def register_user(
        self,
        current_user: CurrentUser,
        *,
        user_id: str,
        password: str | None,
        role_id: int,
        id_parent: str | None,
        full_name: str | None,
        phone: str | None,
        mail: str | None,
    ) -> User:
        UserPolicy.ensure_can_register_user(current_user)
        target_role = await self._users.get_role_by_id(role_id)
        if target_role is None:
            raise Conflict("Role is not allowed for creation")
        if current_user.role_id == settings.superadmin_role_id and role_id == settings.superadmin_role_id:
            raise Forbidden("Superadmin cannot create superadmin users")
        if current_user.role_id == settings.lead_economist_role_id and role_id != settings.economist_role_id:
            raise Forbidden("Lead economist can create only economist users")
        current_role = await self._users.get_role_by_id(current_user.role_id)
        if current_role is None:
            raise Forbidden("Access denied")

        if current_role.role not in {
            ROLE_NAME_SUPERADMIN,
            ROLE_NAME_ADMIN,
            ROLE_NAME_LEAD_ECONOMIST,
        }:
            raise Forbidden("Access denied")

        if target_role.role == ROLE_NAME_SUPERADMIN:
            raise Forbidden("Superadmin cannot create superadmin users")

        if current_role.role == ROLE_NAME_ADMIN and target_role.role not in {
            ROLE_NAME_ECONOMIST,
            ROLE_NAME_OPERATOR,
        }:
            raise Forbidden("Admin can create only economist and operator users")

        if current_role.role == ROLE_NAME_LEAD_ECONOMIST and target_role.role != ROLE_NAME_ECONOMIST:
            raise Forbidden("Lead economist can create only economist users")
        if target_role.role == ROLE_NAME_ECONOMIST:
            if id_parent is None:
                raise Conflict("Economist user must have an economist or lead economist manager")
            parent_user = await self._users.get_by_id(id_parent)
            if parent_user is None:
                raise NotFound("Parent user not found")
            parent_role = await self._users.get_role_by_id(parent_user.id_role)
            if parent_role is None or parent_role.role not in {ROLE_NAME_ECONOMIST, ROLE_NAME_LEAD_ECONOMIST}:
                raise Conflict("Economist user can have only economist or lead economist manager")
            if current_user.role_id == settings.lead_economist_role_id:
                rows = await self._users.list_by_role_ids_with_profiles_and_roles(
                    role_ids=[settings.lead_economist_role_id, settings.economist_role_id],
                )
                descendant_ids = _collect_descendant_user_ids(
                    manager_user_id=current_user.user_id,
                    rows=rows,
                )
                allowed_parent_ids = {current_user.user_id} | {
                    user.id
                    for user, _, _ in rows
                    if user.id in descendant_ids and user.id_role == settings.economist_role_id
                }
                if id_parent not in allowed_parent_ids:
                    raise Forbidden("Economist manager must belong to current user's responsibility")
        elif target_role.role == ROLE_NAME_LEAD_ECONOMIST:
            if id_parent is None:
                raise Conflict("Lead economist user must have a project manager")
            parent_user = await self._users.get_by_id(id_parent)
            if parent_user is None:
                raise NotFound("Parent user not found")
            parent_role = await self._users.get_role_by_id(parent_user.id_role)
            if parent_role is None or parent_user.id_role != settings.project_manager_role_id:
                raise Conflict("Lead economist user can have only project manager")
        else:
            id_parent = None
        if await self._users.exists(user_id):
            raise Conflict("User already exists")

        normalized_full_name = (full_name or "").strip() or PLACEHOLDER_TEXT
        normalized_phone = (phone or "").strip() or PLACEHOLDER_TEXT
        normalized_mail = (mail or "").strip()
        if not normalized_mail:
            raise Conflict("Email is required for user creation")
        try:
            normalized_mail = validate_optional_email(normalized_mail, allow_placeholder=False) or normalized_mail
        except ValueError as exc:
            raise Conflict(str(exc)) from exc
        
        user = User(
            id=user_id,
            id_role=role_id,
            id_parent=id_parent,
            status="active",
        )

        await self._users.add(user)
        await self._profiles.add(
            Profile(
                id=user_id,
                full_name=normalized_full_name,
                phone=normalized_phone,
                mail=normalized_mail,
            )
        )
        keycloak_user = await self._keycloak_admin.ensure_user(
            username=user_id,
            email=normalized_mail,
            email_verified=False,
        )
        await _bind_keycloak_account(
            user_auth_accounts=self._user_auth_accounts,
            user_id=user_id,
            keycloak_subject_id=keycloak_user.id,
            username=user_id,
            email=normalized_mail,
        )
        return user
    

class ContractorRegistrationService:
    def __init__(
        self,
        users: UserRepository,
        profiles: ProfileRepository,
        company_contacts: CompanyContactRepository,
        user_auth_accounts: UserAuthAccountRepository,
        user_contact_channels: UserContactChannelRepository,
    ) -> None:
        self._users = users
        self._profiles = profiles
        self._company_contacts = company_contacts
        self._user_auth_accounts = user_auth_accounts
        self._user_contact_channels = user_contact_channels

    async def register_contractor(
        self,
        *,
        tg_user_id: int,
        login: str,
        password: str,
        full_name: str,
        phone: str,
        company_name: str,
        inn: str,
        company_phone: str,
        company_mail: str,
        address: str,
        note: str,
    ) -> User:
        telegram_subject = telegram_subject_value(tg_user_id)
        if await self._users.exists(login):
            raise Conflict("User already exists")
        existing_by_tg = await self._users.get_by_tg_user_id(tg_user_id)
        if existing_by_tg is not None:
            raise Conflict("TG user already linked")

        user = User(
            id=login,
            id_role=settings.contractor_role_id,
            status="review",
        )
        profile = Profile(
            id=login,
            full_name=full_name,
            phone=phone,
            mail="Не указано",
        )
        company_contact = CompanyContact(
            id=login,
            company_name=company_name,
            inn=inn,
            phone=company_phone,
            mail=company_mail,
            address=address,
            note=note,
        )
        await self._users.add(user)
        await self._users.flush()
        await self._profiles.add(profile)
        await self._company_contacts.add(company_contact)
        await self._user_auth_accounts.add(
            UserAuthAccount(
                id_user=login,
                provider="telegram",
                external_subject_id=telegram_subject,
                external_username=None,
                external_email=None,
                is_active=True,
            )
        )
        await self._user_contact_channels.add(
            UserContactChannel(
                id_user=login,
                channel_type="telegram",
                channel_value=telegram_subject,
                is_verified=False,
                verified_at=None,
                is_primary=True,
                is_active=True,
            )
        )
        return user


@dataclass(frozen=True)
class UserListItem:
    user_id: str
    role_id: int
    id_parent: str | None
    status: str
    full_name: str | None
    phone: str | None
    mail: str | None
    tg_user_id: int | None = None
    tg_status: str | None = None
    company_name: str | None = None
    inn: str | None = None
    company_phone: str | None = None
    company_mail: str | None = None
    address: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class EconomistListItem:
    user_id: str
    status: str
    full_name: str | None
    phone: str | None
    mail: str | None


@dataclass(frozen=True)
class RequestEconomistListItem:
    user_id: str
    full_name: str | None
    role: str
    unavailable_period: UnavailabilityPeriodData | None = None


@dataclass(frozen=True)
class RequestContractorListItem:
    user_id: str
    full_name: str | None
    company_name: str | None
    mail: str | None
    company_mail: str | None


@dataclass(frozen=True)
class UserStatusUpdateResult:
    user_id: str
    user_status: str
    tg_user_id: int | None
    tg_status: str | None


@dataclass(frozen=True)
class UnavailabilityPeriodData:
    id: int
    status: str
    started_at: datetime
    ended_at: datetime


@dataclass(frozen=True)
class MeResult:
    user_id: str
    role_id: int
    status: str
    tg_user_id: int | None
    full_name: str | None
    phone: str | None
    mail: str | None
    company_name: str | None = None
    inn: str | None = None
    company_phone: str | None = None
    company_mail: str | None = None
    address: str | None = None
    note: str | None = None
    unavailable_period: UnavailabilityPeriodData | None = None
    unavailable_periods: list[UnavailabilityPeriodData] = field(default_factory=list)

@dataclass(frozen=True)
class SubordinateProfileResult:
    user_id: str
    role_id: int
    id_parent: str | None
    status: str
    full_name: str | None
    phone: str | None
    mail: str | None
    unavailable_period: UnavailabilityPeriodData | None = None
    unavailable_periods: list[UnavailabilityPeriodData] = field(default_factory=list)

class UserQueryService:
    def __init__(self, users: UserRepository, user_status_periods: UserStatusPeriodRepository):
        self._users = users
        self._user_status_periods = user_status_periods

    async def _is_descendant(self, *, manager_user_id: str, subordinate_user_id: str) -> bool:
        return await _is_descendant_user(
            self._users,
            ancestor_user_id=manager_user_id,
            target_user_id=subordinate_user_id,
        )

    async def _ensure_accessible_subordinate(
        self,
        *,
        current_user: CurrentUser,
        subordinate: User,
    ) -> None:
        if not _can_manage_subordinate_role(
            current_role_id=current_user.role_id,
            target_role_id=subordinate.id_role,
        ):
            raise Conflict("Subordinate profile is available only for permitted subordinate roles")

        if subordinate.id == current_user.user_id:
            raise Forbidden("You can manage subordinate data only for your subordinates")

        is_subordinate = await self._is_descendant(
            manager_user_id=current_user.user_id,
            subordinate_user_id=subordinate.id,
        )
        if not is_subordinate:
            raise Forbidden("You can manage subordinate data only for your subordinates")

    async def list_users(self, current_user: CurrentUser, role_id: int | None = None) -> list[UserListItem]:
        UserPolicy.ensure_can_list_users(current_user)

        if current_user.role_id in {
            settings.lead_economist_role_id,
            settings.project_manager_role_id,
            settings.economist_role_id,
        }:
            if role_id is not None and role_id != settings.economist_role_id:
                raise Forbidden("Project manager, lead economist and economist can view only economist users")
            role_id = settings.economist_role_id

        if current_user.role_id == settings.economist_role_id:
            rows = await self._users.list_by_role_ids_with_profiles_and_roles(
                role_ids=[settings.economist_role_id],
            )
            descendant_ids = _collect_descendant_user_ids(
                manager_user_id=current_user.user_id,
                rows=rows,
            )
            return [
                UserListItem(
                    user_id=user.id,
                    role_id=user.id_role,
                    id_parent=user.id_parent,
                    status=user.status,
                    full_name=profile.full_name if profile else None,
                    phone=profile.phone if profile else None,
                    mail=profile.mail if profile else None,
                )
                for user, profile, _ in rows
                if user.id in descendant_ids and user.id_role == settings.economist_role_id
            ]

        if current_user.role_id == settings.lead_economist_role_id:
            rows = await self._users.list_by_role_ids_with_profiles_and_roles(
                role_ids=[settings.lead_economist_role_id, settings.economist_role_id],
            )
            descendant_ids = _collect_descendant_user_ids(
                manager_user_id=current_user.user_id,
                rows=rows,
            )
            return [
                UserListItem(
                    user_id=user.id,
                    role_id=user.id_role,
                    id_parent=user.id_parent,
                    status=user.status,
                    full_name=profile.full_name if profile else None,
                    phone=profile.phone if profile else None,
                    mail=profile.mail if profile else None,
                )
                for user, profile, _ in rows
                if user.id in descendant_ids and user.id_role == settings.economist_role_id
            ]

        if current_user.role_id == settings.project_manager_role_id:
            rows = await self._users.list_by_role_ids_with_profiles_and_roles(
                role_ids=[settings.lead_economist_role_id, settings.economist_role_id],
            )
            descendant_ids = _collect_descendant_user_ids(
                manager_user_id=current_user.user_id,
                rows=rows,
            )
            return [
                UserListItem(
                    user_id=user.id,
                    role_id=user.id_role,
                    id_parent=user.id_parent,
                    status=user.status,
                    full_name=profile.full_name if profile else None,
                    phone=profile.phone if profile else None,
                    mail=profile.mail if profile else None,
                )
                for user, profile, _ in rows
                if user.id in descendant_ids
            ]

        if role_id == settings.contractor_role_id:
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
                    tg_user_id=user.tg_user_id,
                    tg_status=tg_user.status if tg_user else None,
                    company_name=company.company_name if company else None,
                    inn=company.inn if company else None,
                    company_phone=company.phone if company else None,
                    company_mail=company.mail if company else None,
                    address=company.address if company else None,
                    note=company.note if company else None,
                )
                for user, profile, company, tg_user in rows
            ]

        rows = await self._users.list_users_with_profiles(role_id=role_id)
        return [
            UserListItem(
                user_id=user.id,
                role_id=user.id_role,
                id_parent=user.id_parent,
                status=user.status,
                full_name=profile.full_name if profile else None,
                phone=profile.phone if profile else None,
                mail=profile.mail if profile else None,
            )
            for user, profile in rows
        ]

    async def list_manager_candidates(
        self,
        current_user: CurrentUser,
        *,
        target_role_id: int,
    ) -> list[UserListItem]:
        if not (
            UserPolicy.can_register_user(current_user)
            or UserPolicy.can_update_user_manager(current_user)
        ):
            raise Forbidden("Insufficient permissions to view manager candidates")

        if current_user.role_id == settings.lead_economist_role_id and target_role_id != settings.economist_role_id:
            raise Forbidden("Lead economist can manage only economist users")
        if current_user.role_id == settings.economist_role_id and target_role_id != settings.economist_role_id:
            raise Forbidden("Economist can manage only economist users")
        if current_user.role_id == settings.project_manager_role_id and target_role_id not in {
            settings.lead_economist_role_id,
            settings.economist_role_id,
        }:
            raise Forbidden("Project manager can manage only lead economist and economist users")

        if target_role_id == settings.economist_role_id:
            rows = await self._users.list_by_role_ids_with_profiles_and_roles(
                role_ids=[settings.lead_economist_role_id, settings.economist_role_id],
            )
            if current_user.role_id == settings.lead_economist_role_id:
                descendant_ids = _collect_descendant_user_ids(
                    manager_user_id=current_user.user_id,
                    rows=rows,
                )
                allowed_ids = {current_user.user_id} | {
                    user.id
                    for user, _, _ in rows
                    if user.id in descendant_ids and user.id_role == settings.economist_role_id
                }
                rows = [row for row in rows if row[0].id in allowed_ids]
            elif current_user.role_id == settings.project_manager_role_id:
                descendant_ids = _collect_descendant_user_ids(
                    manager_user_id=current_user.user_id,
                    rows=rows,
                )
                rows = [
                    row for row in rows
                    if row[0].id in descendant_ids
                ]
            elif current_user.role_id == settings.economist_role_id:
                descendant_ids = _collect_descendant_user_ids(
                    manager_user_id=current_user.user_id,
                    rows=rows,
                )
                allowed_ids = {current_user.user_id} | {
                    user.id
                    for user, _, _ in rows
                    if user.id in descendant_ids and user.id_role == settings.economist_role_id
                }
                cursor_id = current_user.user_id
                visited: set[str] = set()
                while cursor_id is not None and cursor_id not in visited:
                    visited.add(cursor_id)
                    cursor_user = await self._users.get_by_id(cursor_id)
                    if cursor_user is None:
                        break
                    if cursor_user.id_role in {settings.economist_role_id, settings.lead_economist_role_id}:
                        allowed_ids.add(cursor_user.id)
                    cursor_id = cursor_user.id_parent
                rows = [row for row in rows if row[0].id in allowed_ids]
            return [
                UserListItem(
                    user_id=user.id,
                    role_id=user.id_role,
                    id_parent=user.id_parent,
                    status=user.status,
                    full_name=profile.full_name if profile else None,
                    phone=profile.phone if profile else None,
                    mail=profile.mail if profile else None,
                )
                for user, profile, _ in rows
            ]

        if target_role_id == settings.lead_economist_role_id:
            if current_user.role_id not in {settings.superadmin_role_id, settings.project_manager_role_id}:
                raise Forbidden("Only superadmin and project manager can manage lead economist manager")
            rows = await self._users.list_users_with_profiles(role_id=settings.project_manager_role_id)
            return [
                UserListItem(
                    user_id=user.id,
                    role_id=user.id_role,
                    id_parent=user.id_parent,
                    status=user.status,
                    full_name=profile.full_name if profile else None,
                    phone=profile.phone if profile else None,
                    mail=profile.mail if profile else None,
                )
                for user, profile in rows
            ]

        return []
    
    async def list_economists(self, current_user: CurrentUser) -> list[EconomistListItem]:
        UserPolicy.ensure_can_list_users(current_user)

        rows = await self._users.list_users_with_profiles(role_id=settings.economist_role_id)
        return [
            EconomistListItem(
                user_id=user.id,
                status=user.status,
                full_name=profile.full_name if profile else None,
                phone=profile.phone if profile else None,
                mail=profile.mail if profile else None,
            )
            for user, profile in rows
        ]
    
    async def list_request_economists(self, current_user: CurrentUser) -> list[RequestEconomistListItem]:
        if not (
            current_user.role_id == settings.superadmin_role_id
            or current_user.role_id == settings.lead_economist_role_id
            or current_user.role_id == settings.project_manager_role_id
        ):
            raise Forbidden("Insufficient permissions to view request economists")

        rows = await self._users.list_by_role_ids_with_profiles_and_roles(
            role_ids=[settings.lead_economist_role_id, settings.economist_role_id],
        )
        if current_user.role_id in {
            settings.lead_economist_role_id,
            settings.project_manager_role_id,
        }:
            descendant_ids = _collect_descendant_user_ids(
                manager_user_id=current_user.user_id,
                rows=rows,
            )
            rows = [
                row for row in rows
                if row[0].id in descendant_ids
            ]

        user_ids = [user.id for user, _, _ in rows]
        active_unavailability_by_user = await self._user_status_periods.list_active_for_users(user_ids=user_ids)

        return [
            RequestEconomistListItem(
                user_id=user.id,
                full_name=profile.full_name if profile else None,
                role=role.role,
                unavailable_period=self._period_to_data(active_unavailability_by_user[user.id]) if user.id in active_unavailability_by_user else None,
            )
            for user, profile, role in rows
        ]

    async def list_request_contractors(self, current_user: CurrentUser) -> list[RequestContractorListItem]:
        UserPolicy.ensure_can_create_request(current_user)

        rows = await self._users.list_contractors(contractor_role_id=settings.contractor_role_id)
        return [
            RequestContractorListItem(
                user_id=user.id,
                full_name=profile.full_name if profile else None,
                company_name=company.company_name if company else None,
                mail=profile.mail if profile else None,
                company_mail=company.mail if company else None,
            )
            for user, profile, company, _ in rows
            if user.status == "active"
        ]
    
    def _period_to_data(self, period: UserStatusPeriod) -> UnavailabilityPeriodData:
        return UnavailabilityPeriodData(
            id=period.id,
            status=period.status,
            started_at=period.started_at,
            ended_at=period.ended_at,
        )

    async def get_subordinate_profile(
        self,
        *,
        current_user: CurrentUser,
        subordinate_user_id: str,
    ) -> SubordinateProfileResult:
        UserPolicy.ensure_can_list_users(current_user)

        subordinate = await self._users.get_by_id(subordinate_user_id)
        if subordinate is None:
            raise NotFound("User not found")

        await self._ensure_accessible_subordinate(
            current_user=current_user,
            subordinate=subordinate,
        )

        profile = None
        descendant_rows = await self._users.list_by_role_ids_with_profiles_and_roles(
            role_ids=[settings.lead_economist_role_id, settings.economist_role_id],
        )
        for user, user_profile, _ in descendant_rows:
            if user.id == subordinate_user_id:
                profile = user_profile
                break

        unavailable_period = await self._user_status_periods.get_active_for_user(user_id=subordinate_user_id)
        unavailable_periods = await self._user_status_periods.list_for_user(user_id=subordinate_user_id)

        return SubordinateProfileResult(
            user_id=subordinate.id,
            role_id=subordinate.id_role,
            id_parent=subordinate.id_parent,
            status=subordinate.status,
            full_name=profile.full_name if profile else None,
            phone=profile.phone if profile else None,
            mail=profile.mail if profile else None,
            unavailable_period=self._period_to_data(unavailable_period) if unavailable_period is not None else None,
            unavailable_periods=[self._period_to_data(period) for period in unavailable_periods],
        )
    
    async def get_me(self, current_user: CurrentUser) -> MeResult:
        UserPolicy.ensure_can_manage_own_profile(current_user)

        row = await self._users.get_with_profile_and_company_contacts(user_id=current_user.user_id)
        if row is None:
            raise NotFound("User not found")

        user, profile, company_contact = row
        unavailable_period = await self._user_status_periods.get_active_for_user(user_id=current_user.user_id)
        unavailable_periods = await self._user_status_periods.list_for_user(user_id=current_user.user_id)

        return MeResult(
            user_id=user.id,
            role_id=user.id_role,
            status=user.status,
            tg_user_id=user.tg_user_id,
            full_name=profile.full_name if profile else None,
            phone=profile.phone if profile else None,
            mail=profile.mail if profile else None,
            company_name=company_contact.company_name if company_contact else None,
            inn=company_contact.inn if company_contact else None,
            company_phone=company_contact.phone if company_contact else None,
            company_mail=company_contact.mail if company_contact else None,
            address=company_contact.address if company_contact else None,
            note=company_contact.note if company_contact else None,
            unavailable_period=self._period_to_data(unavailable_period) if unavailable_period is not None else None,
            unavailable_periods=[self._period_to_data(period) for period in unavailable_periods],
        )

@dataclass(frozen=True)
class UserRoleUpdateResult:
    user_id: str
    role_id: int


@dataclass(frozen=True)
class UserManagerUpdateResult:
    user_id: str
    manager_user_id: str


@dataclass(frozen=True)
class ManualContractorUpdateInput:
    login: str | None = None
    password: str | None = None
    full_name: str | None = None
    phone: str | None = None
    mail: str | None = None
    company_name: str | None = None
    inn: str | None = None
    company_phone: str | None = None
    company_mail: str | None = None
    address: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class ManualContractorCreateInput:
    company_name: str
    inn: str
    company_phone: str
    company_mail: str | None = None
    address: str | None = None
    note: str | None = None


class ManualContractorService:
    def __init__(
        self,
        users: UserRepository,
        profiles: ProfileRepository,
        company_contacts: CompanyContactRepository,
        user_auth_accounts: UserAuthAccountRepository,
        *,
        keycloak_admin: KeycloakAdminService | None = None,
    ) -> None:
        self._users = users
        self._profiles = profiles
        self._company_contacts = company_contacts
        self._user_auth_accounts = user_auth_accounts
        self._keycloak_admin = keycloak_admin or KeycloakAdminService()

    def _normalize_required_text(self, value: str | None, *, field_name: str, max_length: int | None = None) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise Conflict(f"{field_name} is required")
        if max_length is not None and len(normalized) > max_length:
            raise Conflict(f"{field_name} is too long")
        return normalized

    def _normalize_optional_text(self, value: str | None, *, max_length: int | None = None) -> str | None:
        normalized = (value or "").strip()
        if not normalized:
            return None
        if max_length is not None and len(normalized) > max_length:
            raise Conflict("Value is too long")
        return normalized

    def _validate_manual_contractor_create_data(
        self,
        *,
        data: ManualContractorCreateInput,
    ) -> ManualContractorCreateInput:
        try:
            company_name = self._normalize_required_text(
                data.company_name,
                field_name="Company name",
                max_length=256,
            )
            inn = validate_inn(
                self._normalize_required_text(
                    data.inn,
                    field_name="INN",
                    max_length=32,
                )
            )
            company_phone = validate_ru_phone(
                self._normalize_required_text(
                    data.company_phone,
                    field_name="Company phone",
                    max_length=64,
                )
            )
            company_mail = validate_optional_email(
                self._normalize_optional_text(data.company_mail, max_length=256),
                allow_placeholder=True,
            )
            address = self._normalize_optional_text(data.address, max_length=256)
            note = self._normalize_optional_text(data.note, max_length=1024)
        except ValueError as exc:
            raise Conflict(str(exc)) from exc

        return ManualContractorCreateInput(
            company_name=company_name,
            inn=inn,
            company_phone=company_phone,
            company_mail=company_mail,
            address=address,
            note=note,
        )

    def _build_login_slug(self, company_name: str) -> str:
        normalized_name = unicodedata.normalize("NFKC", company_name.strip().lower())
        transliterated: list[str] = []
        for char in normalized_name:
            if char in _CYRILLIC_TO_LATIN:
                transliterated.append(_CYRILLIC_TO_LATIN[char])
                continue
            if char.isascii() and char.isalnum():
                transliterated.append(char)
                continue
            transliterated.append("_")

        candidate = "".join(transliterated)
        candidate = _LOGIN_CLEANUP_PATTERN.sub("_", candidate)
        candidate = _LOGIN_COLLAPSE_PATTERN.sub("_", candidate).strip("_")
        if candidate:
            return candidate
        return "contractor"

    async def _build_manual_login(self, *, company_name: str) -> str:
        date_suffix = datetime.now().strftime("%d_%m")
        base_slug = self._build_login_slug(company_name)
        base_candidate = f"{base_slug}_{date_suffix}"
        if len(base_candidate) > 120:
            base_candidate = base_candidate[:120].rstrip("_")
        if len(base_candidate) < 3:
            base_candidate = f"{base_candidate}xxx"[:3]

        if not await self._users.exists(base_candidate):
            return base_candidate

        index = 1
        while True:
            suffix = f"_{index}"
            login_candidate = f"{base_candidate[: max(0, 128 - len(suffix))]}{suffix}"
            if not await self._users.exists(login_candidate):
                return login_candidate
            index += 1
            if index > 1000:
                raise Conflict("Unable to generate unique login for manual contractor")

    def _build_manual_password(self) -> str:
        return datetime.now().strftime("%d%m%Y%H%M%S%f")[:-3]

    async def _create_manual_contractor(self, *, data: ManualContractorCreateInput) -> str:
        login = await self._build_manual_login(company_name=data.company_name)
        await self._users.add(
            User(
                id=login,
                id_role=settings.contractor_role_id,
                status="active",
            )
        )
        await self._profiles.add(
            Profile(
                id=login,
                full_name=PLACEHOLDER_TEXT,
                phone=PLACEHOLDER_TEXT,
                mail=PLACEHOLDER_TEXT,
            )
        )
        await self._company_contacts.add(
            CompanyContact(
                id=login,
                company_name=data.company_name,
                inn=data.inn,
                phone=data.company_phone,
                mail=data.company_mail or PLACEHOLDER_TEXT,
                address=data.address or PLACEHOLDER_TEXT,
                note=data.note or PLACEHOLDER_TEXT,
            )
        )
        keycloak_user = await self._keycloak_admin.ensure_user(
            username=login,
            email=_normalize_keycloak_email_value(data.company_mail),
            email_verified=False,
        )
        await _bind_keycloak_account(
            user_auth_accounts=self._user_auth_accounts,
            user_id=login,
            keycloak_subject_id=keycloak_user.id,
            username=login,
            email=_normalize_keycloak_email_value(data.company_mail),
        )
        return login

    async def create_manual_contractor(
        self,
        *,
        current_user: CurrentUser,
        data: ManualContractorCreateInput,
    ) -> str:
        UserPolicy.ensure_can_register_user(current_user)
        if current_user.role_id != settings.superadmin_role_id:
            raise Forbidden("Only superadmin can create manual contractors")

        normalized_data = self._validate_manual_contractor_create_data(data=data)
        return await self._create_manual_contractor(data=normalized_data)

    def _normalize_value(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise Conflict("Updated value cannot be empty")
        return normalized

    async def update_manual_contractor(
        self,
        *,
        current_user: CurrentUser,
        user_id: str,
        data: ManualContractorUpdateInput,
    ) -> str:
        UserPolicy.ensure_can_manage_manual_contractors(current_user)
        original_user_id = user_id

        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFound("User not found")
        if user.id_role != settings.contractor_role_id:
            raise Conflict("Only contractor can be updated by this endpoint")
        if user.tg_user_id is not None:
            raise Conflict("Only manually created contractor can be updated by this endpoint")

        profile = await self._profiles.get_by_id(user.id)
        if profile is None:
            raise NotFound("Profile not found")
        company_contact = await self._company_contacts.get_by_id(user.id)
        if company_contact is None:
            raise NotFound("Company contacts not found")

        next_login = self._normalize_value(data.login)
        next_password = self._normalize_value(data.password)
        if next_login is not None and next_login != user.id:
            if await self._users.exists(next_login):
                raise Conflict("User already exists")

            cloned_user = User(
                id=next_login,
                id_role=user.id_role,
                id_parent=user.id_parent,
                status=user.status,
                tg_user_id=user.tg_user_id,
            )
            await self._users.add(cloned_user)
            await self._users.reassign_user_id(old_user_id=user.id, new_user_id=next_login)
            await self._users.delete_by_id(user_id=user.id)
            user = cloned_user
            profile = await self._profiles.get_by_id(user.id)
            company_contact = await self._company_contacts.get_by_id(user.id)
            if profile is None or company_contact is None:
                raise Conflict("Contractor profile data is inconsistent")

        if next_password is not None:
            raise Forbidden("Password is managed by the identity provider")

        full_name = self._normalize_value(data.full_name)
        phone = self._normalize_value(data.phone)
        mail = self._normalize_value(data.mail)
        company_name = self._normalize_value(data.company_name)
        inn = self._normalize_value(data.inn)
        company_phone = self._normalize_value(data.company_phone)
        company_mail = self._normalize_value(data.company_mail)
        address = self._normalize_value(data.address)
        note = self._normalize_value(data.note)

        if full_name is not None:
            profile.full_name = full_name
        if phone is not None:
            profile.phone = phone
        if mail is not None:
            profile.mail = mail
        if company_name is not None:
            company_contact.company_name = company_name
        if inn is not None:
            company_contact.inn = inn
        if company_phone is not None:
            company_contact.phone = company_phone
        if company_mail is not None:
            company_contact.mail = company_mail
        if address is not None:
            company_contact.address = address
        if note is not None:
            company_contact.note = note

        keycloak_user = await self._keycloak_admin.ensure_user(
            username=user.id,
            previous_username=original_user_id,
            email=_normalize_keycloak_email_value(company_contact.mail),
            email_verified=False,
        )
        await _bind_keycloak_account(
            user_auth_accounts=self._user_auth_accounts,
            user_id=user.id,
            keycloak_subject_id=keycloak_user.id,
            username=user.id,
            email=_normalize_keycloak_email_value(company_contact.mail),
        )

        return user.id


class UserRoleService:
    def __init__(self, users: UserRepository):
        self._users = users

    async def update_role(
        self,
        *,
        current_user: CurrentUser,
        user_id: str,
        role_id: int,
    ) -> UserRoleUpdateResult:
        UserPolicy.ensure_can_update_user_role(current_user)

        if role_id not in {settings.admin_role_id, settings.economist_role_id}:
            raise Conflict("Only admin and economist roles are allowed for update")

        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFound("User not found")

        if user.id_role == settings.superadmin_role_id:
            raise Forbidden("Superadmin role cannot be changed")

        await self._users.update_role(user, role_id)
        return UserRoleUpdateResult(user_id=user.id, role_id=user.id_role)


class UserManagerService:
    def __init__(self, users: UserRepository):
        self._users = users

    async def update_manager(
        self,
        *,
        current_user: CurrentUser,
        user_id: str,
        manager_user_id: str,
    ) -> UserManagerUpdateResult:
        UserPolicy.ensure_can_update_user_manager(current_user)

        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFound("User not found")

        if not _can_manage_subordinate_role(
            current_role_id=current_user.role_id,
            target_role_id=user.id_role,
        ):
            raise Forbidden("You can update manager only for permitted subordinate roles")

        if user.id == current_user.user_id:
            raise Forbidden("You can update manager only for your subordinates")

        is_subordinate = await _is_descendant_user(
            self._users,
            ancestor_user_id=current_user.user_id,
            target_user_id=user.id,
        )
        if not is_subordinate:
            raise Forbidden("You can update manager only for your subordinates")

        manager_user = await self._users.get_by_id(manager_user_id)
        if manager_user is None:
            raise NotFound("Manager user not found")
        if manager_user.id == user.id:
            raise Conflict("User cannot be own manager")

        if user.id_role == settings.economist_role_id:
            allowed_manager_role_ids = {
                settings.economist_role_id,
                settings.lead_economist_role_id,
            }
        elif user.id_role == settings.lead_economist_role_id:
            allowed_manager_role_ids = {settings.project_manager_role_id}
        else:
            raise Conflict("Manager can be updated only for lead economist and economist users")

        if manager_user.id_role not in allowed_manager_role_ids:
            raise Conflict("Selected manager role is not allowed for this user")

        candidate_query = UserQueryService(
            self._users,
            UserStatusPeriodRepository(self._users._session),
        )
        allowed_manager_ids = {
            item.user_id
            for item in await candidate_query.list_manager_candidates(
                current_user=current_user,
                target_role_id=user.id_role,
            )
        }
        if manager_user.id not in allowed_manager_ids:
            raise Forbidden("Selected manager is outside the allowed management scope")

        would_create_cycle = await _is_descendant_user(
            self._users,
            ancestor_user_id=user.id,
            target_user_id=manager_user.id,
        )
        if would_create_cycle:
            raise Conflict("Selected manager would create a hierarchy cycle")

        await self._users.update_parent(user, manager_user.id)
        return UserManagerUpdateResult(user_id=user.id, manager_user_id=user.id_parent or manager_user.id)


class UserStatusService:
    VALID_USER_STATUSES = {"active", "inactive", "review", "blacklist"}
    VALID_TG_STATUSES = {"approved", "disapproved", "review"}

    def __init__(
        self,
        users: UserRepository,
        tg_users: TgUserRepository,
        profiles: ProfileRepository,
    ):
        self._users = users
        self._tg_users = tg_users
        self._profiles = profiles

    async def update_statuses(
        self,
        *,
        current_user: CurrentUser,
        user_id: str,
        user_status: str,
        tg_status: str | None,
    ) -> UserStatusUpdateResult:
        UserPolicy.ensure_can_update_user_status(current_user)

        if user_status not in self.VALID_USER_STATUSES:
            raise Conflict("Unsupported users.status value")
        if tg_status is not None and tg_status not in self.VALID_TG_STATUSES:
            raise Conflict("Unsupported Telegram status value")
        if tg_status is not None and not settings.telegram_legacy_enabled:
            raise Forbidden("Telegram legacy status updates are disabled")

        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFound("User not found")

        if current_user.role_id in {
            settings.project_manager_role_id,
            settings.lead_economist_role_id,
            settings.economist_role_id,
        }:
            if not _can_manage_subordinate_role(
                current_role_id=current_user.role_id,
                target_role_id=user.id_role,
            ):
                raise Forbidden("You can update status only for permitted subordinate roles")
            if user.id == current_user.user_id:
                raise Forbidden("You can update status only for your subordinates")
            is_subordinate = await _is_descendant_user(
                self._users,
                ancestor_user_id=current_user.user_id,
                target_user_id=user.id,
            )
            if not is_subordinate:
                raise Forbidden("You can update status only for your subordinates")

        tg_user: TgUser | None = None
        if settings.telegram_legacy_enabled and user.tg_user_id is not None:
            tg_user = await self._tg_users.get_by_id(user.tg_user_id)

        if settings.telegram_legacy_enabled and tg_status is not None:
            if tg_user is None:
                raise Conflict("User has no linked Telegram account")
            await self._tg_users.update_status(tg_user, tg_status)

        if settings.telegram_legacy_enabled and tg_user is not None and tg_status is None:
            if user_status in {"inactive", "blacklist"}:
                await self._tg_users.update_status(tg_user, "disapproved")
            elif user_status == "active":
                await self._tg_users.update_status(tg_user, "approved")

        await self._users.update_status(user, user_status)

        notify_tg_id = tg_user.id if tg_user is not None else None

        result = UserStatusUpdateResult(
            user_id=user.id,
            user_status=user.status,
            tg_user_id=user.tg_user_id,
            tg_status=tg_user.status if tg_user else None,
        )

        notify_email: str | None = None
        if user.id_role == settings.contractor_role_id:
            profile = await self._profiles.get_by_id(user.id)
            notify_email = _normalize_notification_email(profile.mail if profile is not None else None)

        if settings.telegram_legacy_enabled and notify_tg_id is not None and tg_user is not None:
            if user.status == "active" and tg_user.status == "approved":
                await notify_tg_access_opened(notify_tg_id)
            else:
                await notify_tg_access_closed(notify_tg_id)

        if notify_email is not None and (notify_tg_id is None or not settings.telegram_legacy_enabled):
            if user.status == "active":
                await notify_contractor_access_opened_email(to_email=notify_email)

        return result
    
class UserSelfService:
    VALID_UNAVAILABILITY_STATUSES = {"sick", "vacation", "fired", "maternity", "business_trip", "unavailable"}

    def __init__(
        self,
        users: UserRepository,
        profiles: ProfileRepository,
        company_contacts: CompanyContactRepository,
        user_status_periods: UserStatusPeriodRepository,
    ):
        self._users = users
        self._profiles = profiles
        self._company_contacts = company_contacts
        self._user_status_periods = user_status_periods

    async def _ensure_accessible_subordinate(
        self,
        *,
        current_user: CurrentUser,
        subordinate: User,
    ) -> None:
        if not _can_manage_subordinate_role(
            current_role_id=current_user.role_id,
            target_role_id=subordinate.id_role,
        ):
            raise Conflict("Subordinate data can be managed only for permitted subordinate roles")
        if subordinate.id == current_user.user_id:
            raise Forbidden("You can manage subordinate data only for your subordinates")
        is_subordinate = await _is_descendant_user(
            self._users,
            ancestor_user_id=current_user.user_id,
            target_user_id=subordinate.id,
        )
        if not is_subordinate:
            raise Forbidden("You can manage subordinate data only for your subordinates")

    async def _ensure_no_period_overlap(
        self,
        *,
        user_id: str,
        started_at: datetime,
        ended_at: datetime,
    ) -> None:
        overlapping = await self._user_status_periods.get_overlapping_for_user(
            user_id=user_id,
            started_at=started_at,
            ended_at=ended_at,
        )
        if overlapping is not None:
            raise Conflict(
                "User already has unavailability period in this time range "
                f"{overlapping.started_at.isoformat()} - {overlapping.ended_at.isoformat()}"
            )

        existing_periods = await self._user_status_periods.list_for_user(user_id=user_id)
        new_start_date = started_at.date()
        new_end_date = ended_at.date()
        for period in existing_periods:
            period_start_date = period.started_at.date()
            period_end_date = period.ended_at.date()
            has_date_overlap = period_start_date <= new_end_date and period_end_date >= new_start_date
            if has_date_overlap:
                raise Conflict(
                    "User already has unavailability period in this time range "
                    f"{period.started_at.isoformat()} - {period.ended_at.isoformat()}"
                )

    async def update_my_credentials(
        self,
        current_user: CurrentUser,
        *,
        current_password: str,
        new_password: str,
    ) -> None:
        UserPolicy.ensure_can_manage_own_profile(current_user)
        raise Forbidden("Password is managed by the identity provider")

    async def update_my_profile(
        self,
        current_user: CurrentUser,
        *,
        full_name: str | None,
        phone: str | None,
        mail: str | None,
    ) -> None:
        UserPolicy.ensure_can_manage_own_profile(current_user)

        profile = await self._profiles.get_by_id(current_user.user_id)
        if profile is None:
            await self._profiles.add(
                Profile(
                    id=current_user.user_id,
                    full_name=full_name or "Не указано",
                    phone=phone or "Не указано",
                    mail=mail or "Не указано",
                )
            )
            return

        if full_name is not None:
            profile.full_name = full_name
        if phone is not None:
            profile.phone = phone
        if mail is not None:
            profile.mail = mail

    async def update_my_company_contacts(
        self,
        current_user: CurrentUser,
        *,
        company_name: str | None,
        inn: str | None,
        company_phone: str | None,
        company_mail: str | None,
        address: str | None,
        note: str | None,
    ) -> None:
        UserPolicy.ensure_can_manage_own_company_contacts(current_user)

        company_contacts = await self._company_contacts.get_by_id(current_user.user_id)
        if company_contacts is None:
            if company_name is None or inn is None:
                raise NotFound("Company contacts not found")
            await self._company_contacts.add(
                CompanyContact(
                    id=current_user.user_id,
                    company_name=company_name,
                    inn=inn,
                    phone=company_phone or PLACEHOLDER_TEXT,
                    mail=company_mail or PLACEHOLDER_TEXT,
                    address=address or PLACEHOLDER_TEXT,
                    note=note or PLACEHOLDER_TEXT,
                )
            )
            return

        if company_name is not None:
            company_contacts.company_name = company_name
        if inn is not None:
            company_contacts.inn = inn
        if company_phone is not None:
            company_contacts.phone = company_phone
        if company_mail is not None:
            company_contacts.mail = company_mail
        if address is not None:
            company_contacts.address = address
        if note is not None:
            company_contacts.note = note

    async def set_subordinate_unavailability_period(
        self,
        *,
        current_user: CurrentUser,
        subordinate_user_id: str,
        status: str,
        started_at: datetime,
        ended_at: datetime,
    ) -> None:
        UserPolicy.ensure_can_manage_subordinate_unavailability(current_user)

        if status not in self.VALID_UNAVAILABILITY_STATUSES:
            raise Conflict("Unsupported user_status_periods.status value")

        normalized_started_at = _normalize_db_timestamp(started_at)
        normalized_ended_at = _normalize_db_timestamp(ended_at)

        if normalized_ended_at < normalized_started_at:
            raise Conflict("Period end date must be greater than or equal to start date")

        subordinate = await self._users.get_by_id(subordinate_user_id)
        if subordinate is None:
            raise NotFound("User not found")

        await self._ensure_accessible_subordinate(
            current_user=current_user,
            subordinate=subordinate,
        )

        await self._ensure_no_period_overlap(
            user_id=subordinate_user_id,
            started_at=normalized_started_at,
            ended_at=normalized_ended_at,
        )

        await self._user_status_periods.add(
            UserStatusPeriod(
                id_user=subordinate_user_id,
                status=status,
                started_at=normalized_started_at,
                ended_at=normalized_ended_at,
            )
        )

    async def set_my_unavailability_period(
        self,
        current_user: CurrentUser,
        *,
        status: str,
        started_at: datetime,
        ended_at: datetime,
    ) -> None:
        UserPolicy.ensure_can_manage_own_unavailability(current_user)

        if status not in self.VALID_UNAVAILABILITY_STATUSES:
            raise Conflict("Unsupported user_status_periods.status value")

        normalized_started_at = _normalize_db_timestamp(started_at)
        normalized_ended_at = _normalize_db_timestamp(ended_at)

        if normalized_ended_at < normalized_started_at:
            raise Conflict("Period end date must be greater than or equal to start date")

        user = await self._users.get_by_id(current_user.user_id)
        if user is None:
            raise NotFound("User not found")

        await self._ensure_no_period_overlap(
            user_id=current_user.user_id,
            started_at=normalized_started_at,
            ended_at=normalized_ended_at,
        )

        await self._user_status_periods.add(
            UserStatusPeriod(
                id_user=current_user.user_id,
                status=status,
                started_at=normalized_started_at,
                ended_at=normalized_ended_at,
            )
        )
