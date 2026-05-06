from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy import and_, select

from app.core.config import settings
from app.infrastructure.db import SessionLocal, engine
from app.models.auth_models import UserAuthAccount
from app.models.orm_models import User


@dataclass(frozen=True, slots=True)
class KeycloakLinkedUser:
    user_id: str
    role_id: int
    keycloak_subject: str


def _env_flag(name: str, *, default: bool) -> bool:
    raw_value = (os.getenv(name) or "").strip().lower()
    if not raw_value:
        return default
    return raw_value in {"1", "true", "yes", "on"}


def _role_mapping() -> dict[int, str]:
    return {
        settings.superadmin_role_id: "app.superadmin",
        settings.admin_role_id: "app.admin",
        settings.contractor_role_id: "app.contractor",
        settings.project_manager_role_id: "app.project_manager",
        settings.lead_economist_role_id: "app.lead_economist",
        settings.economist_role_id: "app.economist",
        settings.operator_role_id: "app.operator",
    }


async def _load_linked_users() -> list[KeycloakLinkedUser]:
    async with SessionLocal() as session:
        stmt = (
            select(
                User.id,
                User.id_role,
                UserAuthAccount.external_subject_id,
            )
            .join(
                UserAuthAccount,
                and_(
                    UserAuthAccount.id_user == User.id,
                    UserAuthAccount.provider == "keycloak",
                    UserAuthAccount.is_active.is_(True),
                ),
            )
            .order_by(User.id.asc())
        )
        rows = (await session.execute(stmt)).all()

    users: list[KeycloakLinkedUser] = []
    for user_id, role_id, external_subject_id in rows:
        subject = (external_subject_id or "").strip()
        if not subject:
            continue
        users.append(
            KeycloakLinkedUser(
                user_id=str(user_id),
                role_id=int(role_id),
                keycloak_subject=subject,
            )
        )
    return users


def _token_endpoint() -> str:
    return f"{settings.keycloak_internal_base_url.rstrip('/')}/realms/{settings.keycloak_admin_realm}/protocol/openid-connect/token"


def _admin_base_url() -> str:
    return f"{settings.keycloak_internal_base_url.rstrip('/')}/admin/realms/{settings.keycloak_realm}"


async def _get_admin_token(client: httpx.AsyncClient) -> str:
    if settings.keycloak_admin_client_secret:
        form_data = {
            "grant_type": "client_credentials",
            "client_id": settings.keycloak_admin_client_id,
            "client_secret": settings.keycloak_admin_client_secret,
        }
    else:
        form_data = {
            "grant_type": "password",
            "client_id": settings.keycloak_admin_client_id,
            "username": settings.keycloak_admin_username or "",
            "password": settings.keycloak_admin_password or "",
        }
    response = await client.post(
        _token_endpoint(),
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response.raise_for_status()
    payload = response.json()
    access_token = str(payload.get("access_token") or "").strip() if isinstance(payload, dict) else ""
    if not access_token:
        raise RuntimeError("Keycloak admin token is missing in response")
    return access_token


async def _get_api_client_uuid(client: httpx.AsyncClient, token: str) -> str:
    response = await client.get(
        f"{_admin_base_url()}/clients",
        params={"clientId": settings.keycloak_api_client_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise RuntimeError("Keycloak clients lookup returned invalid payload")
    for item in payload:
        if not isinstance(item, dict):
            continue
        if str(item.get("clientId") or "") != settings.keycloak_api_client_id:
            continue
        client_uuid = str(item.get("id") or "").strip()
        if client_uuid:
            return client_uuid
    raise RuntimeError(f"Unable to resolve Keycloak client UUID for {settings.keycloak_api_client_id}")


async def _get_client_role_catalog(
    client: httpx.AsyncClient,
    *,
    token: str,
    api_client_uuid: str,
    role_names: set[str],
) -> dict[str, dict[str, Any]]:
    headers = {"Authorization": f"Bearer {token}"}
    catalog: dict[str, dict[str, Any]] = {}
    for role_name in sorted(role_names):
        response = await client.get(
            f"{_admin_base_url()}/clients/{api_client_uuid}/roles/{role_name}",
            headers=headers,
        )
        if response.status_code == 404:
            continue
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict):
            catalog[role_name] = payload
    return catalog


async def _get_user_client_roles(
    client: httpx.AsyncClient,
    *,
    token: str,
    api_client_uuid: str,
    keycloak_user_id: str,
) -> list[dict[str, Any]] | None:
    response = await client.get(
        f"{_admin_base_url()}/users/{keycloak_user_id}/role-mappings/clients/{api_client_uuid}",
        headers={"Authorization": f"Bearer {token}"},
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


async def _sync_user_app_role(
    client: httpx.AsyncClient,
    *,
    token: str,
    api_client_uuid: str,
    keycloak_user_id: str,
    target_app_role: str,
    role_catalog: dict[str, dict[str, Any]],
) -> tuple[bool, int]:
    current_roles = await _get_user_client_roles(
        client,
        token=token,
        api_client_uuid=api_client_uuid,
        keycloak_user_id=keycloak_user_id,
    )
    if current_roles is None:
        return False, 0

    mapping_url = f"{_admin_base_url()}/users/{keycloak_user_id}/role-mappings/clients/{api_client_uuid}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    current_role_names = {
        str(item.get("name") or "").strip()
        for item in current_roles
        if isinstance(item, dict)
    }
    current_role_names.discard("")

    app_roles_to_remove = [
        item
        for item in current_roles
        if str(item.get("name") or "").strip().startswith("app.")
        and str(item.get("name") or "").strip() != target_app_role
    ]
    removed_count = len(app_roles_to_remove)
    if app_roles_to_remove:
        remove_response = await client.request(
            "DELETE",
            mapping_url,
            json=app_roles_to_remove,
            headers=headers,
        )
        remove_response.raise_for_status()

    changed = bool(app_roles_to_remove)
    if target_app_role not in current_role_names:
        target_role_payload = role_catalog.get(target_app_role)
        if target_role_payload is None:
            raise RuntimeError(f"Missing Keycloak role '{target_app_role}' in {settings.keycloak_api_client_id}")
        add_response = await client.post(
            mapping_url,
            json=[target_role_payload],
            headers=headers,
        )
        add_response.raise_for_status()
        changed = True

    return True, removed_count if changed else 0


async def sync_existing_users_app_roles() -> int:
    if not settings.keycloak_enabled:
        print("SKIP: KEYCLOAK_ENABLED=false")
        return 0

    if not _env_flag("KEYCLOAK_INIT_SYNC_EXISTING_USERS_BY_ROLE", default=True):
        print("SKIP: KEYCLOAK_INIT_SYNC_EXISTING_USERS_BY_ROLE=false")
        return 0

    if not settings.keycloak_admin_client_secret and (not settings.keycloak_admin_username or not settings.keycloak_admin_password):
        raise RuntimeError(
            "Keycloak admin credentials are not configured. "
            "Set KEYCLOAK_ADMIN_CLIENT_SECRET or KEYCLOAK_ADMIN_USERNAME/KEYCLOAK_ADMIN_PASSWORD."
        )

    linked_users = await _load_linked_users()
    role_mapping = _role_mapping()

    if not linked_users:
        print("SYNC_RESULT total_linked_users=0 assigned=0 skipped=0 removed=0")
        return 0

    target_role_names = {role_mapping[item.role_id] for item in linked_users if item.role_id in role_mapping}
    if not target_role_names:
        print(
            "SYNC_RESULT",
            f"total_linked_users={len(linked_users)}",
            "assigned=0",
            f"skipped={len(linked_users)}",
            "removed=0",
        )
        return 0

    timeout = settings.keycloak_http_timeout_seconds
    async with httpx.AsyncClient(timeout=timeout) as client:
        token = await _get_admin_token(client)
        api_client_uuid = await _get_api_client_uuid(client, token)
        role_catalog = await _get_client_role_catalog(
            client,
            token=token,
            api_client_uuid=api_client_uuid,
            role_names=target_role_names,
        )

        assigned = 0
        skipped = 0
        removed = 0
        for linked_user in linked_users:
            target_role = role_mapping.get(linked_user.role_id)
            if target_role is None:
                skipped += 1
                print(
                    "SYNC_SKIP",
                    f"user_id={linked_user.user_id}",
                    f"reason=unsupported_role_id",
                    f"role_id={linked_user.role_id}",
                )
                continue
            synced, removed_count = await _sync_user_app_role(
                client,
                token=token,
                api_client_uuid=api_client_uuid,
                keycloak_user_id=linked_user.keycloak_subject,
                target_app_role=target_role,
                role_catalog=role_catalog,
            )
            if not synced:
                skipped += 1
                print(
                    "SYNC_SKIP",
                    f"user_id={linked_user.user_id}",
                    f"reason=missing_keycloak_user",
                    f"keycloak_sub={linked_user.keycloak_subject}",
                )
                continue
            assigned += 1
            removed += removed_count

    print(
        "SYNC_RESULT",
        f"total_linked_users={len(linked_users)}",
        f"assigned={assigned}",
        f"skipped={skipped}",
        f"removed={removed}",
    )
    return 0


async def _run_main() -> int:
    try:
        return await sync_existing_users_app_roles()
    finally:
        await engine.dispose()


def main() -> int:
    return asyncio.run(_run_main())


if __name__ == "__main__":
    raise SystemExit(main())
