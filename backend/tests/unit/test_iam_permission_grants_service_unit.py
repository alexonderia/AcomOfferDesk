from __future__ import annotations

import pytest

from app.infrastructure.iam_client import IamAccountPermissions
from app.services.iam_permission_grants import IamPermissionGrantsService


class _IamClient:
    def __init__(self) -> None:
        self.permissions = IamAccountPermissions(
            permissions_from_role=frozenset({"department.requests.read"}),
            individually_granted_permissions=frozenset(
                {
                    "department.requests.update",
                    "contractors.profile.status.update",
                    "unrelated.permission",
                }
            ),
            effective_permissions=frozenset(
                {
                    "department.requests.read",
                    "department.requests.update",
                    "contractors.profile.status.update",
                    "unrelated.permission",
                }
            ),
        )
        self.put_calls: list[frozenset[str]] = []

    async def get_account_permissions(self, *, account_id: str):
        assert account_id == "iam-account-id"
        return self.permissions

    async def replace_account_permission_grants(
        self,
        *,
        account_id: str,
        permissions: frozenset[str],
    ):
        assert account_id == "iam-account-id"
        self.put_calls.append(permissions)
        self.permissions = IamAccountPermissions(
            permissions_from_role=self.permissions.permissions_from_role,
            individually_granted_permissions=permissions,
            effective_permissions=self.permissions.permissions_from_role | permissions,
        )
        return self.permissions


@pytest.mark.asyncio
async def test_replaces_only_managed_subset_and_preserves_unrelated_grants() -> None:
    client = _IamClient()
    service = IamPermissionGrantsService(client)

    result = await service.replace_managed_grants(
        account_id="iam-account-id",
        managed_permissions=frozenset(
            {
                "department.requests.read",
                "department.requests.update",
                "department.offers.accept",
            }
        ),
        requested_permissions=frozenset({"department.offers.accept"}),
    )

    assert result.changed is True
    assert client.put_calls == [
        frozenset(
            {
                "department.offers.accept",
                "contractors.profile.status.update",
                "unrelated.permission",
            }
        )
    ]
    assert "department.requests.read" in result.permissions.effective_permissions
    assert "department.requests.read" not in result.permissions.individually_granted_permissions


@pytest.mark.asyncio
async def test_repeated_save_is_idempotent_and_skips_duplicate_put() -> None:
    client = _IamClient()
    service = IamPermissionGrantsService(client)
    requested = frozenset({"department.requests.update"})
    managed = frozenset(
        {
            "department.requests.read",
            "department.requests.update",
            "department.offers.accept",
        }
    )

    first = await service.replace_managed_grants(
        account_id="iam-account-id",
        managed_permissions=managed,
        requested_permissions=requested,
    )
    second = await service.replace_managed_grants(
        account_id="iam-account-id",
        managed_permissions=managed,
        requested_permissions=requested,
    )

    assert first.changed is False
    assert second.changed is False
    assert client.put_calls == []
