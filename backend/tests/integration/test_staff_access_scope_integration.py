"""Integration tests for staff access scope and scope-aware request actions."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.api.v1 import requests as requests_api
from app.core.config import settings
from app.domain.permissions import PermissionCodes
from app.services.requests import RequestListItem, RequestFileItem
from tests.integration.conftest import DummyUow
from tests.integration.hierarchy_users_repo import HierarchyUsersRepo


def _dt() -> datetime:
    return datetime(2026, 5, 7, 10, 0, tzinfo=timezone.utc)


def _request_item(*, request_id: int, owner_user_id: str) -> RequestListItem:
    return RequestListItem(
        request_id=request_id,
        description=f"Request {request_id}",
        status="open",
        status_label="open",
        deadline_at=_dt(),
        created_at=_dt(),
        updated_at=_dt(),
        closed_at=None,
        owner_user_id=owner_user_id,
        owner_full_name=owner_user_id,
        chosen_offer_id=None,
        id_plan=None,
        count_submitted=0,
        count_deleted_alert=0,
        count_accepted_total=0,
        count_rejected_total=0,
        unread_messages_count=0,
        files=[RequestFileItem(id=request_id, path="uploads/f.pdf", name="f.pdf")],
    )


_LE_MANAGE_PERMISSIONS = {
    PermissionCodes.REQUESTS_READ,
    PermissionCodes.REQUESTS_UPDATE,
    PermissionCodes.REQUESTS_STATUS_UPDATE,
    PermissionCodes.REQUESTS_OWNER_CHANGE,
}

_ECONOMIST_MANAGE_PERMISSIONS = {
    PermissionCodes.REQUESTS_READ,
    PermissionCodes.REQUESTS_UPDATE,
    PermissionCodes.REQUESTS_STATUS_UPDATE,
}


@pytest.mark.parametrize(
    ("viewer_id", "owner_id", "expected_can_edit", "expected_can_change_owner"),
    [
        ("lead-1", "eco-1", True, True),
        ("eco-1", "eco-1", True, False),
        ("eco-1", "eco-2", False, False),
        ("eco-1", "eco-3", False, False),
        ("pm-1", "eco-1", False, True),
        ("pm-1", "eco-3", False, True),
    ],
)
def test_request_list_actions_reflect_hierarchy_management_scope(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
    viewer_id: str,
    owner_id: str,
    expected_can_edit: bool,
    expected_can_change_owner: bool,
):
    role_by_user = {
        "pm-1": settings.project_manager_role_id,
        "lead-1": settings.lead_economist_role_id,
        "eco-1": settings.economist_role_id,
        "eco-2": settings.economist_role_id,
        "eco-3": settings.economist_role_id,
    }
    permissions = (
        {
            PermissionCodes.REQUESTS_READ,
            PermissionCodes.REQUESTS_OWNER_CHANGE,
        }
        if viewer_id == "pm-1"
        else (
            _ECONOMIST_MANAGE_PERMISSIONS
            if role_by_user[viewer_id] == settings.economist_role_id
            else _LE_MANAGE_PERMISSIONS
        )
    )

    set_current_user(
        make_current_user(
            user_id=viewer_id,
            role_id=role_by_user[viewer_id],
            permissions=permissions,
        )
    )
    uow = DummyUow()
    uow.users = HierarchyUsersRepo()
    set_uow(uow)

    async def _fake_list_requests(self, *, current_user):
        _ = current_user
        return [_request_item(request_id=1, owner_user_id=owner_id)]

    monkeypatch.setattr(requests_api.RequestService, "list_requests", _fake_list_requests)

    response = test_client.get("/api/v1/requests")

    assert response.status_code == 200
    actions = response.json()["data"]["items"][0]["actions"]
    assert actions["can_edit"] is expected_can_edit
    assert actions["can_change_owner"] is expected_can_change_owner


def test_project_manager_can_change_owner_in_actions_without_edit_permission(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    set_current_user(
        make_current_user(
            user_id="pm-1",
            role_id=settings.project_manager_role_id,
            permissions={
                PermissionCodes.REQUESTS_READ,
                PermissionCodes.REQUESTS_OWNER_CHANGE,
            },
        )
    )
    uow = DummyUow()
    uow.users = HierarchyUsersRepo()
    set_uow(uow)

    async def _fake_list_requests(self, *, current_user):
        _ = current_user
        return [_request_item(request_id=5, owner_user_id="eco-1")]

    monkeypatch.setattr(requests_api.RequestService, "list_requests", _fake_list_requests)

    response = test_client.get("/api/v1/requests")

    assert response.status_code == 200
    actions = response.json()["data"]["items"][0]["actions"]
    assert actions["can_edit"] is False
    assert actions["can_upload_files"] is False
    assert actions["can_change_owner"] is True


def test_peer_economist_sees_department_request_but_cannot_edit(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    set_current_user(
        make_current_user(
            user_id="eco-1",
            role_id=settings.economist_role_id,
            permissions=_ECONOMIST_MANAGE_PERMISSIONS,
        )
    )
    uow = DummyUow()
    uow.users = HierarchyUsersRepo()
    set_uow(uow)

    async def _fake_list_requests(self, *, current_user):
        _ = current_user
        return [_request_item(request_id=9, owner_user_id="eco-2")]

    monkeypatch.setattr(requests_api.RequestService, "list_requests", _fake_list_requests)

    response = test_client.get("/api/v1/requests")

    assert response.status_code == 200
    actions = response.json()["data"]["items"][0]["actions"]
    assert actions["can_view_details"] is True
    assert actions["can_edit"] is False


def test_department_delegation_grants_manage_scope_without_economist_edit_actions(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    """Service layer may edit via department.*; action flags still block peer economist edit."""
    set_current_user(
        make_current_user(
            user_id="eco-1",
            role_id=settings.economist_role_id,
            permissions={
                PermissionCodes.REQUESTS_READ,
                PermissionCodes.REQUESTS_UPDATE,
                PermissionCodes.DEPARTMENT_REQUESTS_UPDATE,
            },
        )
    )
    uow = DummyUow()
    uow.users = HierarchyUsersRepo()
    set_uow(uow)

    async def _fake_list_requests(self, *, current_user):
        _ = current_user
        return [_request_item(request_id=12, owner_user_id="eco-3")]

    monkeypatch.setattr(requests_api.RequestService, "list_requests", _fake_list_requests)

    response = test_client.get("/api/v1/requests")

    assert response.status_code == 200
    actions = response.json()["data"]["items"][0]["actions"]
    assert actions["can_edit"] is False
    assert actions["can_change_owner"] is False
