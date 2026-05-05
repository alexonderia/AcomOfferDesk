from __future__ import annotations

from dataclasses import dataclass

from app.domain.permissions import get_permissions_for_role


@dataclass(frozen=True, slots=True)
class CurrentUser:
    user_id: str
    role_id: int
    status: str
    permissions: frozenset[str]


def build_current_user(*, user_id: str, role_id: int, status: str) -> CurrentUser:
    return CurrentUser(
        user_id=user_id,
        role_id=role_id,
        status=status,
        permissions=get_permissions_for_role(role_id),
    )
