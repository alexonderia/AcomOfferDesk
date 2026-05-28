from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import settings
from app.domain.department_delegations import (
    DEPARTMENT_DELEGATION_ROLE_TO_PERMISSION,
    get_department_delegation_role_codes,
)
from app.domain.exceptions import Conflict
from app.services.keycloak_admin import KeycloakAdminService


@dataclass(frozen=True, slots=True)
class KeycloakDepartmentDelegationSyncResult:
    enabled_role_codes: frozenset[str]
    added_role_codes: frozenset[str]
    removed_role_codes: frozenset[str]


class KeycloakDepartmentDelegationsService:
    def __init__(self, keycloak_admin: KeycloakAdminService | None = None):
        self._keycloak_admin = keycloak_admin or KeycloakAdminService()

    async def list_available_department_role_payloads(self) -> dict[str, dict[str, Any]]:
        admin_token = await self._keycloak_admin.get_admin_token()
        api_client_uuid = await self._keycloak_admin.get_client_uuid_by_client_id(
            client_id=settings.keycloak_api_client_id,
            admin_token=admin_token,
        )
        return await self._load_available_role_payloads(
            api_client_uuid=api_client_uuid,
            admin_token=admin_token,
        )

    async def _load_available_role_payloads(
        self,
        *,
        api_client_uuid: str,
        admin_token: str,
    ) -> dict[str, dict[str, Any]]:
        payloads: dict[str, dict[str, Any]] = {}
        for role_code in sorted(get_department_delegation_role_codes()):
            role_payload = await self._keycloak_admin.get_client_role_by_name(
                client_uuid=api_client_uuid,
                role_name=role_code,
                admin_token=admin_token,
            )
            if role_payload is None:
                raise Conflict(f"Missing Keycloak role '{role_code}' in API client")
            payloads[role_code] = role_payload
        return payloads

    async def list_user_enabled_department_role_codes(self, *, keycloak_user_id: str) -> frozenset[str]:
        admin_token = await self._keycloak_admin.get_admin_token()
        api_client_uuid = await self._keycloak_admin.get_client_uuid_by_client_id(
            client_id=settings.keycloak_api_client_id,
            admin_token=admin_token,
        )
        current_roles = await self._keycloak_admin.get_user_client_role_mappings(
            keycloak_user_id=keycloak_user_id,
            client_uuid=api_client_uuid,
            admin_token=admin_token,
        )
        if current_roles is None:
            return frozenset()
        allowed_codes = get_department_delegation_role_codes()
        return frozenset(
            str(role_payload.get("name") or "").strip()
            for role_payload in current_roles
            if str(role_payload.get("name") or "").strip() in allowed_codes
        )

    async def sync_user_department_role_codes(
        self,
        *,
        keycloak_user_id: str,
        requested_role_codes: set[str] | frozenset[str],
    ) -> KeycloakDepartmentDelegationSyncResult:
        allowed_codes = get_department_delegation_role_codes()
        normalized_requested = {
            role_code.strip()
            for role_code in requested_role_codes
            if isinstance(role_code, str) and role_code.strip()
        }
        unknown_codes = sorted(normalized_requested - allowed_codes)
        if unknown_codes:
            raise Conflict(f"Unsupported delegation role code(s): {', '.join(unknown_codes)}")

        admin_token = await self._keycloak_admin.get_admin_token()
        api_client_uuid = await self._keycloak_admin.get_client_uuid_by_client_id(
            client_id=settings.keycloak_api_client_id,
            admin_token=admin_token,
        )
        available_payloads = await self._load_available_role_payloads(
            api_client_uuid=api_client_uuid,
            admin_token=admin_token,
        )

        current_roles = await self._keycloak_admin.get_user_client_role_mappings(
            keycloak_user_id=keycloak_user_id,
            client_uuid=api_client_uuid,
            admin_token=admin_token,
        )
        if current_roles is None:
            raise Conflict("Unable to query Keycloak user role mappings")

        current_department_payloads_by_code = {
            str(role_payload.get("name") or "").strip(): role_payload
            for role_payload in current_roles
            if str(role_payload.get("name") or "").strip() in allowed_codes
        }
        current_codes = set(current_department_payloads_by_code.keys())

        codes_to_add = normalized_requested - current_codes
        codes_to_remove = current_codes - normalized_requested

        if codes_to_remove:
            await self._keycloak_admin.remove_user_client_roles(
                keycloak_user_id=keycloak_user_id,
                client_uuid=api_client_uuid,
                roles=[current_department_payloads_by_code[code] for code in sorted(codes_to_remove)],
                admin_token=admin_token,
            )

        if codes_to_add:
            await self._keycloak_admin.add_user_client_roles(
                keycloak_user_id=keycloak_user_id,
                client_uuid=api_client_uuid,
                roles=[available_payloads[code] for code in sorted(codes_to_add)],
                admin_token=admin_token,
            )

        # Hard guarantee for checklist-save flow:
        # keep department.* atomics in sync with delegation.department.* regardless of
        # temporary Keycloak composite drift.
        requested_permission_codes = {
            DEPARTMENT_DELEGATION_ROLE_TO_PERMISSION[role_code]
            for role_code in normalized_requested
        }
        available_permission_payloads = await self._load_permission_role_payloads(
            api_client_uuid=api_client_uuid,
            admin_token=admin_token,
            permission_codes=requested_permission_codes
            | {DEPARTMENT_DELEGATION_ROLE_TO_PERMISSION[role_code] for role_code in current_codes},
        )
        current_department_permission_payloads_by_code = {
            str(role_payload.get("name") or "").strip(): role_payload
            for role_payload in current_roles
            if str(role_payload.get("name") or "").strip() in available_permission_payloads
        }
        current_permission_codes = set(current_department_permission_payloads_by_code.keys())
        permission_codes_to_add = requested_permission_codes - current_permission_codes
        permission_codes_to_remove = current_permission_codes - requested_permission_codes

        if permission_codes_to_remove:
            await self._keycloak_admin.remove_user_client_roles(
                keycloak_user_id=keycloak_user_id,
                client_uuid=api_client_uuid,
                roles=[
                    current_department_permission_payloads_by_code[code]
                    for code in sorted(permission_codes_to_remove)
                ],
                admin_token=admin_token,
            )

        if permission_codes_to_add:
            await self._keycloak_admin.add_user_client_roles(
                keycloak_user_id=keycloak_user_id,
                client_uuid=api_client_uuid,
                roles=[available_permission_payloads[code] for code in sorted(permission_codes_to_add)],
                admin_token=admin_token,
            )

        return KeycloakDepartmentDelegationSyncResult(
            enabled_role_codes=frozenset(normalized_requested),
            added_role_codes=frozenset(codes_to_add),
            removed_role_codes=frozenset(codes_to_remove),
        )

    async def _load_permission_role_payloads(
        self,
        *,
        api_client_uuid: str,
        admin_token: str,
        permission_codes: set[str],
    ) -> dict[str, dict[str, Any]]:
        payloads: dict[str, dict[str, Any]] = {}
        for permission_code in sorted(permission_codes):
            role_payload = await self._keycloak_admin.get_client_role_by_name(
                client_uuid=api_client_uuid,
                role_name=permission_code,
                admin_token=admin_token,
            )
            if role_payload is None:
                raise Conflict(f"Missing Keycloak role '{permission_code}' in API client")
            payloads[permission_code] = role_payload
        return payloads
