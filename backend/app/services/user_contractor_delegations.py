from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.contractor_delegations import CONTRACTOR_DELEGATIONS, get_contractor_delegation_role_codes
from app.domain.exceptions import Conflict, Forbidden, NotFound
from app.repositories.profiles import ProfileRepository
from app.repositories.user_auth_accounts import UserAuthAccountRepository
from app.repositories.users import UserRepository
from app.services.keycloak_admin import KeycloakAdminService
from app.services.keycloak_delegations import KeycloakContractorDelegationsService


@dataclass(frozen=True, slots=True)
class ContractorDelegationAccessState:
    code: str
    label: str
    description: str
    enabled: bool


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
        keycloak_delegations: KeycloakContractorDelegationsService | None = None,
        keycloak_admin: KeycloakAdminService | None = None,
    ) -> None:
        self._users = users
        self._profiles = profiles
        self._user_auth_accounts = user_auth_accounts
        self._keycloak_delegations = keycloak_delegations or KeycloakContractorDelegationsService()
        self._keycloak_admin = keycloak_admin or KeycloakAdminService()

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
        keycloak_subject = await self._get_keycloak_subject_for_user(user_id=target_user.id)

        enabled_role_codes: frozenset[str] = frozenset()
        warning: str | None = None
        if keycloak_subject is None:
            warning = "User does not have an active Keycloak account link"
        else:
            enabled_role_codes = await self._keycloak_delegations.list_user_enabled_contractor_role_codes(
                keycloak_user_id=keycloak_subject,
            )

        profile = await self._profiles.get_by_id(target_user.id)
        return ContractorDelegationUserState(
            user_id=target_user.id,
            role_id=target_user.id_role,
            full_name=profile.full_name if profile is not None else None,
            can_manage=can_manage,
            accesses=self._build_accesses(enabled_role_codes=enabled_role_codes),
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

        keycloak_subject = await self._get_keycloak_subject_for_user(user_id=target_user.id)
        if keycloak_subject is None:
            raise Conflict("User does not have an active Keycloak account link")

        normalized_requested = self._normalize_requested_codes(requested_access_codes)
        sync_result = await self._keycloak_delegations.sync_user_contractor_role_codes(
            keycloak_user_id=keycloak_subject,
            requested_role_codes=normalized_requested,
        )

        token_refresh_required = False
        warning: str | None = None
        if sync_result.added_role_codes or sync_result.removed_role_codes:
            try:
                await self._keycloak_admin.logout_user_sessions(user_id=keycloak_subject)
            except Exception:  # noqa: BLE001
                token_refresh_required = True
                warning = "Delegations changed. User must refresh token or re-login."

        enabled_role_codes = await self._keycloak_delegations.list_user_enabled_contractor_role_codes(
            keycloak_user_id=keycloak_subject,
        )
        profile = await self._profiles.get_by_id(target_user.id)
        return ContractorDelegationUserState(
            user_id=target_user.id,
            role_id=target_user.id_role,
            full_name=profile.full_name if profile is not None else None,
            can_manage=can_manage,
            accesses=self._build_accesses(enabled_role_codes=enabled_role_codes),
            token_refresh_required=token_refresh_required,
            warning=warning,
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

    async def _get_keycloak_subject_for_user(self, *, user_id: str) -> str | None:
        account = await self._user_auth_accounts.get_by_user_provider(
            user_id=user_id,
            provider="keycloak",
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

    def _build_accesses(self, *, enabled_role_codes: frozenset[str]) -> tuple[ContractorDelegationAccessState, ...]:
        return tuple(
            ContractorDelegationAccessState(
                code=definition.role_code,
                label=definition.label,
                description=definition.description,
                enabled=definition.role_code in enabled_role_codes,
            )
            for definition in CONTRACTOR_DELEGATIONS
        )
