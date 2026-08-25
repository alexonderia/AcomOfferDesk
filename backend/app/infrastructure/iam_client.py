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
class IamBrowserPage:
    status_code: int
    html: str


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
class IamActionConsumeResult:
    account_id: str
    purpose: str
    auth_status: str
    context: dict | None = None


@dataclass(frozen=True, slots=True)
class IamAccountPermissions:
    permissions_from_role: frozenset[str]
    individually_granted_permissions: frozenset[str]
    effective_permissions: frozenset[str]


@dataclass(frozen=True, slots=True)
class IamCredentialState:
    id: str
    login: str
    role: str
    auth_status: str
    password_set: bool
    created: bool = False
    required_actions: tuple[str, ...] = ()


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

    async def render_password_action_page(
        self,
        *,
        action: str,
        token: str | None = None,
        form: dict[str, str] | None = None,
    ) -> IamBrowserPage:
        """Use IAM's private network path while the browser stays on BFF URLs."""

        if action not in {"setup", "reset"}:
            raise ValueError("Unsupported password action")
        path = f"/iam/password/{action}"
        headers = {
            "X-Acom-Service-Token": settings.iam_internal_service_token,
            REQUEST_ID_HEADER: get_request_id() or str(uuid.uuid4()),
        }
        try:
            if self._client is not None:
                response = await self._client.request(
                    "POST" if form is not None else "GET",
                    path,
                    params={"token": token} if token is not None else None,
                    data=form,
                    headers=headers,
                )
            else:
                async with httpx.AsyncClient(
                    base_url=settings.iam_internal_base_url,
                    timeout=settings.iam_http_timeout_seconds,
                ) as client:
                    response = await client.request(
                        "POST" if form is not None else "GET",
                        path,
                        params={"token": token} if token is not None else None,
                        data=form,
                        headers=headers,
                    )
        except httpx.HTTPError as exc:
            raise AuthenticationUnavailable() from exc
        if response.status_code >= 500:
            raise AuthenticationUnavailable()
        return IamBrowserPage(status_code=response.status_code, html=response.text)

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

    async def provision_registration_credentials(
        self,
        *,
        account_id: uuid.UUID | str,
        login: str,
        role: str,
        password: str,
        auth_status: str = "pending",
        replace_password: bool = False,
    ) -> IamCredentialState:
        response = await self._request(
            "PUT",
            f"/internal/accounts/{account_id}/registration-credentials",
            json={
                "login": login,
                "role": role,
                "auth_status": auth_status,
                "password": password,
                "replace_password": replace_password,
            },
        )
        payload = response.json()
        return IamCredentialState(
            id=str(payload["id"]),
            login=payload["login"],
            role=payload["role"],
            auth_status=payload["auth_status"],
            password_set=bool(payload["password_set"]),
            created=bool(payload.get("created", False)),
            required_actions=tuple(payload.get("required_actions") or ()),
        )

    async def get_credential_state(
        self,
        *,
        account_id: uuid.UUID | str,
    ) -> IamCredentialState:
        response = await self._request(
            "GET",
            f"/internal/accounts/{account_id}/credential-state",
        )
        payload = response.json()
        return IamCredentialState(
            id=str(payload["id"]),
            login=payload["login"],
            role=payload["role"],
            auth_status=payload["auth_status"],
            password_set=bool(payload["password_set"]),
            required_actions=tuple(payload.get("required_actions") or ()),
        )

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

    async def create_action_token(
        self,
        *,
        account_id: uuid.UUID | str,
        purpose: str,
        context: dict | None = None,
    ) -> IamActionToken:
        payload: dict = {"purpose": purpose}
        if context:
            payload["context"] = context
        response = await self._request(
            "POST",
            f"/internal/accounts/{account_id}/action-tokens",
            json=payload,
        )
        return IamActionToken(**response.json())

    async def consume_action_token(
        self,
        *,
        token: str,
        purpose: str,
        new_password: str | None = None,
    ) -> IamActionConsumeResult:
        payload: dict = {"token": token, "purpose": purpose}
        if new_password is not None:
            payload["new_password"] = new_password
        response = await self._request(
            "POST",
            "/internal/action-tokens/consume",
            json=payload,
        )
        body = response.json()
        return IamActionConsumeResult(
            account_id=str(body["account_id"]),
            purpose=body["purpose"],
            auth_status=body["auth_status"],
            context=body.get("context"),
        )

    async def complete_required_action(
        self,
        *,
        account_id: uuid.UUID | str,
        purpose: str = "complete_profile",
    ) -> None:
        await self._request(
            "POST",
            f"/internal/accounts/{account_id}/required-actions/{purpose}/complete",
        )

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
