from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.contractor_delegations import (
    CONTRACTOR_DELEGATIONS,
    CONTRACTOR_DELEGATION_ROLE_TO_PERMISSIONS,
    get_contractor_delegation_permission_codes,
    get_contractor_delegation_role_codes,
)
from app.domain.exceptions import Conflict, Forbidden, NotFound
from app.infrastructure.iam_client import IamAccountPermissions
from app.repositories.profiles import ProfileRepository
from app.repositories.user_auth_accounts import UserAuthAccountRepository
from app.repositories.users import UserRepository
from app.services.iam_permission_grants import IamPermissionGrantsService


@dataclass(frozen=True, slots=True)
class ContractorDelegationAccessState:
    code: str
    label: str
    description: str
    enabled: bool
    granted_via_role: bool
    granted_individually: bool


@dataclass(frozen=True, slots=True)
class ContractorDelegationUserState:
    user_id: str
    role_id: int
    full_name: str | None
    can_manage: bool
    accesses: tuple[ContractorDelegationAccessState, ...]
    token_refresh_required: bool
    warning: str | None


class UserContractorDelegationsService:
    def __init__(
        self,
        *,
        users: UserRepository,
        profiles: ProfileRepository,
        user_auth_accounts: UserAuthAccountRepository,
        iam_permission_grants: IamPermissionGrantsService | None = None,
    ) -> None:
        self._users = users
        self._profiles = profiles
        self._user_auth_accounts = user_auth_accounts
        self._iam_permission_grants = iam_permission_grants or IamPermissionGrantsService()

    async def get_state(
        self,
        *,
        current_user: CurrentUser,
        target_user_id: str,
    ) -> ContractorDelegationUserState:
        target_user = await self._users.get_by_id(target_user_id)
        if target_user is None:
            raise NotFound("User not found")

        can_manage = self._resolve_can_manage_target(
            current_user=current_user,
            target_role_id=target_user.id_role,
        )
        iam_account_id = await self._get_iam_account_id_for_user(user_id=target_user.id)

        permissions = IamAccountPermissions(frozenset(), frozenset(), frozenset())
        warning: str | None = None
        if iam_account_id is None:
            warning = "У пользователя отсутствует активная привязка IAM"
        else:
            permissions = await self._iam_permission_grants.get(
                account_id=iam_account_id,
            )

        profile = await self._profiles.get_by_id(target_user.id)
        return ContractorDelegationUserState(
            user_id=target_user.id,
            role_id=target_user.id_role,
            full_name=profile.full_name if profile is not None else None,
            can_manage=can_manage,
            accesses=self._build_accesses(permissions=permissions),
            token_refresh_required=False,
            warning=warning,
        )

    async def update_state(
        self,
        *,
        current_user: CurrentUser,
        target_user_id: str,
        requested_access_codes: list[str],
    ) -> ContractorDelegationUserState:
        target_user = await self._users.get_by_id(target_user_id)
        if target_user is None:
            raise NotFound("User not found")

        can_manage = self._resolve_can_manage_target(
            current_user=current_user,
            target_role_id=target_user.id_role,
        )
        if not can_manage:
            raise Forbidden("Insufficient permissions to manage contractor delegations")

        iam_account_id = await self._get_iam_account_id_for_user(user_id=target_user.id)
        if iam_account_id is None:
            raise Conflict("У пользователя отсутствует активная привязка IAM")

        normalized_requested = self._normalize_requested_codes(requested_access_codes)
        requested_permissions = frozenset(
            permission
            for role_code in normalized_requested
            for permission in CONTRACTOR_DELEGATION_ROLE_TO_PERMISSIONS[role_code]
        )
        sync_result = await self._iam_permission_grants.replace_managed_grants(
            account_id=iam_account_id,
            managed_permissions=get_contractor_delegation_permission_codes(),
            requested_permissions=requested_permissions,
        )
        profile = await self._profiles.get_by_id(target_user.id)
        return ContractorDelegationUserState(
            user_id=target_user.id,
            role_id=target_user.id_role,
            full_name=profile.full_name if profile is not None else None,
            can_manage=can_manage,
            accesses=self._build_accesses(permissions=sync_result.permissions),
            token_refresh_required=sync_result.changed,
            warning=(
                "Дополнительные доступы изменены. Новые права появятся после обновления сессии."
                if sync_result.changed
                else None
            ),
        )

    def _resolve_can_manage_target(
        self,
        *,
        current_user: CurrentUser,
        target_role_id: int,
    ) -> bool:
        if current_user.role_id not in {settings.superadmin_role_id, settings.admin_role_id}:
            return False
        return target_role_id == settings.lead_economist_role_id

    async def _get_iam_account_id_for_user(self, *, user_id: str) -> str | None:
        account = await self._user_auth_accounts.get_by_user_provider(
            user_id=user_id,
            provider="iam",
            include_inactive=False,
        )
        if account is None:
            return None
        normalized_subject = (account.external_subject_id or "").strip()
        return normalized_subject or None

    def _normalize_requested_codes(self, access_codes: list[str]) -> set[str]:
        allowed_codes = get_contractor_delegation_role_codes()
        normalized = {
            code.strip()
            for code in access_codes
            if isinstance(code, str) and code.strip()
        }
        unknown = sorted(normalized - allowed_codes)
        if unknown:
            raise Conflict(f"Unsupported delegation role code(s): {', '.join(unknown)}")
        return normalized

    def _build_accesses(
        self,
        *,
        permissions: IamAccountPermissions,
    ) -> tuple[ContractorDelegationAccessState, ...]:
        return tuple(
            ContractorDelegationAccessState(
                code=definition.role_code,
                label=definition.label,
                description=definition.description,
                enabled=definition.permission_codes.issubset(
                    permissions.effective_permissions
                ),
                granted_via_role=bool(
                    definition.permission_codes & permissions.permissions_from_role
                ),
                granted_individually=bool(
                    definition.permission_codes
                    & permissions.individually_granted_permissions
                ),
            )
            for definition in CONTRACTOR_DELEGATIONS
        )
