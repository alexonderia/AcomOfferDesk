from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Awaitable, Callable

from app.core.config import settings
from app.domain.contractor_validation import validate_inn, validate_optional_email, validate_ru_phone
from app.domain.authorization import has_permission
from app.domain.department_delegations import get_department_permission_codes
from app.domain.exceptions import Conflict, Forbidden, NotFound
from app.domain.permissions import PermissionCodes
from app.domain.policies import CurrentUser, UserPolicy
from app.models.orm_models import CompanyContact, Profile, Role, User, UserStatusPeriod
from app.repositories.company_contacts import CompanyContactRepository
from app.repositories.profiles import ProfileRepository
from app.repositories.user_auth_accounts import UserAuthAccountRepository
from app.repositories.user_status_periods import UserStatusPeriodRepository
from app.repositories.units import UnitRepository
from app.repositories.users import UserRepository
from app.services.contractor_email_notifications import (
    notify_contractor_status_changed_email,
)
from app.infrastructure.iam_client import IamClient
from app.infrastructure.notification_publisher import publish_process_notification_event
from app.services.registration_admin_notify import schedule_registration_review_required_notification
from app.services.department_scope import DepartmentScopeService
from app.services.contractor_units import ContractorUnitService
from app.services.staff_access_scope import StaffAccessScopeService
from app.services.unit_hierarchy import HierarchyCounts, UnitHierarchyService
from app.services.user_notification_preferences import UserNotificationPreferencesService
from shared.process_notifications import ProcessNotificationEvent, build_process_notification_event

ROLE_NAME_SUPERADMIN = "Суперадмин"
ROLE_NAME_ADMIN = "Администратор"
ROLE_NAME_PROJECT_MANAGER = "Руководитель проекта"
ROLE_NAME_LEAD_ECONOMIST = "Ведущий экономист"
ROLE_NAME_ECONOMIST = "Экономист"
ROLE_NAME_OPERATOR = "Оператор"
ROLE_NAME_CONTRACTOR = "Контрагент"
ROLE_NAME_SECURITY_OFFICER = "Служба безопасности"
PLACEHOLDER_TEXT = "Не указано"
SUBORDINATE_PROFILE_ROLE_IDS = {
    settings.lead_economist_role_id,
    settings.economist_role_id,
    settings.operator_role_id,
}
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
    return await UnitHierarchyService(users).is_manager_of(
        manager_user_id=ancestor_user_id,
        subordinate_user_id=target_user_id,
    )

def _role_update_options_for_user(current_user: CurrentUser) -> set[int]:
    if current_user.role_id == settings.superadmin_role_id and has_permission(
        current_user, PermissionCodes.USERS_ROLE_UPDATE_ANY
    ):
        return {
            settings.admin_role_id,
            settings.contractor_role_id,
            settings.security_officer_role_id,
            settings.project_manager_role_id,
            settings.lead_economist_role_id,
            settings.economist_role_id,
            settings.operator_role_id,
        }
    if current_user.role_id == settings.admin_role_id and has_permission(
        current_user, PermissionCodes.USERS_ROLE_UPDATE_ANY
    ):
        # Contractor onboarding is a separate flow; Admin may only assign the
        # two staff roles explicitly approved for this role.
        return {settings.economist_role_id, settings.operator_role_id}
    if not has_permission(current_user, PermissionCodes.USERS_ROLE_UPDATE_ECONOMY):
        return set()
    if current_user.role_id == settings.project_manager_role_id:
        return {
            settings.lead_economist_role_id,
            settings.economist_role_id,
            settings.operator_role_id,
        }
    if current_user.role_id == settings.lead_economist_role_id:
        return {settings.economist_role_id, settings.operator_role_id}
    return set()


@dataclass(frozen=True)
class HierarchyRoleRule:
    parent_required: bool
    parent_allowed: bool
    allowed_parent_role_ids: frozenset[int]


def _hierarchy_rule_for_role(*, role_id: int) -> HierarchyRoleRule:
    if role_id == settings.project_manager_role_id:
        return HierarchyRoleRule(
            parent_required=False,
            parent_allowed=True,
            allowed_parent_role_ids=frozenset({settings.project_manager_role_id}),
        )
    if role_id == settings.lead_economist_role_id:
        return HierarchyRoleRule(
            parent_required=True,
            parent_allowed=True,
            allowed_parent_role_ids=frozenset(
                {
                    settings.project_manager_role_id,
                    settings.lead_economist_role_id,
                }
            ),
        )
    if role_id == settings.economist_role_id:
        return HierarchyRoleRule(
            parent_required=True,
            parent_allowed=True,
            allowed_parent_role_ids=frozenset(
                {
                    settings.lead_economist_role_id,
                    settings.economist_role_id,
                }
            ),
        )
    return HierarchyRoleRule(
        parent_required=False,
        parent_allowed=False,
        allowed_parent_role_ids=frozenset(),
    )


def _role_name_by_id(*, role_id: int) -> str:
    if role_id == settings.project_manager_role_id:
        return ROLE_NAME_PROJECT_MANAGER
    if role_id == settings.lead_economist_role_id:
        return ROLE_NAME_LEAD_ECONOMIST
    if role_id == settings.economist_role_id:
        return ROLE_NAME_ECONOMIST
    if role_id == settings.operator_role_id:
        return ROLE_NAME_OPERATOR
    if role_id == settings.contractor_role_id:
        return ROLE_NAME_CONTRACTOR
    if role_id == settings.security_officer_role_id:
        return ROLE_NAME_SECURITY_OFFICER
    if role_id == settings.admin_role_id:
        return ROLE_NAME_ADMIN
    if role_id == settings.superadmin_role_id:
        return ROLE_NAME_SUPERADMIN
    return "Неизвестная роль"


def _manager_required_error(*, role_id: int) -> str:
    role_name = _role_name_by_id(role_id=role_id)
    return f"Для роли «{role_name}» необходимо указать руководителя"


def _manager_disallowed_error(*, role_id: int) -> str:
    role_name = _role_name_by_id(role_id=role_id)
    return f"Для роли «{role_name}» руководитель не используется"


def _normalize_notification_email(value: str | None) -> str | None:
    normalized = (value or "").strip()
    if not normalized:
        return None
    if normalized.lower() in {PLACEHOLDER_TEXT.lower(), "none", "null"}:
        return None
    return normalized


class UserRegistrationService:
    def __init__(
        self,
        users: UserRepository,
        profiles: ProfileRepository,
        user_auth_accounts: UserAuthAccountRepository,
    ):
        self._users = users
        self._profiles = profiles
        self._user_auth_accounts = user_auth_accounts

    async def register_user(
        self,
        current_user: CurrentUser,
        *,
        user_id: str,
        role_id: int,
        id_parent: str | None,
        full_name: str | None,
        phone: str | None,
        mail: str | None,
    ) -> User:
        UserPolicy.ensure_can_register_user(current_user)
        target_role = await self._users.get_role_by_id(role_id)
        if target_role is None:
            raise Conflict("Роль недоступна для создания")
        if role_id == settings.contractor_role_id:
            raise Conflict("Контрагента нельзя создавать через регистрацию сотрудника")
        if current_user.role_id == settings.superadmin_role_id and role_id == settings.superadmin_role_id:
            raise Forbidden("Суперадминистратор не может создавать суперадминистраторов")
        if current_user.role_id == settings.lead_economist_role_id and role_id != settings.economist_role_id:
            raise Forbidden("Ведущий экономист может создавать только экономистов")
        current_role = await self._users.get_role_by_id(current_user.role_id)
        if current_role is None:
            raise Forbidden("Доступ запрещен")

        if current_role.role not in {
            ROLE_NAME_SUPERADMIN,
            ROLE_NAME_ADMIN,
            ROLE_NAME_LEAD_ECONOMIST,
        }:
            raise Forbidden("Доступ запрещен")

        if target_role.role == ROLE_NAME_SUPERADMIN:
            raise Forbidden("Суперадминистратор не может создавать суперадминистраторов")

        if current_role.role == ROLE_NAME_ADMIN and target_role.role not in {
            ROLE_NAME_ECONOMIST,
            ROLE_NAME_OPERATOR,
        }:
            raise Forbidden("Администратор может создавать только экономистов и операторов")

        if current_role.role == ROLE_NAME_LEAD_ECONOMIST and target_role.role != ROLE_NAME_ECONOMIST:
            raise Forbidden("Ведущий экономист может создавать только экономистов")
        role_rule = _hierarchy_rule_for_role(role_id=role_id)
        if not role_rule.parent_allowed:
            id_parent = None

        if id_parent is not None:
            if id_parent == user_id:
                raise Conflict("Пользователь не может быть руководителем самому себе")
            parent_user = await self._users.get_by_id(id_parent)
            if parent_user is None:
                raise NotFound("Руководитель не найден")
            if parent_user.id_role not in role_rule.allowed_parent_role_ids:
                raise Conflict("Выбранный пользователь не может быть руководителем для этой роли")

            visible_user_ids = await UnitHierarchyService(self._users).get_visible_user_ids(
                current_user=current_user,
            )
            if visible_user_ids is not None and id_parent not in visible_user_ids:
                raise Forbidden("Выбранный руководитель вне разрешенной зоны управления")
        if await self._users.exists(user_id):
            raise Conflict("Пользователь уже существует")

        normalized_full_name = (full_name or "").strip() or PLACEHOLDER_TEXT
        normalized_phone = (phone or "").strip() or PLACEHOLDER_TEXT
        normalized_mail = (mail or "").strip()
        if not normalized_mail:
            raise Conflict("Для создания пользователя требуется email")
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
    email_verified: bool = False
    is_manual: bool = False
    company_name: str | None = None
    inn: str | None = None
    company_phone: str | None = None
    company_mail: str | None = None
    address: str | None = None
    note: str | None = None
    units_count: int = 0
    managers_count: int = 0
    subordinates_count: int = 0


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

    async def resolve_hierarchy_subordinate_user_ids(
        self,
        *,
        current_user: CurrentUser,
    ) -> set[str] | None:
        if current_user.role_id not in {
            settings.project_manager_role_id,
            settings.lead_economist_role_id,
            settings.economist_role_id,
        }:
            return None

        hierarchy = UnitHierarchyService(self._users)
        return set(await hierarchy.get_subordinate_user_ids(user_id=current_user.user_id))

    async def _resolve_internal_staff_scope_user_ids(
        self,
        *,
        current_user: CurrentUser,
    ) -> set[str]:
        visible_ids = await UnitHierarchyService(self._users).get_visible_user_ids(
            current_user=current_user,
        )
        if visible_ids is None:
            return set()
        return visible_ids

    async def _apply_hierarchy_counts(self, items: list[UserListItem]) -> list[UserListItem]:
        if not items:
            return items

        hierarchy = UnitHierarchyService(self._users)
        counts_by_user_id = await hierarchy.get_hierarchy_counts_by_user_ids(
            user_ids=[item.user_id for item in items],
        )
        result: list[UserListItem] = []
        for item in items:
            counts = counts_by_user_id.get(item.user_id, HierarchyCounts(0, 0, 0))
            result.append(
                replace(
                    item,
                    units_count=counts.units_count,
                    managers_count=counts.managers_count,
                    subordinates_count=counts.subordinates_count,
                )
            )
        return result

    async def _apply_email_verified(self, items: list[UserListItem]) -> list[UserListItem]:
        if not items:
            return items
        verified_by_user_id = await self._users.map_primary_email_verified(
            user_ids=[item.user_id for item in items],
        )
        return [
            replace(item, email_verified=verified_by_user_id.get(item.user_id, False))
            for item in items
        ]

    async def _ensure_accessible_subordinate(
        self,
        *,
        current_user: CurrentUser,
        subordinate: User,
    ) -> None:
        if subordinate.id_role not in SUBORDINATE_PROFILE_ROLE_IDS:
            raise Conflict("Профиль подчиненного доступен только для разрешенных ролей")

        if not UserPolicy.can_manage_subordinate_role(
            current_role_id=current_user.role_id,
            target_role_id=subordinate.id_role,
        ):
            raise Conflict("Профиль подчиненного доступен только для разрешенных ролей")

        if subordinate.id == current_user.user_id:
            raise Forbidden("Вы можете управлять данными только своих подчиненных")

        is_subordinate = await self._is_descendant(
            manager_user_id=current_user.user_id,
            subordinate_user_id=subordinate.id,
        )
        if not is_subordinate:
            raise Forbidden("Вы можете управлять данными только своих подчиненных")

    async def list_users(self, current_user: CurrentUser, role_id: int | None = None) -> list[UserListItem]:
        UserPolicy.ensure_can_list_users(current_user)

        if current_user.role_id in {
            settings.lead_economist_role_id,
            settings.project_manager_role_id,
            settings.economist_role_id,
        }:
            scoped_internal_role_ids = {
                settings.lead_economist_role_id,
                settings.economist_role_id,
                settings.operator_role_id,
            }
            allowed_role_ids = scoped_internal_role_ids if role_id is None else {role_id}
            if not allowed_role_ids.issubset(scoped_internal_role_ids):
                raise Forbidden("Руководитель проекта, ведущий экономист и экономист могут просматривать только сотрудников своего контура")

            rows = await self._users.list_by_role_ids_with_profiles_and_roles(
                role_ids=sorted(scoped_internal_role_ids),
            )
            visible_scope_ids = await self._resolve_internal_staff_scope_user_ids(current_user=current_user)
            items = [
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
                if user.id in visible_scope_ids and user.id_role in allowed_role_ids
            ]
            return await self._apply_email_verified(await self._apply_hierarchy_counts(items))

        if current_user.role_id == settings.admin_role_id and role_id != settings.contractor_role_id:
            visible_scope_ids = await UnitHierarchyService(self._users).get_visible_user_ids(
                current_user=current_user,
            )
            rows = await self._users.list_users_with_profiles(role_id=role_id)
            items = [
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
                if (
                    visible_scope_ids is None or user.id in visible_scope_ids
                )
                and user.id_role not in {
                    settings.contractor_role_id,
                    settings.superadmin_role_id,
                }
            ]
            return await self._apply_email_verified(await self._apply_hierarchy_counts(items))

        if role_id == settings.contractor_role_id:
            rows = await self._users.list_contractors(contractor_role_id=settings.contractor_role_id)
            items = [
                UserListItem(
                    user_id=user.id,
                    role_id=user.id_role,
                    id_parent=user.id_parent,
                    status=user.status,
                    full_name=profile.full_name if profile else None,
                    phone=profile.phone if profile else None,
                    mail=profile.mail if profile else None,
                    is_manual=_legacy_user is None and legacy_account_id is None,
                    company_name=company.company_name if company else None,
                    inn=company.inn if company else None,
                    company_phone=company.phone if company else None,
                    company_mail=company.mail if company else None,
                    address=company.address if company else None,
                    note=company.note if company else None,
                )
                for user, profile, company, _legacy_user, legacy_account_id in rows
            ]
            return await self._apply_email_verified(items)

        rows = await self._users.list_users_with_profiles(role_id=role_id)
        items = [
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
        return await self._apply_email_verified(await self._apply_hierarchy_counts(items))

    async def list_manager_candidates(
        self,
        current_user: CurrentUser,
        *,
        target_role_id: int,
        target_user_id: str | None = None,
    ) -> list[UserListItem]:
        if not (
            UserPolicy.can_register_user(current_user)
            or UserPolicy.can_update_user_manager(current_user)
        ):
            raise Forbidden("Недостаточно прав для просмотра кандидатов в руководители")

        if current_user.role_id == settings.lead_economist_role_id and target_role_id != settings.economist_role_id:
            raise Forbidden("Ведущий экономист может управлять только экономистами")
        if current_user.role_id == settings.economist_role_id and target_role_id != settings.economist_role_id:
            raise Forbidden("Экономист может управлять только экономистами")
        if current_user.role_id == settings.project_manager_role_id and target_role_id not in {
            settings.project_manager_role_id,
            settings.lead_economist_role_id,
            settings.economist_role_id,
        }:
            raise Forbidden("Руководитель проекта может управлять только руководителями проекта, ведущими экономистами и экономистами")

        role_rule = _hierarchy_rule_for_role(role_id=target_role_id)
        if not role_rule.parent_allowed:
            return []

        hierarchy = UnitHierarchyService(self._users)
        rows = await self._users.list_by_role_ids_with_profiles_and_roles(
            role_ids=list(role_rule.allowed_parent_role_ids),
        )
        rows = [row for row in rows if row[0].status == "active"]

        visible_user_ids = await hierarchy.get_visible_user_ids(current_user=current_user)
        if visible_user_ids is not None:
            rows = [row for row in rows if row[0].id in visible_user_ids]

        if target_user_id is not None:
            unit_based_manager_ids = set(await hierarchy.get_manager_user_ids(user_id=target_user_id))
            if unit_based_manager_ids:
                rows = [row for row in rows if row[0].id in unit_based_manager_ids]
            rows = [row for row in rows if row[0].id != target_user_id]

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
    
    async def list_economists(self, current_user: CurrentUser) -> list[EconomistListItem]:
        UserPolicy.ensure_can_list_users(current_user)

        rows = await self._users.list_users_with_profiles(role_id=settings.economist_role_id)
        visible_scope_ids: set[str] | None = None
        if current_user.role_id in {
            settings.admin_role_id,
            settings.project_manager_role_id,
            settings.lead_economist_role_id,
            settings.economist_role_id,
        }:
            visible_scope_ids = await self._resolve_internal_staff_scope_user_ids(current_user=current_user)
        return [
            EconomistListItem(
                user_id=user.id,
                status=user.status,
                full_name=profile.full_name if profile else None,
                phone=profile.phone if profile else None,
                mail=profile.mail if profile else None,
            )
            for user, profile in rows
            if visible_scope_ids is None or user.id in visible_scope_ids
        ]
    
    async def list_request_economists(self, current_user: CurrentUser) -> list[RequestEconomistListItem]:
        if not (
            current_user.role_id == settings.superadmin_role_id
            or current_user.role_id == settings.lead_economist_role_id
            or current_user.role_id == settings.project_manager_role_id
        ):
            raise Forbidden("Недостаточно прав для просмотра экономистов заявки")

        rows = await self._users.list_by_role_ids_with_profiles_and_roles(
            role_ids=[settings.lead_economist_role_id, settings.economist_role_id],
        )
        if current_user.role_id in {
            settings.lead_economist_role_id,
            settings.project_manager_role_id,
        }:
            hierarchy = UnitHierarchyService(self._users)
            if has_permission(current_user, PermissionCodes.DEPARTMENT_REQUESTS_ASSIGN):
                scoped_owner_ids = set(
                    await DepartmentScopeService(self._users).resolve_department_owner_ids_for_current_user(
                        current_user=current_user,
                    )
                )
            else:
                scoped_owner_ids = set(
                    await hierarchy.get_subordinate_user_ids(
                        user_id=current_user.user_id,
                    )
                )
                scoped_owner_ids.add(current_user.user_id)
            rows = [
                row for row in rows
                if row[0].id in scoped_owner_ids
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
            for user, profile, company, _, _legacy_account_id in rows
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
            raise NotFound("Пользователь не найден")

        await self._ensure_accessible_subordinate(
            current_user=current_user,
            subordinate=subordinate,
        )

        profile = None
        descendant_rows = await self._users.list_by_role_ids_with_profiles_and_roles(
            role_ids=list(SUBORDINATE_PROFILE_ROLE_IDS),
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
    
    async def _get_me_result(self, *, user_id: str) -> MeResult:
        row = await self._users.get_with_profile_and_company_contacts(user_id=user_id)
        if row is None:
            raise NotFound("Пользователь не найден")

        user, profile, company_contact = row
        unavailable_period = await self._user_status_periods.get_active_for_user(user_id=user_id)
        unavailable_periods = await self._user_status_periods.list_for_user(user_id=user_id)

        return MeResult(
            user_id=user.id,
            role_id=user.id_role,
            status=user.status,
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

    async def get_me(self, current_user: CurrentUser) -> MeResult:
        UserPolicy.ensure_can_manage_own_profile(current_user)
        return await self._get_me_result(user_id=current_user.user_id)

    async def get_me_for_review_onboarding(self, current_user: CurrentUser) -> MeResult:
        UserPolicy.ensure_can_manage_review_onboarding(current_user)
        return await self._get_me_result(user_id=current_user.user_id)

@dataclass(frozen=True)
class UserRoleUpdateResult:
    user_id: str
    role_id: int


@dataclass(frozen=True)
class UserManagerUpdateResult:
    user_id: str
    manager_user_id: str | None


@dataclass(frozen=True)
class ManualContractorUpdateInput:
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


@dataclass(frozen=True)
class ManualContractorCreateResult:
    user_id: str
    created: bool
    company_name: str
    inn: str
    company_mail: str | None


@dataclass(frozen=True)
class ManualContractorDuplicateItem:
    user_id: str
    full_name: str | None
    phone: str | None
    mail: str | None
    company_name: str | None
    inn: str | None
    company_phone: str | None
    company_mail: str | None
    address: str | None
    note: str | None
    status: str
    created_at: str | None
    updated_at: str | None


class ManualContractorService:
    def __init__(
        self,
        users: UserRepository,
        profiles: ProfileRepository,
        company_contacts: CompanyContactRepository,
        user_auth_accounts: UserAuthAccountRepository,
        units: UnitRepository | None = None,
        user_contact_channels=None,
        after_commit_hook_registrar: Callable[[Callable[[], Awaitable[None]]], None] | None = None,
    ) -> None:
        self._users = users
        self._profiles = profiles
        self._company_contacts = company_contacts
        self._user_auth_accounts = user_auth_accounts
        self._units = units
        self._user_contact_channels = user_contact_channels
        self._after_commit_hook_registrar = after_commit_hook_registrar

    def _contractor_unit_service(self) -> ContractorUnitService:
        if self._units is None:
            raise RuntimeError("Manual contractor service requires unit repository")
        return ContractorUnitService(users=self._users, units=self._units)

    def _normalize_required_text(self, value: str | None, *, field_name: str, max_length: int | None = None) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise Conflict(f"Поле {field_name} обязательно")
        if max_length is not None and len(normalized) > max_length:
            raise Conflict(f"Поле {field_name} слишком длинное")
        return normalized

    def _normalize_optional_text(self, value: str | None, *, max_length: int | None = None) -> str | None:
        normalized = (value or "").strip()
        if not normalized:
            return None
        if max_length is not None and len(normalized) > max_length:
            raise Conflict("Значение слишком длинное")
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
                raise Conflict("Не удалось сгенерировать уникальный логин для ручного контрагента")

    async def _find_existing_manual_contractor_user_id(
        self,
        *,
        data: ManualContractorCreateInput,
    ) -> str | None:
        matched_user_ids = await self._users.find_matching_contractor_user_ids(
            contractor_role_id=settings.contractor_role_id,
            email=data.company_mail,
            inn=data.inn,
            company_name=data.company_name,
        )
        if not matched_user_ids:
            return None
        if len(matched_user_ids) > 1:
            raise Conflict("Найдено несколько похожих контрагентов. Уточните данные и повторите попытку.")
        return matched_user_ids[0]

    async def _resolve_creator_root_unit_ids(self, *, current_user: CurrentUser) -> set[int]:
        if self._units is None:
            return set()
        return await self._contractor_unit_service().list_effective_root_unit_ids_for_user(user_id=current_user.user_id)

    async def _bind_to_creator_root_units_if_needed(
        self,
        *,
        current_user: CurrentUser,
        contractor_user_id: str,
    ) -> None:
        if self._units is None or current_user.role_id == settings.contractor_role_id:
            return
        creator_root_unit_ids = await self._resolve_creator_root_unit_ids(current_user=current_user)
        if not creator_root_unit_ids:
            return
        await self._contractor_unit_service().bind_user_to_root_units(
            user_id=contractor_user_id,
            root_unit_ids=creator_root_unit_ids,
            assigned_by_user_id=current_user.user_id,
        )

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
        if self._user_contact_channels is not None and data.company_mail:
            await self._user_contact_channels.upsert_channel(
                user_id=login,
                channel_type="email",
                channel_value=data.company_mail.strip().lower(),
                is_verified=False,
                is_primary=True,
            )
        return login

    async def create_manual_contractor(
        self,
        *,
        current_user: CurrentUser,
        data: ManualContractorCreateInput,
    ) -> ManualContractorCreateResult:
        UserPolicy.ensure_can_create_manual_contractors(current_user)

        normalized_data = self._validate_manual_contractor_create_data(data=data)
        existing_contractor_user_id = await self._find_existing_manual_contractor_user_id(
            data=normalized_data,
        )
        if existing_contractor_user_id is not None:
            await self._bind_to_creator_root_units_if_needed(
                current_user=current_user,
                contractor_user_id=existing_contractor_user_id,
            )
            return ManualContractorCreateResult(
                user_id=existing_contractor_user_id,
                created=False,
                # These are the normalized values submitted by the actor, not
                # additional fields read from the existing contractor profile.
                company_name=normalized_data.company_name,
                inn=normalized_data.inn,
                company_mail=normalized_data.company_mail,
            )

        login = await self._create_manual_contractor(data=normalized_data)
        await self._bind_to_creator_root_units_if_needed(
            current_user=current_user,
            contractor_user_id=login,
        )
        return ManualContractorCreateResult(
            user_id=login,
            created=True,
            company_name=normalized_data.company_name,
            inn=normalized_data.inn,
            company_mail=normalized_data.company_mail,
        )

    async def list_possible_duplicates(
        self,
        *,
        current_user: CurrentUser,
        company_name: str | None = None,
        inn: str | None = None,
        company_mail: str | None = None,
    ) -> list[ManualContractorDuplicateItem]:
        UserPolicy.ensure_can_create_manual_contractors(current_user)

        search_values = [
            value.strip()
            for value in (company_name, inn, company_mail)
            if value is not None and value.strip()
        ]
        search_values = [value for value in search_values if len(value) >= 2]
        if not search_values:
            return []

        normalized_name = (company_name or '').strip().lower()
        normalized_inn = (inn or '').strip().lower()
        normalized_mail = (company_mail or '').strip().lower()
        items: dict[str, ManualContractorDuplicateItem] = {}
        for search_value in search_values:
            rows, _ = await self._users.list_contractors_page(
                contractor_role_id=settings.contractor_role_id,
                search=search_value,
                sort_by='created_at',
                sort_order='desc',
                limit=50,
                offset=0,
            )
            for user, profile, company, _legacy_user, _legacy_account_id in rows:
                company_name_value = (company.company_name if company else None) or ''
                inn_value = (company.inn if company else None) or ''
                company_mail_value = (company.mail if company else None) or ''
                if not any(
                    candidate and candidate in source
                    for candidate, source in (
                        (normalized_name, company_name_value.lower()),
                        (normalized_inn, inn_value.lower()),
                        (normalized_mail, company_mail_value.lower()),
                    )
                ):
                    continue
                if self._units is not None and not await self._contractor_unit_service().can_access_contractor(
                    current_user=current_user,
                    contractor_user_id=user.id,
                ):
                    continue
                items[user.id] = ManualContractorDuplicateItem(
                    user_id=user.id,
                    full_name=profile.full_name if profile else None,
                    phone=profile.phone if profile else None,
                    mail=profile.mail if profile else None,
                    company_name=company.company_name if company else None,
                    inn=company.inn if company else None,
                    company_phone=company.phone if company else None,
                    company_mail=company.mail if company else None,
                    address=company.address if company else None,
                    note=company.note if company else None,
                    status=user.status,
                    created_at=str(user.created_at) if user.created_at is not None else None,
                    updated_at=str(user.updated_at) if user.updated_at is not None else None,
                )

        return sorted(
            items.values(),
            key=lambda item: ((item.company_name or '').lower(), item.user_id),
        )

    def _normalize_value(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise Conflict("Обновляемое значение не может быть пустым")
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
            raise NotFound("Пользователь не найден")
        if user.id_role != settings.contractor_role_id:
            raise Conflict("Через этот endpoint можно обновлять только контрагента")
        if await self._users.has_legacy_messenger_account(user_id=user.id):
            raise Conflict("Через этот endpoint можно обновлять только вручную созданного контрагента")

        profile = await self._profiles.get_by_id(user.id)
        if profile is None:
            raise NotFound("Профиль не найден")

        company_contact = await self._company_contacts.get_by_id(user.id)

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

        if company_contact is None:
            company_contact = CompanyContact(
                id=user.id,
                company_name=company_name or PLACEHOLDER_TEXT,
                inn=inn or PLACEHOLDER_TEXT,
                phone=company_phone or PLACEHOLDER_TEXT,
                mail=company_mail or PLACEHOLDER_TEXT,
                address=address or PLACEHOLDER_TEXT,
                note=note or PLACEHOLDER_TEXT,
            )
            await self._company_contacts.add(company_contact)
        else:
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

        return user.id


class UserRoleService:
    def __init__(
        self,
        users: UserRepository,
        user_auth_accounts: UserAuthAccountRepository,
        units: UnitRepository | None = None,
    ):
        self._users = users
        self._user_auth_accounts = user_auth_accounts
        self._units = units

    async def _ensure_target_root_scope(
        self,
        *,
        current_user: CurrentUser,
        target_user_id: str,
    ) -> None:
        """Role permissions are never a substitute for organizational scope."""
        if current_user.role_id == settings.superadmin_role_id or self._units is None:
            return
        scope = ContractorUnitService(users=self._users, units=self._units)
        actor_root_ids = await scope.list_effective_root_unit_ids_for_user(user_id=current_user.user_id)
        target_root_ids = await scope.list_effective_root_unit_ids_for_user(user_id=target_user_id)
        if not actor_root_ids or not target_root_ids or not (actor_root_ids & target_root_ids):
            raise Forbidden("Пользователь находится вне разрешенной зоны управления")

    async def update_role(
        self,
        *,
        current_user: CurrentUser,
        user_id: str,
        role_id: int,
    ) -> UserRoleUpdateResult:
        UserPolicy.ensure_can_update_user_role(current_user)

        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFound("Пользователь не найден")

        if user.id_role == settings.superadmin_role_id:
            raise Forbidden("Роль суперадминистратора нельзя изменить")

        allowed_role_ids = _role_update_options_for_user(current_user)
        if role_id not in allowed_role_ids:
            raise Forbidden("Выбранная роль недоступна для назначения")

        await self._ensure_target_root_scope(
            current_user=current_user,
            target_user_id=user.id,
        )

        has_role_update_any = has_permission(current_user, PermissionCodes.USERS_ROLE_UPDATE_ANY)
        if not has_role_update_any and has_permission(current_user, PermissionCodes.USERS_ROLE_UPDATE_ECONOMY):
            if user.id == current_user.user_id:
                raise Forbidden("Вы можете обновлять роль только своих подчиненных")
            if not UserPolicy.can_manage_subordinate_role(
                current_role_id=current_user.role_id,
                target_role_id=user.id_role,
            ):
                raise Forbidden("Вы можете обновлять роль только для разрешенных ролей подчиненных")
            is_subordinate = await _is_descendant_user(
                self._users,
                ancestor_user_id=current_user.user_id,
                target_user_id=user.id,
            )
            if not is_subordinate:
                raise Forbidden("Вы можете обновлять роль только своих подчиненных")

        role_rule = _hierarchy_rule_for_role(role_id=role_id)
        if not role_rule.parent_allowed:
            await self._users.update_parent(user, None)
        elif user.id_parent is not None:
            manager_user = await self._users.get_by_id(user.id_parent)
            if manager_user is None:
                raise Conflict("Текущий руководитель пользователя не найден")
            if manager_user.id_role not in role_rule.allowed_parent_role_ids:
                raise Conflict("Текущий руководитель несовместим с выбранной ролью")

        await self._users.update_role(user, role_id)

        return UserRoleUpdateResult(user_id=user.id, role_id=user.id_role)


class UserManagerService:
    """Legacy service: updates users.id_parent. Business scope uses unit hierarchy."""

    def __init__(self, users: UserRepository):
        self._users = users

    async def update_manager(
        self,
        *,
        current_user: CurrentUser,
        user_id: str,
        manager_user_id: str | None,
    ) -> UserManagerUpdateResult:
        UserPolicy.ensure_can_update_user_manager(current_user)

        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFound("Пользователь не найден")

        if not UserPolicy.can_manage_subordinate_role(
            current_role_id=current_user.role_id,
            target_role_id=user.id_role,
        ):
            raise Forbidden("Вы можете обновлять руководителя только для разрешенных ролей подчиненных")

        if user.id == current_user.user_id:
            raise Forbidden("Вы можете обновлять руководителя только своих подчиненных")

        is_subordinate = await _is_descendant_user(
            self._users,
            ancestor_user_id=current_user.user_id,
            target_user_id=user.id,
        )
        if not is_subordinate:
            raise Forbidden("Вы можете обновлять руководителя только своих подчиненных")

        role_rule = _hierarchy_rule_for_role(role_id=user.id_role)
        if not role_rule.parent_allowed:
            raise Conflict(_manager_disallowed_error(role_id=user.id_role))

        if manager_user_id is None:
            # legacy only: users.id_parent is not used for business access checks
            await self._users.update_parent(user, None)
            return UserManagerUpdateResult(user_id=user.id, manager_user_id=None)

        manager_user = await self._users.get_by_id(manager_user_id)
        if manager_user is None:
            raise NotFound("Руководитель не найден")
        if manager_user.id == user.id:
            raise Conflict("Пользователь не может быть руководителем самого себя")
        if manager_user.id_role not in role_rule.allowed_parent_role_ids:
            raise Conflict("Выбранная роль руководителя недопустима для этого пользователя")

        candidate_query = UserQueryService(
            self._users,
            UserStatusPeriodRepository(self._users._session),
        )
        allowed_manager_ids = {
            item.user_id
            for item in await candidate_query.list_manager_candidates(
                current_user=current_user,
                target_role_id=user.id_role,
                target_user_id=user.id,
            )
        }
        if manager_user.id not in allowed_manager_ids:
            raise Forbidden("Выбранный руководитель вне разрешенной зоны управления")

        # legacy only: users.id_parent is not used for business access checks
        await self._users.update_parent(user, manager_user.id)
        return UserManagerUpdateResult(user_id=user.id, manager_user_id=manager_user.id)


class UserStatusService:
    VALID_USER_STATUSES = {"active", "inactive", "review", "blacklist"}

    def __init__(
        self,
        users: UserRepository,
        profiles: ProfileRepository,
        user_auth_accounts: UserAuthAccountRepository | None = None,
        user_contact_channels=None,
        notification_preferences: UserNotificationPreferencesService | None = None,
        after_commit_hook_registrar: Callable[[Callable[[], Awaitable[None]]], None] | None = None,
        process_event_publisher: Callable[[ProcessNotificationEvent], Awaitable[bool]] | None = None,
    ):
        self._users = users
        self._profiles = profiles
        self._user_auth_accounts = user_auth_accounts
        self._user_contact_channels = user_contact_channels
        self._notification_preferences = notification_preferences
        self._after_commit_hook_registrar = after_commit_hook_registrar
        self._process_event_publisher = process_event_publisher or publish_process_notification_event

    def _schedule_process_notification_event(self, event: ProcessNotificationEvent) -> bool:
        if self._after_commit_hook_registrar is None:
            return False
        self._after_commit_hook_registrar(
            lambda: self._process_event_publisher(event)
        )
        return True

    async def update_statuses(
        self,
        *,
        current_user: CurrentUser,
        user_id: str,
        user_status: str,
        contractor_only: bool = False,
    ) -> UserStatusUpdateResult:
        if contractor_only:
            UserPolicy.ensure_can_update_contractor_profile_status(current_user)
        else:
            UserPolicy.ensure_can_update_user_status(current_user)

        if user_status not in self.VALID_USER_STATUSES:
            raise Conflict("Неподдерживаемое значение users.status")

        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFound("Пользователь не найден")

        if contractor_only:
            if user.id_role != settings.contractor_role_id:
                raise Forbidden("Изменение статуса доступно только для контрагентов")
        elif current_user.role_id in {
            settings.project_manager_role_id,
            settings.lead_economist_role_id,
            settings.economist_role_id,
        }:
            if not UserPolicy.can_manage_subordinate_role(
                current_role_id=current_user.role_id,
                target_role_id=user.id_role,
            ):
                raise Forbidden("Вы можете обновлять статус только для разрешенных ролей подчиненных")
            if user.id == current_user.user_id:
                raise Forbidden("Вы можете обновлять статус только своих подчиненных")
            is_subordinate = await _is_descendant_user(
                self._users,
                ancestor_user_id=current_user.user_id,
                target_user_id=user.id,
            )
            if not is_subordinate:
                raise Forbidden("Вы можете обновлять статус только своих подчиненных")

        old_status = user.status
        if old_status == "review" and user_status == "active":
            UserPolicy.ensure_can_approve_registration(current_user)
            channel = None
            if self._user_contact_channels is not None:
                channel = await self._user_contact_channels.get_primary_by_type(
                    user_id=user.id,
                    channel_type="email",
                )
            if channel is None or not channel.is_verified:
                raise Conflict("Нельзя подтвердить регистрацию до подтверждения email")
        status_changed = old_status != user_status
        await self._users.update_status(user, user_status)

        result = UserStatusUpdateResult(
            user_id=user.id,
            user_status=user.status,
        )

        notify_email: str | None = None
        contractor_email_notification_queued = False
        contractor_email_notification_reason: str | None = None
        if user.id_role == settings.contractor_role_id:
            profile = await self._profiles.get_by_id(user.id)
            notify_email = _normalize_notification_email(profile.mail if profile is not None else None)

        if status_changed and user.id_role == settings.contractor_role_id:
            if notify_email is None:
                contractor_email_notification_reason = "missing_email"
            else:
                email_system_enabled = True
                if self._notification_preferences is not None:
                    email_system_enabled = await self._notification_preferences.is_channel_enabled(
                        user_id=user.id,
                        channel_type="email",
                        notification_type="system",
                    )
                if not email_system_enabled:
                    contractor_email_notification_reason = "disabled_by_user"
                else:
                    contractor_email_notification_queued = await notify_contractor_status_changed_email(
                        to_email=notify_email,
                        user_status=user.status,
                        recipient_user_id=user.id,
                        initiator_user_id=current_user.user_id,
                    )
                    if not contractor_email_notification_queued:
                        contractor_email_notification_reason = "status_not_supported_for_email"

        if status_changed:
            event = build_process_notification_event(
                event_type="user.status_changed",
                actor_user_id=current_user.user_id,
                entity_type="user",
                entity_id=user.id,
                dedupe_key=f"user.status_changed:{user.id}:{old_status}:{user.status}",
                payload={
                    "target_user_id": user.id,
                    "old_status": old_status,
                    "new_status": user.status,
                    "target_role": user.id_role,
                    "target_is_contractor": user.id_role == settings.contractor_role_id,
                    "target_user_email": notify_email,
                    "actor_user_id": current_user.user_id,
                    "email_notification_queued": contractor_email_notification_queued,
                    "email_notification_reason": contractor_email_notification_reason,
                },
            )
            self._schedule_process_notification_event(event)
            # user.status_changed already notifies admins about the transition to
            # "review" with full context (who changed, old→new).  Firing a second
            # user.review_required event from this code path would produce a
            # duplicate ping for the same admin recipients.  New-registration
            # paths call registration_admin_notify which issues user.review_required
            # independently and is NOT suppressed here.

        return result
    
class UserSelfService:
    VALID_UNAVAILABILITY_STATUSES = {"sick", "vacation", "fired", "maternity", "business_trip", "unavailable"}

    def __init__(
        self,
        users: UserRepository,
        profiles: ProfileRepository,
        company_contacts: CompanyContactRepository,
        user_status_periods: UserStatusPeriodRepository,
        user_auth_accounts: UserAuthAccountRepository | None = None,
        user_contact_channels=None,
    ):
        self._users = users
        self._profiles = profiles
        self._company_contacts = company_contacts
        self._user_status_periods = user_status_periods
        self._user_auth_accounts = user_auth_accounts
        self._user_contact_channels = user_contact_channels

    async def _ensure_accessible_subordinate(
        self,
        *,
        current_user: CurrentUser,
        subordinate: User,
    ) -> None:
        if subordinate.id_role not in SUBORDINATE_PROFILE_ROLE_IDS:
            raise Conflict("Данными подчиненного можно управлять только для разрешенных ролей подчиненных")
        if not UserPolicy.can_manage_subordinate_role(
            current_role_id=current_user.role_id,
            target_role_id=subordinate.id_role,
        ):
            raise Conflict("Данными подчиненного можно управлять только для разрешенных ролей подчиненных")
        if subordinate.id == current_user.user_id:
            raise Forbidden("Вы можете управлять данными только своих подчиненных")
        if has_permission(current_user, PermissionCodes.UNAVAILABILITY_MANAGE_ALL):
            return
        is_subordinate = await _is_descendant_user(
            self._users,
            ancestor_user_id=current_user.user_id,
            target_user_id=subordinate.id,
        )
        if not is_subordinate:
            raise Forbidden("Вы можете управлять данными только своих подчиненных")

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
                "У пользователя уже есть период недоступности в этом диапазоне времени "
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
                    "У пользователя уже есть период недоступности в этом диапазоне времени "
                    f"{period.started_at.isoformat()} - {period.ended_at.isoformat()}"
                )

    async def _apply_my_profile_update(
        self,
        *,
        user_id: str,
        full_name: str | None,
        phone: str | None,
        mail: str | None,
    ) -> None:
        profile = await self._profiles.get_by_id(user_id)
        if profile is None:
            profile = Profile(
                id=user_id,
                full_name=full_name or "Не указано",
                phone=phone or "Не указано",
                mail=mail or "Не указано",
            )
            await self._profiles.add(profile)
        else:
            if full_name is not None:
                profile.full_name = full_name
            if phone is not None:
                profile.phone = phone
            if mail is not None:
                profile.mail = mail
        if mail is not None and self._user_contact_channels is not None:
            normalized_mail = mail.strip().lower()
            if normalized_mail and normalized_mail not in {"не указано", "none", "null"}:
                await self._user_contact_channels.upsert_channel(
                    user_id=user_id,
                    channel_type="email",
                    channel_value=normalized_mail,
                    is_verified=False,
                    is_primary=True,
                )


    async def update_my_profile(
        self,
        current_user: CurrentUser,
        *,
        full_name: str | None,
        phone: str | None,
        mail: str | None,
    ) -> None:
        UserPolicy.ensure_can_manage_own_profile(current_user)
        await self._apply_my_profile_update(
            user_id=current_user.user_id,
            full_name=full_name,
            phone=phone,
            mail=mail,
        )

    async def update_my_profile_for_review_onboarding(
        self,
        current_user: CurrentUser,
        *,
        full_name: str | None,
        phone: str | None,
        mail: str | None,
    ) -> None:
        UserPolicy.ensure_can_manage_review_onboarding(current_user)
        previous_email = None
        if mail is not None and self._user_contact_channels is not None:
            channel = await self._user_contact_channels.get_primary_by_type(
                user_id=current_user.user_id,
                channel_type="email",
            )
            if channel is not None:
                previous_email = (channel.channel_value or "").strip().lower()
        await self._apply_my_profile_update(
            user_id=current_user.user_id,
            full_name=full_name,
            phone=phone,
            mail=mail,
        )
        if current_user.onboarding_state == "first_login":
            await IamClient().complete_required_action(account_id=current_user.iam_account_id)
            normalized_mail = (mail or "").strip().lower()
            if (
                normalized_mail
                and normalized_mail not in {"не указано", "none", "null"}
                and normalized_mail != previous_email
            ):
                from app.services.email_verification import EmailVerificationService, PROFILE_CHANGE_PURPOSE

                await EmailVerificationService(
                    self._profiles,
                    self._user_contact_channels,
                    user_auth_accounts=self._user_auth_accounts,
                ).request_profile_verification(
                    user_id=current_user.user_id,
                    email=normalized_mail,
                    purpose=PROFILE_CHANGE_PURPOSE,
                    account_id=current_user.iam_account_id,
                )

    async def _apply_my_company_contacts_update(
        self,
        *,
        user_id: str,
        company_name: str | None,
        inn: str | None,
        company_phone: str | None,
        company_mail: str | None,
        address: str | None,
        note: str | None,
    ) -> None:
        company_contacts = await self._company_contacts.get_by_id(user_id)
        if company_contacts is None:
            if company_name is None or inn is None:
                raise NotFound("Контакты компании не найдены")
            await self._company_contacts.add(
                CompanyContact(
                    id=user_id,
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
        await self._apply_my_company_contacts_update(
            user_id=current_user.user_id,
            company_name=company_name,
            inn=inn,
            company_phone=company_phone,
            company_mail=company_mail,
            address=address,
            note=note,
        )

    async def update_my_company_contacts_for_review_onboarding(
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
        UserPolicy.ensure_can_manage_review_onboarding(current_user)
        await self._apply_my_company_contacts_update(
            user_id=current_user.user_id,
            company_name=company_name,
            inn=inn,
            company_phone=company_phone,
            company_mail=company_mail,
            address=address,
            note=note,
        )

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
            raise Conflict("Неподдерживаемое значение user_status_periods.status")

        normalized_started_at = _normalize_db_timestamp(started_at)
        normalized_ended_at = _normalize_db_timestamp(ended_at)

        if normalized_ended_at < normalized_started_at:
            raise Conflict("Дата окончания периода должна быть больше или равна дате начала")

        subordinate = await self._users.get_by_id(subordinate_user_id)
        if subordinate is None:
            raise NotFound("Пользователь не найден")

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
            raise Conflict("Неподдерживаемое значение user_status_periods.status")

        normalized_started_at = _normalize_db_timestamp(started_at)
        normalized_ended_at = _normalize_db_timestamp(ended_at)

        if normalized_ended_at < normalized_started_at:
            raise Conflict("Дата окончания периода должна быть больше или равна дате начала")

        user = await self._users.get_by_id(current_user.user_id)
        if user is None:
            raise NotFound("Пользователь не найден")

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
