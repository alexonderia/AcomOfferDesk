"""Shared fixtures for unit tests.

`make_current_user` builds lightweight `CurrentUser` objects to avoid
heavy mocking and keep tests fast/readable.
"""

from __future__ import annotations

import pytest

from app.core.config import settings
from app.domain.auth_context import CurrentUser


@pytest.fixture
def make_current_user():
    def _make_current_user(
        *,
        user_id: str = "user-1",
        role_id: int = settings.economist_role_id,
        status: str = "active",
        permissions: set[str] | frozenset[str] | None = None,
    ) -> CurrentUser:
        raw_permissions = permissions or set()
        return CurrentUser(
            user_id=user_id,
            iam_account_id="00000000-0000-4000-8000-000000000001",
            iam_session_id="00000000-0000-4000-8000-000000000002",
            system_role="economist",
            role_id=role_id,
            status=status,
            permissions=frozenset(raw_permissions),
        )

    return _make_current_user
