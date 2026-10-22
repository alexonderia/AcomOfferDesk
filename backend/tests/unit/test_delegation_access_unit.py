from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.v1 import users as users_api
from app.domain.auth_context import CurrentUser
from app.domain.exceptions import Forbidden


class _Uow:
    def __init__(self) -> None:
        self.users = object()
        self.profiles = object()
        self.user_auth_accounts = object()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _current_user() -> CurrentUser:
    return CurrentUser(
        user_id="viewer",
        iam_account_id="00000000-0000-4000-8000-000000000001",
        iam_session_id="00000000-0000-4000-8000-000000000002",
        system_role="economist",
        role_id=6,
        status="active",
        permissions=frozenset(),
        required_actions=frozenset(),
    )


@pytest.mark.asyncio
async def test_department_delegations_get_requires_manage_or_self(monkeypatch) -> None:
    service = SimpleNamespace(
        get_state=AsyncMock(return_value=SimpleNamespace(can_manage=False)),
    )
    monkeypatch.setattr(users_api, "UserDepartmentDelegationsService", lambda **_kwargs: service)

    with pytest.raises(Forbidden):
        await users_api.get_user_department_delegations(
            user_id="other-user",
            current_user=_current_user(),
            uow=_Uow(),
        )


@pytest.mark.asyncio
async def test_contractor_delegations_get_requires_manage_or_self(monkeypatch) -> None:
    service = SimpleNamespace(
        get_state=AsyncMock(return_value=SimpleNamespace(can_manage=False)),
    )
    monkeypatch.setattr(users_api, "UserContractorDelegationsService", lambda **_kwargs: service)

    with pytest.raises(Forbidden):
        await users_api.get_user_contractor_delegations(
            user_id="other-user",
            current_user=_current_user(),
            uow=_Uow(),
        )
