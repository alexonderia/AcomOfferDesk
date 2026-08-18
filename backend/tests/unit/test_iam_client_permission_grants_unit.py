from __future__ import annotations

import json

import httpx
import pytest

from app.core.config import settings
from app.infrastructure.iam_client import IamClient


@pytest.mark.asyncio
async def test_iam_client_reads_and_replaces_individual_permission_grants() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.headers["X-Acom-Service-Token"] == settings.iam_internal_service_token
        return httpx.Response(
            200,
            json={
                "permissions_from_role": ["requests.read"],
                "individually_granted_permissions": ["requests.update"],
                "effective_permissions": ["requests.read", "requests.update"],
            },
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="http://iam.test",
    ) as http_client:
        client = IamClient(http_client)
        fetched = await client.get_account_permissions(account_id="account-1")
        updated = await client.replace_account_permission_grants(
            account_id="account-1",
            permissions=frozenset({"requests.update"}),
        )

    assert fetched == updated
    assert requests[0].method == "GET"
    assert requests[0].url.path == "/internal/accounts/account-1/permissions"
    assert requests[1].method == "PUT"
    assert requests[1].url.path == "/internal/accounts/account-1/permission-grants"
    assert json.loads(requests[1].content) == {"permissions": ["requests.update"]}


@pytest.mark.asyncio
async def test_iam_client_provisions_registration_credentials_and_reads_password_set_only() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/credential-state"):
            return httpx.Response(
                200,
                json={
                    "id": "account-1",
                    "login": "new.user",
                    "role": "contractor",
                    "auth_status": "pending",
                    "password_set": True,
                },
            )
        return httpx.Response(
            200,
            json={
                "id": "account-1",
                "login": "new.user",
                "role": "contractor",
                "auth_status": "pending",
                "password_set": True,
                "created": True,
            },
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="http://iam.test",
    ) as http_client:
        client = IamClient(http_client)
        created = await client.provision_registration_credentials(
            account_id="account-1",
            login="new.user",
            role="contractor",
            password="correct horse battery staple",
        )
        state = await client.get_credential_state(account_id="account-1")

    assert created.password_set is True
    assert state.password_set is True
    assert requests[0].url.path == "/internal/accounts/account-1/registration-credentials"
    assert "correct horse battery staple" not in str(state)

