from __future__ import annotations

import uuid
from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.core.request_id import REQUEST_ID_HEADER, get_request_id
from app.domain.exceptions import AuthenticationUnavailable, Conflict, NotFound, Unauthorized


@dataclass(frozen=True, slots=True)
class IamTokenBundle:
    access_token: str
    access_token_expires_at: int
    refresh_token: str
    refresh_token_expires_at: int


@dataclass(frozen=True, slots=True)
class IamAccount:
    id: str
    login: str
    role: str
    auth_status: str
    created: bool


@dataclass(frozen=True, slots=True)
class IamActionToken:
    token: str
    expires_at: int
    purpose: str


@dataclass(frozen=True, slots=True)
class IamAccountPermissions:
    permissions_from_role: frozenset[str]
    individually_granted_permissions: frozenset[str]
    effective_permissions: frozenset[str]


class IamClient:
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    async def _request(self, method: str, path: str, *, json: dict | None = None) -> httpx.Response:
        headers = {
            "X-Acom-Service-Token": settings.iam_internal_service_token,
            REQUEST_ID_HEADER: get_request_id() or str(uuid.uuid4()),
        }
        try:
            if self._client is not None:
                response = await self._client.request(method, path, json=json, headers=headers)
            else:
                async with httpx.AsyncClient(
                    base_url=settings.iam_internal_base_url,
                    timeout=settings.iam_http_timeout_seconds,
                ) as client:
                    response = await client.request(method, path, json=json, headers=headers)
        except httpx.HTTPError as exc:
            raise AuthenticationUnavailable() from exc
        if response.status_code in {401, 403}:
            raise Unauthorized("IAM request rejected")
        if response.status_code == 404:
            raise NotFound("IAM account not found")
        if response.status_code == 409:
            raise Conflict("IAM operation conflict")
        if response.status_code >= 500:
            raise AuthenticationUnavailable()
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise Conflict("IAM operation rejected") from exc
        return response

    async def exchange_code(
        self,
        *,
        code: str,
        verifier: str,
        redirect_uri: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> IamTokenBundle:
        response = await self._request(
            "POST",
            "/internal/token",
            json={
                "code": code,
                "code_verifier": verifier,
                "redirect_uri": redirect_uri,
                "ip_address": ip_address,
                "user_agent": user_agent,
            },
        )
        return IamTokenBundle(**response.json())

    async def refresh(self, refresh_token: str) -> IamTokenBundle:
        response = await self._request(
            "POST", "/internal/refresh", json={"refresh_token": refresh_token}
        )
        return IamTokenBundle(**response.json())

    async def logout(self, refresh_token: str, *, reason: str = "logout") -> None:
        await self._request(
            "POST",
            "/internal/logout",
            json={"refresh_token": refresh_token, "reason": reason},
        )

    async def put_account(
        self,
        *,
        account_id: uuid.UUID | str,
        login: str,
        role: str,
        auth_status: str = "pending",
    ) -> IamAccount:
        response = await self._request(
            "PUT",
            f"/internal/accounts/{account_id}",
            json={"login": login, "role": role, "auth_status": auth_status},
        )
        return IamAccount(**response.json())

    async def provision_local_development_account(
        self,
        *,
        account_id: uuid.UUID | str,
        login: str,
        role: str,
    ) -> IamAccount:
        response = await self._request(
            "POST",
            f"/internal/local-dev/accounts/{account_id}/provision",
            json={"login": login, "role": role, "auth_status": "active"},
        )
        return IamAccount(**response.json())

    async def update_role(
        self,
        *,
        account_id: str,
        role: str,
        actor_account_id: str | None,
        actor_session_id: str | None,
    ) -> IamAccount:
        response = await self._request(
            "PATCH",
            f"/internal/accounts/{account_id}/role",
            json={
                "role": role,
                "actor_account_id": actor_account_id,
                "actor_session_id": actor_session_id,
            },
        )
        return IamAccount(**response.json())

    async def update_status(
        self,
        *,
        account_id: str,
        auth_status: str,
        actor_account_id: str | None,
        actor_session_id: str | None,
    ) -> IamAccount:
        response = await self._request(
            "PATCH",
            f"/internal/accounts/{account_id}/status",
            json={
                "auth_status": auth_status,
                "actor_account_id": actor_account_id,
                "actor_session_id": actor_session_id,
            },
        )
        return IamAccount(**response.json())

    async def revoke_all(
        self,
        *,
        account_id: str,
        reason: str,
        actor_account_id: str | None = None,
        actor_session_id: str | None = None,
    ) -> int:
        response = await self._request(
            "POST",
            f"/internal/accounts/{account_id}/revoke-all",
            json={
                "reason": reason,
                "actor_account_id": actor_account_id,
                "actor_session_id": actor_session_id,
            },
        )
        return int(response.json()["revoked_sessions"])

    async def create_action_token(self, *, account_id: uuid.UUID | str, purpose: str) -> IamActionToken:
        response = await self._request(
            "POST",
            f"/internal/accounts/{account_id}/action-tokens",
            json={"purpose": purpose},
        )
        return IamActionToken(**response.json())

    async def get_account_permissions(
        self,
        *,
        account_id: uuid.UUID | str,
    ) -> IamAccountPermissions:
        response = await self._request(
            "GET",
            f"/internal/accounts/{account_id}/permissions",
        )
        payload = response.json()
        return IamAccountPermissions(
            permissions_from_role=frozenset(payload["permissions_from_role"]),
            individually_granted_permissions=frozenset(
                payload["individually_granted_permissions"]
            ),
            effective_permissions=frozenset(payload["effective_permissions"]),
        )

    async def replace_account_permission_grants(
        self,
        *,
        account_id: uuid.UUID | str,
        permissions: set[str] | frozenset[str],
    ) -> IamAccountPermissions:
        response = await self._request(
            "PUT",
            f"/internal/accounts/{account_id}/permission-grants",
            json={"permissions": sorted(permissions)},
        )
        payload = response.json()
        return IamAccountPermissions(
            permissions_from_role=frozenset(payload["permissions_from_role"]),
            individually_granted_permissions=frozenset(
                payload["individually_granted_permissions"]
            ),
            effective_permissions=frozenset(payload["effective_permissions"]),
        )

    async def seed_rbac(self, matrix: dict[str, list[str]]) -> dict[str, list[str]]:
        response = await self._request(
            "PUT",
            "/internal/rbac",
            json={
                "roles": [
                    {"name": role, "permissions": sorted(permissions)}
                    for role, permissions in sorted(matrix.items())
                ]
            },
        )
        return response.json()["roles"]

    async def rbac_report(self) -> dict[str, list[str]]:
        response = await self._request("GET", "/internal/rbac")
        return response.json()["roles"]

    async def reconcile_account_ids(
        self,
        account_ids: list[str],
    ) -> tuple[list[str], list[str]]:
        response = await self._request(
            "POST",
            "/internal/reconciliation/accounts",
            json={"account_ids": sorted(set(account_ids))},
        )
        payload = response.json()
        return (
            list(payload["orphan_iam_account_ids"]),
            list(payload["missing_iam_account_ids"]),
        )
