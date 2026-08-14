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
