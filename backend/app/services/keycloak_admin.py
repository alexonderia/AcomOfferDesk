from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings
from app.domain.exceptions import Conflict, Forbidden


def _normalize_email(email: str | None) -> str | None:
    normalized = (email or "").strip().lower()
    return normalized or None


@dataclass(frozen=True, slots=True)
class KeycloakAdminUser:
    id: str
    username: str | None
    email: str | None


class KeycloakAdminService:
    def __init__(self) -> None:
        self._base_url = settings.keycloak_internal_base_url.rstrip("/")
        self._realm = settings.keycloak_realm
        self._admin_realm = settings.keycloak_admin_realm
        self._admin_client_id = settings.keycloak_admin_client_id
        self._admin_client_secret = settings.keycloak_admin_client_secret
        self._admin_username = settings.keycloak_admin_username
        self._admin_password = settings.keycloak_admin_password
        self._timeout = settings.keycloak_http_timeout_seconds

    async def ensure_user(
        self,
        *,
        username: str,
        email: str | None,
        password: str | None = None,
        previous_username: str | None = None,
        enabled: bool = True,
        email_verified: bool = False,
    ) -> KeycloakAdminUser:
        if not settings.keycloak_enabled:
            return

        self._ensure_configured()
        normalized_email = _normalize_email(email)
        admin_token = await self._get_admin_token()

        current_user = await self._find_user_by_username(admin_token, username)
        if current_user is None and previous_username and previous_username != username:
            current_user = await self._find_user_by_username(admin_token, previous_username)

        if normalized_email:
            same_email_user = await self._find_user_by_email(admin_token, normalized_email)
            if same_email_user is not None and (current_user is None or same_email_user.id != current_user.id):
                raise Conflict("Keycloak email is already used by another account")

        if current_user is None:
            user_id = await self._create_user(
                admin_token,
                username=username,
                email=normalized_email,
                enabled=enabled,
                email_verified=email_verified,
            )
            current_user = KeycloakAdminUser(
                id=user_id,
                username=username,
                email=normalized_email,
            )
        else:
            await self._update_user(
                admin_token,
                user_id=current_user.id,
                username=username,
                email=normalized_email,
                enabled=enabled,
                email_verified=email_verified,
            )
            user_id = current_user.id
            current_user = KeycloakAdminUser(
                id=user_id,
                username=username,
                email=normalized_email,
            )

        if password is not None:
            await self._set_password(admin_token, user_id=user_id, password=password)
        return current_user

    async def logout_user_sessions(self, *, user_id: str) -> None:
        if not settings.keycloak_enabled:
            return
        self._ensure_configured()
        normalized_user_id = (user_id or "").strip()
        if not normalized_user_id:
            return

        admin_token = await self._get_admin_token()
        async with httpx.AsyncClient(timeout=self._timeout, trust_env=False) as client:
            response = await client.post(
                f"{self._users_endpoint}/{normalized_user_id}/logout",
                headers=self._headers(admin_token),
            )
        if response.status_code >= 400:
            raise Conflict("Unable to terminate Keycloak user sessions")

    async def get_admin_token(self) -> str:
        if not settings.keycloak_enabled:
            raise Forbidden("Keycloak integration is disabled")
        self._ensure_configured()
        return await self._get_admin_token()

    async def get_client_uuid_by_client_id(
        self,
        *,
        client_id: str,
        admin_token: str | None = None,
    ) -> str:
        if not settings.keycloak_enabled:
            raise Forbidden("Keycloak integration is disabled")

        normalized_client_id = (client_id or "").strip()
        if not normalized_client_id:
            raise Conflict("Keycloak clientId is required")

        token = admin_token or await self.get_admin_token()
        async with httpx.AsyncClient(timeout=self._timeout, trust_env=False) as client:
            response = await client.get(
                f"{self._admin_base_url}/clients",
                params={"clientId": normalized_client_id},
                headers=self._headers(token),
            )
        if response.status_code >= 400:
            raise Conflict("Unable to query Keycloak clients")

        payload = response.json()
        if not isinstance(payload, list):
            raise Conflict("Unable to query Keycloak clients")

        for item in payload:
            if not isinstance(item, dict):
                continue
            if str(item.get("clientId") or "").strip() != normalized_client_id:
                continue
            client_uuid = str(item.get("id") or "").strip()
            if client_uuid:
                return client_uuid
        raise Conflict(f"Unable to resolve Keycloak client '{normalized_client_id}'")

    async def get_client_role_by_name(
        self,
        *,
        client_uuid: str,
        role_name: str,
        admin_token: str | None = None,
    ) -> dict[str, Any] | None:
        if not settings.keycloak_enabled:
            raise Forbidden("Keycloak integration is disabled")

        normalized_client_uuid = (client_uuid or "").strip()
        normalized_role_name = (role_name or "").strip()
        if not normalized_client_uuid or not normalized_role_name:
            raise Conflict("Keycloak role lookup requires client UUID and role name")

        token = admin_token or await self.get_admin_token()
        async with httpx.AsyncClient(timeout=self._timeout, trust_env=False) as client:
            response = await client.get(
                f"{self._admin_base_url}/clients/{normalized_client_uuid}/roles/{normalized_role_name}",
                headers=self._headers(token),
            )
        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            raise Conflict("Unable to query Keycloak client role")

        payload = response.json()
        if not isinstance(payload, dict):
            raise Conflict("Unable to query Keycloak client role")
        return payload

    async def get_user_client_role_mappings(
        self,
        *,
        keycloak_user_id: str,
        client_uuid: str,
        admin_token: str | None = None,
    ) -> list[dict[str, Any]] | None:
        if not settings.keycloak_enabled:
            raise Forbidden("Keycloak integration is disabled")

        normalized_user_id = (keycloak_user_id or "").strip()
        normalized_client_uuid = (client_uuid or "").strip()
        if not normalized_user_id or not normalized_client_uuid:
            raise Conflict("Keycloak role mappings lookup requires user ID and client UUID")

        token = admin_token or await self.get_admin_token()
        async with httpx.AsyncClient(timeout=self._timeout, trust_env=False) as client:
            response = await client.get(
                f"{self._users_endpoint}/{normalized_user_id}/role-mappings/clients/{normalized_client_uuid}",
                headers=self._headers(token),
            )
        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            raise Conflict("Unable to query Keycloak user role mappings")

        payload = response.json()
        if not isinstance(payload, list):
            raise Conflict("Unable to query Keycloak user role mappings")
        return [item for item in payload if isinstance(item, dict)]

    async def add_user_client_roles(
        self,
        *,
        keycloak_user_id: str,
        client_uuid: str,
        roles: list[dict[str, Any]],
        admin_token: str | None = None,
    ) -> None:
        if not roles:
            return
        token = admin_token or await self.get_admin_token()
        async with httpx.AsyncClient(timeout=self._timeout, trust_env=False) as client:
            response = await client.post(
                f"{self._users_endpoint}/{keycloak_user_id}/role-mappings/clients/{client_uuid}",
                json=roles,
                headers=self._headers(token),
            )
        if response.status_code >= 400:
            raise Conflict("Unable to assign Keycloak user role mappings")

    async def remove_user_client_roles(
        self,
        *,
        keycloak_user_id: str,
        client_uuid: str,
        roles: list[dict[str, Any]],
        admin_token: str | None = None,
    ) -> None:
        if not roles:
            return
        token = admin_token or await self.get_admin_token()
        async with httpx.AsyncClient(timeout=self._timeout, trust_env=False) as client:
            response = await client.request(
                "DELETE",
                f"{self._users_endpoint}/{keycloak_user_id}/role-mappings/clients/{client_uuid}",
                json=roles,
                headers=self._headers(token),
            )
        if response.status_code >= 400:
            raise Conflict("Unable to remove Keycloak user role mappings")

    async def replace_user_app_role(
        self,
        *,
        keycloak_user_id: str,
        api_client_uuid: str,
        target_app_role: str,
        admin_token: str | None = None,
    ) -> tuple[bool, int]:
        normalized_target_role = (target_app_role or "").strip()
        if not normalized_target_role.startswith("app."):
            raise Conflict("Target Keycloak role must be app.*")

        token = admin_token or await self.get_admin_token()
        current_roles = await self.get_user_client_role_mappings(
            keycloak_user_id=keycloak_user_id,
            client_uuid=api_client_uuid,
            admin_token=token,
        )
        if current_roles is None:
            return False, 0

        app_roles_to_remove = [
            role_payload
            for role_payload in current_roles
            if str(role_payload.get("name") or "").strip().startswith("app.")
            and str(role_payload.get("name") or "").strip() != normalized_target_role
        ]
        removed_count = len(app_roles_to_remove)
        if app_roles_to_remove:
            await self.remove_user_client_roles(
                keycloak_user_id=keycloak_user_id,
                client_uuid=api_client_uuid,
                roles=app_roles_to_remove,
                admin_token=token,
            )

        current_role_names = {
            str(role_payload.get("name") or "").strip()
            for role_payload in current_roles
            if isinstance(role_payload, dict)
        }
        current_role_names.discard("")

        changed = bool(app_roles_to_remove)
        if normalized_target_role not in current_role_names:
            target_role_payload = await self.get_client_role_by_name(
                client_uuid=api_client_uuid,
                role_name=normalized_target_role,
                admin_token=token,
            )
            if target_role_payload is None:
                raise Conflict(f"Missing Keycloak role '{normalized_target_role}' in API client")
            await self.add_user_client_roles(
                keycloak_user_id=keycloak_user_id,
                client_uuid=api_client_uuid,
                roles=[target_role_payload],
                admin_token=token,
            )
            changed = True

        return True, removed_count if changed else 0

    async def sync_user_app_role_for_local_role(
        self,
        *,
        keycloak_user_id: str,
        api_client_uuid: str,
        local_role_id: int,
        role_mapping: dict[int, str],
        admin_token: str | None = None,
    ) -> tuple[bool, int]:
        target_app_role = role_mapping.get(local_role_id)
        if target_app_role is None:
            raise Conflict(f"Unsupported local role id '{local_role_id}' for Keycloak app-role sync")
        return await self.replace_user_app_role(
            keycloak_user_id=keycloak_user_id,
            api_client_uuid=api_client_uuid,
            target_app_role=target_app_role,
            admin_token=admin_token,
        )

    def _ensure_configured(self) -> None:
        has_service_account_credentials = bool(self._admin_client_id and self._admin_client_secret)
        has_password_grant_credentials = bool(self._admin_username and self._admin_password)
        if not has_service_account_credentials and not has_password_grant_credentials:
            raise Forbidden("Keycloak admin integration is not configured")

    async def _get_admin_token(self) -> str:
        if self._admin_client_secret:
            # Service account permissions (realm-management roles) are usually granted in the app realm.
            # Try app realm first, but keep a fallback token even when expected claims are not exposed.
            weak_service_account_token: str | None = None
            for realm in self._iter_realm_candidates(prefer_master=False):
                token = await self._request_token(
                    realm=realm,
                    form_data={
                        "grant_type": "client_credentials",
                        "client_id": self._admin_client_id,
                        "client_secret": self._admin_client_secret,
                    },
                )
                if not token:
                    continue
                if self._token_has_realm_management_users_roles(token):
                    return token
                if weak_service_account_token is None:
                    weak_service_account_token = token

            if self._admin_username and self._admin_password:
                password_token = await self._request_password_grant_token()
                if password_token:
                    return password_token

            if weak_service_account_token:
                return weak_service_account_token
            raise Forbidden("Unable to authenticate in Keycloak admin API")

        password_token = await self._request_password_grant_token()
        if password_token:
            return password_token
        raise Forbidden("Unable to authenticate in Keycloak admin API")

    async def _request_password_grant_token(self) -> str | None:
        if not self._admin_username or not self._admin_password:
            return None

        candidate_clients: list[tuple[str, str | None]] = [("admin-cli", None)]
        normalized_admin_client_id = self._admin_client_id.strip()
        if (
            normalized_admin_client_id
            and normalized_admin_client_id != "admin-cli"
            and self._admin_client_secret
        ):
            candidate_clients.append((normalized_admin_client_id, self._admin_client_secret))

        for realm in self._iter_realm_candidates(prefer_master=True):
            for client_id, client_secret in candidate_clients:
                form_data = {
                    "grant_type": "password",
                    "client_id": client_id,
                    "username": self._admin_username,
                    "password": self._admin_password,
                }
                if client_secret:
                    form_data["client_secret"] = client_secret
                token = await self._request_token(
                    realm=realm,
                    form_data=form_data,
                )
                if token:
                    return token
        return None

    def _iter_realm_candidates(self, *, prefer_master: bool) -> list[str]:
        candidates: list[str] = []
        if prefer_master:
            candidates.extend([self._admin_realm, "master", self._realm])
        else:
            candidates.extend([self._realm, self._admin_realm, "master"])
        unique_candidates: list[str] = []
        for realm in candidates:
            normalized = (realm or "").strip()
            if not normalized or normalized in unique_candidates:
                continue
            unique_candidates.append(normalized)
        return unique_candidates

    async def _request_token(self, *, realm: str, form_data: dict[str, str]) -> str | None:
        token_endpoint = f"{self._base_url}/realms/{realm}/protocol/openid-connect/token"
        async with httpx.AsyncClient(timeout=self._timeout, trust_env=False) as client:
            response = await client.post(
                token_endpoint,
                data=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if response.status_code >= 400:
            return None

        payload = response.json()
        if not isinstance(payload, dict):
            return None
        access_token = str(payload.get("access_token") or "").strip()
        return access_token or None

    def _token_has_realm_management_users_roles(self, token: str) -> bool:
        parts = token.split(".")
        if len(parts) < 2:
            return False
        payload_segment = parts[1]
        payload_segment += "=" * (-len(payload_segment) % 4)
        try:
            payload_raw = base64.urlsafe_b64decode(payload_segment.encode("utf-8")).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return False

        try:
            payload = json.loads(payload_raw)
        except ValueError:
            return False
        if not isinstance(payload, dict):
            return False

        resource_access = payload.get("resource_access")
        if not isinstance(resource_access, dict):
            return False
        realm_management = resource_access.get("realm-management")
        if not isinstance(realm_management, dict):
            return False
        roles = realm_management.get("roles")
        if not isinstance(roles, list):
            return False
        roles_set = {str(role).strip() for role in roles}
        return {"query-users", "view-users", "manage-users"}.issubset(roles_set)

    async def _find_user_by_username(self, admin_token: str, username: str) -> KeycloakAdminUser | None:
        payload = await self._get_users(
            admin_token,
            params={"username": username, "exact": "true", "max": "2"},
        )
        return self._pick_exact_user(payload, username=username)

    async def _find_user_by_email(self, admin_token: str, email: str) -> KeycloakAdminUser | None:
        payload = await self._get_users(
            admin_token,
            params={"email": email, "exact": "true", "max": "2"},
        )
        return self._pick_exact_user(payload, email=email)

    async def _get_users(self, admin_token: str, *, params: dict[str, str]) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self._timeout, trust_env=False) as client:
            response = await client.get(
                self._users_endpoint,
                params=params,
                headers=self._headers(admin_token),
            )
        if response.status_code >= 400:
            raise Conflict(f"Unable to query Keycloak users (status={response.status_code})")

        payload = response.json()
        if not isinstance(payload, list):
            raise Conflict("Unable to query Keycloak users")
        return [item for item in payload if isinstance(item, dict)]

    def _pick_exact_user(
        self,
        payload: list[dict[str, Any]],
        *,
        username: str | None = None,
        email: str | None = None,
    ) -> KeycloakAdminUser | None:
        normalized_username = (username or "").strip().lower()
        normalized_email = _normalize_email(email)

        for item in payload:
            item_id = str(item.get("id") or "").strip()
            item_username = str(item.get("username") or "").strip()
            item_email = _normalize_email(str(item.get("email") or ""))
            if not item_id:
                continue
            if normalized_username and item_username.lower() != normalized_username:
                continue
            if normalized_email and item_email != normalized_email:
                continue
            return KeycloakAdminUser(
                id=item_id,
                username=item_username or None,
                email=item_email,
            )
        return None

    async def _create_user(
        self,
        admin_token: str,
        *,
        username: str,
        email: str | None,
        enabled: bool,
        email_verified: bool,
    ) -> str:
        payload: dict[str, Any] = {
            "username": username,
            "enabled": enabled,
            "emailVerified": email_verified,
        }
        if email is not None:
            payload["email"] = email

        async with httpx.AsyncClient(timeout=self._timeout, trust_env=False) as client:
            response = await client.post(
                self._users_endpoint,
                json=payload,
                headers=self._headers(admin_token),
            )
        if response.status_code == 409:
            raise Conflict("Keycloak account already exists")
        if response.status_code >= 400:
            raise Conflict("Unable to create Keycloak account")

        created_user = await self._find_user_by_username(admin_token, username)
        if created_user is None:
            raise Conflict("Unable to create Keycloak account")
        return created_user.id

    async def _update_user(
        self,
        admin_token: str,
        *,
        user_id: str,
        username: str,
        email: str | None,
        enabled: bool,
        email_verified: bool,
    ) -> None:
        payload: dict[str, Any] = {
            "username": username,
            "enabled": enabled,
            "emailVerified": email_verified,
        }
        if email is not None:
            payload["email"] = email

        async with httpx.AsyncClient(timeout=self._timeout, trust_env=False) as client:
            response = await client.put(
                f"{self._users_endpoint}/{user_id}",
                json=payload,
                headers=self._headers(admin_token),
            )
        if response.status_code >= 400:
            raise Conflict("Unable to update Keycloak account")

    async def _set_password(self, admin_token: str, *, user_id: str, password: str) -> None:
        async with httpx.AsyncClient(timeout=self._timeout, trust_env=False) as client:
            response = await client.put(
                f"{self._users_endpoint}/{user_id}/reset-password",
                json={
                    "type": "password",
                    "temporary": False,
                    "value": password,
                },
                headers=self._headers(admin_token),
            )
        if response.status_code >= 400:
            raise Conflict("Unable to set Keycloak password")

    def _headers(self, admin_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json",
        }

    @property
    def _users_endpoint(self) -> str:
        return f"{self._base_url}/admin/realms/{self._realm}/users"

    @property
    def _admin_base_url(self) -> str:
        return f"{self._base_url}/admin/realms/{self._realm}"

