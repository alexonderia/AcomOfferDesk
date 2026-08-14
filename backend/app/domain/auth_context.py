from __future__ import annotations

from dataclasses import dataclass

from app.domain.iam_roles import technical_role_name
from app.domain.permissions import get_permissions_for_role


@dataclass(frozen=True, slots=True)
class CurrentUser:
    user_id: str
    iam_account_id: str
    iam_session_id: str
    system_role: str
    role_id: int
    status: str
    permissions: frozenset[str]

    def has_permission(self, permission: str) -> bool:
        normalized_permission = permission.strip()
        return bool(normalized_permission and normalized_permission in self.permissions)


def build_current_user(*, user_id: str, role_id: int, status: str) -> CurrentUser:
    role_name = technical_role_name(role_id) or "unknown"
    return CurrentUser(
        user_id=user_id,
        iam_account_id=user_id,
        iam_session_id=user_id,
        system_role=role_name,
        role_id=role_id,
        status=status,
        permissions=get_permissions_for_role(role_id),
    )
