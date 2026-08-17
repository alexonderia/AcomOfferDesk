from __future__ import annotations

from dataclasses import dataclass

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
