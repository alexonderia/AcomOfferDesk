from __future__ import annotations

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
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._users_endpoint}/{normalized_user_id}/logout",
                headers=self._headers(admin_token),
            )
        if response.status_code >= 400:
            raise Conflict("Unable to terminate Keycloak user sessions")

    def _ensure_configured(self) -> None:
        if not self._admin_username or not self._admin_password:
            raise Forbidden("Keycloak admin integration is not configured")

    async def _get_admin_token(self) -> str:
        token_endpoint = f"{self._base_url}/realms/{self._admin_realm}/protocol/openid-connect/token"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                token_endpoint,
                data={
                    "grant_type": "password",
                    "client_id": self._admin_client_id,
                    "username": self._admin_username or "",
                    "password": self._admin_password or "",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if response.status_code >= 400:
            raise Forbidden("Unable to authenticate in Keycloak admin API")

        payload = response.json()
        if not isinstance(payload, dict):
            raise Forbidden("Unable to authenticate in Keycloak admin API")

        access_token = str(payload.get("access_token") or "").strip()
        if not access_token:
            raise Forbidden("Unable to authenticate in Keycloak admin API")
        return access_token

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
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                self._users_endpoint,
                params=params,
                headers=self._headers(admin_token),
            )
        if response.status_code >= 400:
            raise Conflict("Unable to query Keycloak users")

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

        async with httpx.AsyncClient(timeout=self._timeout) as client:
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

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.put(
                f"{self._users_endpoint}/{user_id}",
                json=payload,
                headers=self._headers(admin_token),
            )
        if response.status_code >= 400:
            raise Conflict("Unable to update Keycloak account")

    async def _set_password(self, admin_token: str, *, user_id: str, password: str) -> None:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
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
