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
        identity_roles: set[str] | frozenset[str] | None = None,
        keycloak_roles: set[str] | frozenset[str] | None = None,
    ) -> CurrentUser:
        raw_permissions = permissions or set()
        raw_identity_roles = identity_roles or keycloak_roles or set(raw_permissions)
        return CurrentUser(
            user_id=user_id,
            role_id=role_id,
            status=status,
            permissions=frozenset(raw_permissions),
            identity_roles=frozenset(raw_identity_roles),
            app_roles=frozenset(role for role in raw_identity_roles if role.startswith("app.")),
            delegation_roles=frozenset(role for role in raw_identity_roles if role.startswith("delegation.")),
        )

    return _make_current_user
