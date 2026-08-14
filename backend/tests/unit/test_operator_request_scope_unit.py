"""Unit tests for operator request visibility scope."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.exceptions import Forbidden
from app.services.requests import RequestService


def _operator_user(*, user_id: str = "operator-1") -> CurrentUser:
    return CurrentUser(
        user_id=user_id,
        iam_account_id="00000000-0000-4000-8000-000000000001",
        iam_session_id="00000000-0000-4000-8000-000000000002",
        system_role="operator",
        role_id=settings.operator_role_id,
        status="active",
        permissions=frozenset(),
    )


@pytest.mark.asyncio
async def test_operator_visible_owner_scope_is_self_only() -> None:
    service = RequestService(
        requests=AsyncMock(),
        files=AsyncMock(),
        users=AsyncMock(),
        offers=AsyncMock(),
        user_status_periods=AsyncMock(),
    )

    owner_ids = await service._resolve_visible_owner_ids_for_staff_scope(current_user=_operator_user())

    assert owner_ids == ["operator-1"]


@pytest.mark.asyncio
async def test_operator_cannot_view_request_after_responsible_assigned() -> None:
    users = AsyncMock()
    users.get_by_id = AsyncMock(
        return_value=SimpleNamespace(id="eco-1", id_role=settings.economist_role_id, id_parent="lead-1")
    )
    service = RequestService(
        requests=AsyncMock(),
        files=AsyncMock(),
        users=users,
        offers=AsyncMock(),
        user_status_periods=AsyncMock(),
    )

    with pytest.raises(Forbidden, match="outside your management scope"):
        await service._ensure_can_view_request_in_staff_scope(
            current_user=_operator_user(),
            request_owner_user_id="eco-1",
        )


@pytest.mark.asyncio
async def test_operator_cannot_view_request_when_owner_role_is_no_longer_operator() -> None:
    users = AsyncMock()
    users.get_by_id = AsyncMock(
        return_value=SimpleNamespace(id="operator-1", id_role=settings.economist_role_id, id_parent="lead-1")
    )
    service = RequestService(
        requests=AsyncMock(),
        files=AsyncMock(),
        users=users,
        offers=AsyncMock(),
        user_status_periods=AsyncMock(),
    )

    with pytest.raises(Forbidden, match="no longer available for operator"):
        await service._ensure_can_view_request_in_staff_scope(
            current_user=_operator_user(),
            request_owner_user_id="operator-1",
        )


@pytest.mark.asyncio
async def test_operator_can_view_own_unassigned_request() -> None:
    users = AsyncMock()
    users.get_by_id = AsyncMock(
        return_value=SimpleNamespace(id="operator-1", id_role=settings.operator_role_id, id_parent=None)
    )
    service = RequestService(
        requests=AsyncMock(),
        files=AsyncMock(),
        users=users,
        offers=AsyncMock(),
        user_status_periods=AsyncMock(),
    )

    await service._ensure_can_view_request_in_staff_scope(
        current_user=_operator_user(),
        request_owner_user_id="operator-1",
    )
