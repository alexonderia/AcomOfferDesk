from __future__ import annotations

from dataclasses import dataclass

from app.infrastructure.iam_client import IamAccountPermissions, IamClient


@dataclass(frozen=True, slots=True)
class ManagedPermissionGrantsResult:
    permissions: IamAccountPermissions
    changed: bool


class IamPermissionGrantsService:
    def __init__(self, iam_client: IamClient | None = None) -> None:
        self._iam_client = iam_client or IamClient()

    async def get(self, *, account_id: str) -> IamAccountPermissions:
        return await self._iam_client.get_account_permissions(account_id=account_id)

    async def replace_managed_grants(
        self,
        *,
        account_id: str,
        managed_permissions: frozenset[str],
        requested_permissions: frozenset[str],
    ) -> ManagedPermissionGrantsResult:
        if not requested_permissions.issubset(managed_permissions):
            raise ValueError("requested permissions must belong to the managed subset")
        current = await self.get(account_id=account_id)
        next_grants = (
            current.individually_granted_permissions - managed_permissions
        ) | requested_permissions
        changed = next_grants != current.individually_granted_permissions
        if not changed:
            return ManagedPermissionGrantsResult(permissions=current, changed=False)
        updated = await self._iam_client.replace_account_permission_grants(
            account_id=account_id,
            permissions=next_grants,
        )
        return ManagedPermissionGrantsResult(permissions=updated, changed=True)
