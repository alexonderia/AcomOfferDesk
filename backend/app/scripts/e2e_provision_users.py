from __future__ import annotations

import argparse
import asyncio
import json
import os
import secrets
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ProvisionedUser:
    prefix: str
    username: str
    password: str
    email: str
    local_user_id: str
    keycloak_user_id: str
    app_role: str


@dataclass(frozen=True, slots=True)
class ProvisionState:
    run_id: str
    users: list[ProvisionedUser]
    state_file: str


def _load_env_file(path: str) -> dict[str, str]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Env file not found: {path}")

    result: dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and ((value[0] == '"' and value[-1] == '"') or (value[0] == "'" and value[-1] == "'")):
                value = value[1:-1]
            result[key] = value
    return result


def _apply_env_file(path: str) -> None:
    for key, value in _load_env_file(path).items():
        os.environ.setdefault(key, value)


def _print_status(message: str) -> None:
    print(message, file=sys.stderr)


def _random_password() -> str:
    return f"E2e-{secrets.token_urlsafe(18)}-1a"


def _state_from_dict(payload: dict[str, Any]) -> ProvisionState:
    users = [
        ProvisionedUser(
            prefix=str(item["prefix"]),
            username=str(item["username"]),
            password=str(item.get("password") or ""),
            email=str(item["email"]),
            local_user_id=str(item["local_user_id"]),
            keycloak_user_id=str(item["keycloak_user_id"]),
            app_role=str(item["app_role"]),
        )
        for item in payload.get("users", [])
        if isinstance(item, dict)
    ]
    return ProvisionState(
        run_id=str(payload["run_id"]),
        users=users,
        state_file=str(payload["state_file"]),
    )


async def _request_token(
    *,
    token_endpoint: str,
    form_data: dict[str, str],
    timeout: float,
) -> str | None:
    import httpx

    try:
        async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
            response = await client.post(
                token_endpoint,
                data=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
    except Exception:  # noqa: BLE001
        return None
    if response.status_code >= 400:
        return None
    payload = response.json()
    if not isinstance(payload, dict):
        return None
    token = str(payload.get("access_token") or "").strip()
    return token or None


async def _get_admin_token_for_provisioning() -> tuple[str, str]:
    from app.core.config import settings

    timeout = settings.keycloak_http_timeout_seconds
    candidate_bases: list[str] = []
    for base in (settings.keycloak_internal_base_url, settings.resolved_keycloak_public_base_url):
        normalized = (base or "").rstrip("/")
        if normalized and normalized not in candidate_bases:
            candidate_bases.append(normalized)

    for internal_base in candidate_bases:
        if settings.keycloak_admin_username and settings.keycloak_admin_password:
            token = await _request_token(
                token_endpoint=f"{internal_base}/realms/{settings.keycloak_admin_realm}/protocol/openid-connect/token",
                form_data={
                    "grant_type": "password",
                    "client_id": "admin-cli",
                    "username": settings.keycloak_admin_username,
                    "password": settings.keycloak_admin_password,
                },
                timeout=timeout,
            )
            if token:
                return token, internal_base

        if settings.keycloak_admin_client_id and settings.keycloak_admin_client_secret:
            for realm in (settings.keycloak_realm, settings.keycloak_admin_realm):
                token = await _request_token(
                    token_endpoint=f"{internal_base}/realms/{realm}/protocol/openid-connect/token",
                    form_data={
                        "grant_type": "client_credentials",
                        "client_id": settings.keycloak_admin_client_id,
                        "client_secret": settings.keycloak_admin_client_secret,
                    },
                    timeout=timeout,
                )
                if token:
                    return token, internal_base

    raise RuntimeError("Unable to authenticate in Keycloak admin API")


async def _delete_keycloak_user(*, keycloak_user_id: str, admin_token: str) -> None:
    import httpx

    from app.core.config import settings

    async with httpx.AsyncClient(timeout=settings.keycloak_http_timeout_seconds, trust_env=False) as client:
        response = await client.delete(
            f"{settings.keycloak_internal_base_url}/admin/realms/{settings.keycloak_realm}/users/{keycloak_user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    if response.status_code not in {204, 404}:
        raise RuntimeError(f"Unable to delete Keycloak user '{keycloak_user_id}': HTTP {response.status_code}")


async def _create_keycloak_user(
    *,
    username: str,
    email: str,
    first_name: str,
    last_name: str,
    middle_name: str,
    password: str,
    app_role: str,
    admin_token: str,
    api_client_uuid: str,
) -> str:
    import httpx

    from app.core.config import settings
    from app.services.keycloak_admin import KeycloakAdminService

    service = KeycloakAdminService()
    users_endpoint = f"{settings.keycloak_internal_base_url}/admin/realms/{settings.keycloak_realm}/users"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=settings.keycloak_http_timeout_seconds, trust_env=False) as client:
        existing_response = await client.get(
            users_endpoint,
            params={"username": username, "exact": "true", "max": "2"},
            headers=headers,
        )
        if existing_response.status_code >= 400:
            raise RuntimeError(f"Unable to query Keycloak users: HTTP {existing_response.status_code}")
        existing_payload = existing_response.json()

    existing = [
        item
        for item in existing_payload
        if isinstance(item, dict) and str(item.get("username") or "").strip().lower() == username.lower()
    ]
    if existing:
        raise RuntimeError(f"Refusing to reuse existing Keycloak user '{username}'")

    async with httpx.AsyncClient(timeout=settings.keycloak_http_timeout_seconds, trust_env=False) as client:
        create_response = await client.post(
            users_endpoint,
            json={
                "username": username,
                "email": email,
                "firstName": first_name,
                "lastName": last_name,
                "attributes": {
                    "middleName": [middle_name],
                },
                "enabled": True,
                "emailVerified": True,
            },
            headers=headers,
        )
        if create_response.status_code >= 400:
            raise RuntimeError(f"Unable to create Keycloak user '{username}': HTTP {create_response.status_code}")

        created_response = await client.get(
            users_endpoint,
            params={"username": username, "exact": "true", "max": "2"},
            headers=headers,
        )
        if created_response.status_code >= 400:
            raise RuntimeError(f"Unable to query created Keycloak user '{username}': HTTP {created_response.status_code}")
        created_payload = created_response.json()

    created = [
        item
        for item in created_payload
        if isinstance(item, dict) and str(item.get("username") or "").strip().lower() == username.lower()
    ]
    if not created:
        raise RuntimeError(f"Unable to resolve created Keycloak user '{username}'")
    user_id = str(created[0].get("id") or "").strip()
    if not user_id:
        raise RuntimeError(f"Created Keycloak user '{username}' has empty id")

    try:
        async with httpx.AsyncClient(timeout=settings.keycloak_http_timeout_seconds, trust_env=False) as client:
            password_response = await client.put(
                f"{users_endpoint}/{user_id}/reset-password",
                json={"type": "password", "temporary": False, "value": password},
                headers=headers,
            )
            if password_response.status_code >= 400:
                raise RuntimeError(
                    f"Unable to set password for Keycloak user '{username}': HTTP {password_response.status_code}"
                )

        role_payload = await service.get_client_role_by_name(
            client_uuid=api_client_uuid,
            role_name=app_role,
            admin_token=admin_token,
        )
        if role_payload is None:
            raise RuntimeError(f"Missing Keycloak role '{app_role}'")
        await service.add_user_client_roles(
            keycloak_user_id=user_id,
            client_uuid=api_client_uuid,
            roles=[role_payload],
            admin_token=admin_token,
        )
    except Exception:
        await _delete_keycloak_user(keycloak_user_id=user_id, admin_token=admin_token)
        raise
    return user_id


async def _create_local_user(
    *,
    local_user_id: str,
    role_id: int,
    email: str,
    full_name: str,
    keycloak_user_id: str,
    username: str,
) -> None:
    from app.infrastructure.db import SessionLocal
    from app.models.auth_models import UserAuthAccount, UserContactChannel
    from app.models.orm_models import Profile, Role, User

    async with SessionLocal() as session:
        async with session.begin():
            existing = await session.get(User, local_user_id)
            if existing is not None:
                raise RuntimeError(f"Refusing to reuse existing local user '{local_user_id}'")

            role = await session.get(Role, role_id)
            if role is None:
                raise RuntimeError(f"Local role id '{role_id}' is missing in table roles")

            session.add(
                User(
                    id=local_user_id,
                    id_role=role_id,
                    status="active",
                )
            )
            await session.flush()
            session.add(Profile(id=local_user_id, full_name=full_name, phone=None, mail=email))
            session.add(
                UserAuthAccount(
                    id_user=local_user_id,
                    provider="keycloak",
                    external_subject_id=keycloak_user_id,
                    external_username=username,
                    external_email=email,
                    is_active=True,
                )
            )
            session.add(
                UserContactChannel(
                    id_user=local_user_id,
                    channel_type="email",
                    channel_value=email,
                    is_verified=True,
                    is_primary=True,
                    is_active=True,
                )
            )


async def _delete_local_user(*, local_user_id: str) -> None:
    from app.infrastructure.db import SessionLocal
    from app.models.orm_models import User

    if not local_user_id.startswith("e2e_"):
        raise RuntimeError(f"Refusing to delete non-e2e local user '{local_user_id}'")

    async with SessionLocal() as session:
        async with session.begin():
            user = await session.get(User, local_user_id)
            if user is not None:
                await session.delete(user)


async def provision(*, env_file: str, state_dir: str) -> int:
    _apply_env_file(env_file)

    from app.core.config import settings
    from app.infrastructure.db import engine
    from app.services.keycloak_admin import KeycloakAdminService

    if not settings.keycloak_enabled:
        raise RuntimeError("KEYCLOAK_ENABLED must be true for E2E provisioning")

    run_id = secrets.token_hex(4)
    role_specs = [
        ("E2E_SUPERADMIN", "superadmin", settings.superadmin_role_id, "app.superadmin"),
        ("E2E_ADMIN", "admin", settings.admin_role_id, "app.admin"),
        ("E2E_PROJECT_MANAGER", "project_manager", settings.project_manager_role_id, "app.project_manager"),
        ("E2E_LEAD_ECONOMIST", "lead_economist", settings.lead_economist_role_id, "app.lead_economist"),
        ("E2E_ECONOMIST", "economist", settings.economist_role_id, "app.economist"),
        ("E2E_OPERATOR", "operator", settings.operator_role_id, "app.operator"),
        ("E2E_CONTRACTOR", "contractor", settings.contractor_role_id, "app.contractor"),
    ]

    admin_token, admin_base_url = await _get_admin_token_for_provisioning()
    settings.keycloak_internal_base_url = admin_base_url
    service = KeycloakAdminService()
    api_client_uuid = await service.get_client_uuid_by_client_id(
        client_id=settings.keycloak_api_client_id,
        admin_token=admin_token,
    )

    users: list[ProvisionedUser] = []
    try:
        for env_prefix, role_slug, role_id, app_role in role_specs:
            username = f"e2e_{role_slug}_{run_id}"
            email = f"{username}@example.test"
            password = _random_password()
            _print_status(f"[OK] creating {username} with {app_role}")
            keycloak_user_id = await _create_keycloak_user(
                username=username,
                email=email,
                first_name="E2E",
                last_name=role_slug,
                middle_name="Autotest",
                password=password,
                app_role=app_role,
                admin_token=admin_token,
                api_client_uuid=api_client_uuid,
            )
            try:
                await _create_local_user(
                    local_user_id=username,
                    role_id=role_id,
                    email=email,
                    full_name=f"E2E {role_slug}",
                    keycloak_user_id=keycloak_user_id,
                    username=username,
                )
            except Exception:
                await _delete_keycloak_user(keycloak_user_id=keycloak_user_id, admin_token=admin_token)
                raise
            users.append(
                ProvisionedUser(
                    prefix=env_prefix,
                    username=username,
                    password=password,
                    email=email,
                    local_user_id=username,
                    keycloak_user_id=keycloak_user_id,
                    app_role=app_role,
                )
            )
    except Exception:
        state = ProvisionState(run_id=run_id, users=users, state_file="")
        await cleanup_state(state=state, env_file=env_file)
        raise
    finally:
        await engine.dispose()

    state_path = Path(state_dir) / f"e2e-users-{run_id}.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state = ProvisionState(run_id=run_id, users=users, state_file=str(state_path))
    state_path.write_text(json.dumps(asdict(state), indent=2), encoding="utf-8")
    print(json.dumps(asdict(state)))
    return 0


async def cleanup_state(*, state: ProvisionState, env_file: str) -> int:
    _apply_env_file(env_file)

    from app.core.config import settings
    from app.infrastructure.db import engine

    failures = 0
    admin_token: str | None = None
    try:
        admin_token, admin_base_url = await _get_admin_token_for_provisioning()
        settings.keycloak_internal_base_url = admin_base_url
    except Exception as exc:  # noqa: BLE001
        failures += 1
        _print_status(f"[FAIL] Keycloak cleanup bootstrap failed: {exc}")

    for user in reversed(state.users):
        try:
            await _delete_local_user(local_user_id=user.local_user_id)
            _print_status(f"[OK] deleted local user {user.local_user_id}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            _print_status(f"[FAIL] local cleanup for {user.local_user_id}: {exc}")

        if admin_token is None:
            failures += 1
            _print_status(f"[FAIL] Keycloak cleanup for {user.username}: admin token unavailable")
        else:
            try:
                await _delete_keycloak_user(keycloak_user_id=user.keycloak_user_id, admin_token=admin_token)
                _print_status(f"[OK] deleted Keycloak user {user.username}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                _print_status(f"[FAIL] Keycloak cleanup for {user.username}: {exc}")

    state_path = Path(state.state_file) if state.state_file else None
    if state_path is not None and state_path.exists():
        state_path.unlink()

    await engine.dispose()
    return 1 if failures else 0


async def cleanup(*, env_file: str, state_file: str) -> int:
    payload = json.loads(Path(state_file).read_text(encoding="utf-8"))
    state = _state_from_dict(payload)
    return await cleanup_state(state=state, env_file=env_file)


def main() -> int:
    parser = argparse.ArgumentParser(description="Provision temporary Keycloak/local users for E2E smoke tests")
    subparsers = parser.add_subparsers(dest="command", required=True)

    provision_parser = subparsers.add_parser("provision")
    provision_parser.add_argument("--env-file", required=True)
    provision_parser.add_argument("--state-dir", default=".tmp/e2e")

    cleanup_parser = subparsers.add_parser("cleanup")
    cleanup_parser.add_argument("--env-file", required=True)
    cleanup_parser.add_argument("--state-file", required=True)

    args = parser.parse_args()
    if args.command == "provision":
        return asyncio.run(provision(env_file=args.env_file, state_dir=args.state_dir))
    if args.command == "cleanup":
        return asyncio.run(cleanup(env_file=args.env_file, state_file=args.state_file))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
