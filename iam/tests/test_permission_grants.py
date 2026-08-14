from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from iam_app.core.config import settings
from iam_app.core.security import pkce_s256
from iam_app.errors import Conflict
from iam_app.main import app
from iam_app.repositories import AuditRepository, RoleRepository
from iam_app.services import IamService


ROLE = "economist"
ROLE_PERMISSIONS = ["offers.read", "requests.read"]
GRANTABLE_PERMISSIONS = ["offers.accept", "requests.update"]
REDIRECT_URI = "http://testserver/api/v1/auth/callback"
VERIFIER = "v" * 64


async def _create_account(service: IamService, *, login: str = "grants.user") -> uuid.UUID:
    account_id = uuid.uuid4()
    await service.seed_rbac(
        {
            ROLE: ROLE_PERMISSIONS,
            "permission_catalog": GRANTABLE_PERMISSIONS,
        }
    )
    await service.create_account(
        account_id=account_id,
        login=login,
        role_name=ROLE,
        auth_status="active",
    )
    return account_id


@pytest.mark.asyncio
async def test_individual_grants_extend_role_permissions_without_duplicates(session) -> None:
    service = IamService(session)
    account_id = await _create_account(service)

    result = await service.replace_account_permission_grants(
        account_id=account_id,
        permission_names=["requests.update", "requests.read", "requests.update"],
    )

    assert result.permissions_from_role == sorted(ROLE_PERMISSIONS)
    assert result.individually_granted_permissions == ["requests.read", "requests.update"]
    assert result.effective_permissions == ["offers.read", "requests.read", "requests.update"]
    assert (await service.rbac_report())[ROLE] == sorted(ROLE_PERMISSIONS)

    repeated = await service.replace_account_permission_grants(
        account_id=account_id,
        permission_names=["requests.read", "requests.update"],
    )
    assert repeated == result
    events = [
        event
        for event in await AuditRepository(session).list_events()
        if event.event_type == "account.permissions.updated"
    ]
    assert len(events) == 1
    assert events[0].account_id == account_id
    assert events[0].session_id is None
    assert events[0].details == {
        "added": ["requests.read", "requests.update"],
        "removed": [],
    }


@pytest.mark.asyncio
async def test_removing_grants_preserves_permissions_from_role_and_audits_delta(session) -> None:
    service = IamService(session)
    account_id = await _create_account(service)
    await service.replace_account_permission_grants(
        account_id=account_id,
        permission_names=["offers.accept", "requests.read"],
    )

    result = await service.replace_account_permission_grants(
        account_id=account_id,
        permission_names=[],
    )

    assert result.individually_granted_permissions == []
    assert result.effective_permissions == sorted(ROLE_PERMISSIONS)
    events = [
        event
        for event in await AuditRepository(session).list_events()
        if event.event_type == "account.permissions.updated"
    ]
    assert {
        "added": [],
        "removed": ["offers.accept", "requests.read"],
    } in [event.details for event in events]


@pytest.mark.asyncio
async def test_unknown_or_inactive_permission_is_rejected_atomically(session) -> None:
    service = IamService(session)
    account_id = await _create_account(service)
    await service.replace_account_permission_grants(
        account_id=account_id,
        permission_names=["requests.update"],
    )
    inactive = await RoleRepository(session).get_permission_by_name("offers.accept")
    assert inactive is not None
    inactive.is_active = False
    await session.flush()

    with pytest.raises(Conflict):
        await service.replace_account_permission_grants(
            account_id=account_id,
            permission_names=["requests.update", "unknown.permission"],
        )
    with pytest.raises(Conflict):
        await service.replace_account_permission_grants(
            account_id=account_id,
            permission_names=["offers.accept"],
        )

    result = await service.get_account_permissions(account_id=account_id)
    assert result.individually_granted_permissions == ["requests.update"]


@pytest.mark.asyncio
async def test_access_token_uses_effective_permissions_after_login_and_refresh(session) -> None:
    service = IamService(session)
    account_id = uuid.uuid4()
    await service.seed_rbac(
        {
            ROLE: ROLE_PERMISSIONS,
            "permission_catalog": GRANTABLE_PERMISSIONS,
        }
    )
    await service.create_account(
        account_id=account_id,
        login="token.grants.user",
        role_name=ROLE,
        auth_status="pending",
    )
    setup_token, _ = await service.create_action_token(
        account_id=account_id,
        purpose="password_setup",
    )
    await service.consume_action_token(
        raw_token=setup_token,
        purpose="password_setup",
        new_password="correct horse battery staple",
    )
    await service.replace_account_permission_grants(
        account_id=account_id,
        permission_names=["offers.accept", "requests.read"],
    )
    authorization = await service.authenticate_and_create_code(
        login="token.grants.user",
        password="correct horse battery staple",
        state="state",
        pkce_challenge=pkce_s256(VERIFIER),
        redirect_uri=REDIRECT_URI,
    )
    bundle = await service.exchange_code(
        raw_code=authorization.code,
        code_verifier=VERIFIER,
        redirect_uri=REDIRECT_URI,
        ip_address=None,
        user_agent=None,
    )

    initial_claims = jwt.decode(
        bundle.access_token,
        settings.signing_public_key,
        algorithms=["RS256"],
        issuer=settings.issuer,
        audience=settings.audience,
    )
    assert initial_claims["permissions"] == ["offers.accept", "offers.read", "requests.read"]

    await service.replace_account_permission_grants(
        account_id=account_id,
        permission_names=["requests.update"],
    )
    refreshed = await service.refresh(raw_refresh_token=bundle.refresh_token)
    refreshed_claims = jwt.decode(
        refreshed.access_token,
        settings.signing_public_key,
        algorithms=["RS256"],
        issuer=settings.issuer,
        audience=settings.audience,
    )
    assert refreshed_claims["permissions"] == ["offers.read", "requests.read", "requests.update"]


def test_internal_permission_grants_api_requires_auth_and_returns_three_sets() -> None:
    headers = {"X-Acom-Service-Token": settings.internal_service_token}
    account_id = "2efc6d60-a4a6-4e11-8ac4-a3e4d21d679e"
    with TestClient(app) as client:
        client.put(
            "/internal/rbac",
            headers=headers,
            json={
                "roles": [
                    {"name": ROLE, "permissions": ROLE_PERMISSIONS},
                    {"name": "permission_catalog", "permissions": GRANTABLE_PERMISSIONS},
                ]
            },
        )
        client.put(
            f"/internal/accounts/{account_id}",
            headers=headers,
            json={"login": "api.grants.user", "role": ROLE, "auth_status": "active"},
        )

        forbidden_get = client.get(f"/internal/accounts/{account_id}/permissions")
        forbidden_put = client.put(
            f"/internal/accounts/{account_id}/permission-grants",
            json={"permissions": ["requests.update"]},
        )
        updated = client.put(
            f"/internal/accounts/{account_id}/permission-grants",
            headers=headers,
            json={"permissions": ["requests.update", "requests.read", "requests.update"]},
        )
        fetched = client.get(
            f"/internal/accounts/{account_id}/permissions",
            headers=headers,
        )
        unknown = client.put(
            f"/internal/accounts/{account_id}/permission-grants",
            headers=headers,
            json={"permissions": ["unknown.permission"]},
        )

    assert forbidden_get.status_code == 403
    assert forbidden_put.status_code == 403
    assert updated.status_code == 200
    assert updated.json() == {
        "permissions_from_role": sorted(ROLE_PERMISSIONS),
        "individually_granted_permissions": ["requests.read", "requests.update"],
        "effective_permissions": ["offers.read", "requests.read", "requests.update"],
    }
    assert fetched.json() == updated.json()
    assert unknown.status_code == 409
