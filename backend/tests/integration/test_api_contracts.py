"""Integration-style API contract tests.

Focus:
- request/offer payload contract shape (`actions` present, no duplicated global permissions);
- amount visibility rules in details responses;
- negative authorization scenarios returning 403.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from app.api.v1 import offers as offers_api
from app.api.v1 import requests as requests_api
from app.core.config import settings
from app.domain.exceptions import Forbidden
from app.domain.permissions import PermissionCodes
from app.schemas.actions import ChatActionsSchema, OfferActionsSchema, RequestActionsSchema
from app.services.requests import OfferedRequestOfferItem, OfferItem, OpenRequestListItem, RequestDetailItem, RequestFileItem, RequestListItem


def _dt() -> datetime:
    return datetime(2026, 5, 7, 10, 0, tzinfo=timezone.utc)


def test_requests_list_contract_has_item_actions_without_top_level_permissions(
    test_client,
    monkeypatch,
    set_current_user,
    make_current_user,
):
    user = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions={PermissionCodes.REQUESTS_READ, PermissionCodes.REQUESTS_AMOUNTS_READ},
    )
    set_current_user(user)

    async def _fake_list_requests(self, *, current_user):
        _ = current_user
        return [
            RequestListItem(
                request_id=1,
                description="Request 1",
                status="open",
                status_label="open",
                deadline_at=_dt(),
                created_at=_dt(),
                updated_at=_dt(),
                closed_at=None,
                owner_user_id="owner-1",
                owner_full_name="Owner",
                chosen_offer_id=None,
                id_plan=None,
                count_submitted=0,
                count_deleted_alert=0,
                count_accepted_total=0,
                count_rejected_total=0,
                unread_messages_count=0,
                files=[RequestFileItem(id=101, path="uploads/f1.pdf", name="f1.pdf")],
            )
        ]

    monkeypatch.setattr(requests_api.RequestService, "list_requests", _fake_list_requests)

    response = test_client.get("/api/v1/requests")

    assert response.status_code == 200
    data = response.json()["data"]
    assert "permissions" not in data
    assert len(data["items"]) == 1
    assert "actions" in data["items"][0]


def test_open_requests_contract_has_item_actions_without_top_level_permissions(
    test_client,
    monkeypatch,
    set_current_user,
    make_current_user,
):
    user = make_current_user(
        role_id=settings.contractor_role_id,
        permissions={PermissionCodes.REQUESTS_OPEN_READ, PermissionCodes.OFFERS_WORKSPACE_READ},
    )
    set_current_user(user)

    async def _fake_list_open_requests_for_contractor(self, *, current_user):
        _ = current_user
        return [
            OpenRequestListItem(
                request_id=2,
                description="Open request",
                status="open",
                status_label="open",
                deadline_at=_dt(),
                created_at=_dt(),
                updated_at=_dt(),
                closed_at=None,
                owner_user_id="owner-2",
                owner_full_name="Owner 2",
                chosen_offer_id=None,
                id_plan=None,
                files=[],
                offers=[OfferedRequestOfferItem(offer_id=50, status="submitted", unread_messages_count=0)],
                latest_offer_id=50,
                latest_offer_status="submitted",
            )
        ]

    monkeypatch.setattr(requests_api.RequestService, "list_open_requests_for_contractor", _fake_list_open_requests_for_contractor)

    response = test_client.get("/api/v1/requests/open")

    assert response.status_code == 200
    data = response.json()["data"]
    assert "permissions" not in data
    assert len(data["items"]) == 1
    assert "actions" in data["items"][0]


def test_request_details_contract_contains_actions_and_hides_amounts_without_permission(
    test_client,
    monkeypatch,
    set_current_user,
    make_current_user,
):
    user = make_current_user(
        role_id=settings.economist_role_id,
        permissions={PermissionCodes.REQUESTS_READ},
    )
    set_current_user(user)

    async def _fake_get_request_details(self, *, current_user, request_id):
        _ = (current_user, request_id)
        return RequestDetailItem(
            request_id=3,
            description="Detailed request",
            status="open",
            status_label="open",
            initial_amount=1500.0,
            final_amount=1200.0,
            deadline_at=_dt(),
            created_at=_dt(),
            updated_at=_dt(),
            closed_at=None,
            owner_user_id="owner-3",
            owner_full_name="Owner 3",
            chosen_offer_id=None,
            id_plan=None,
            count_submitted=1,
            count_deleted_alert=0,
            count_accepted_total=0,
            count_rejected_total=0,
            unread_messages_count=0,
            files=[],
            offers=[
                OfferItem(
                    offer_id=70,
                    contractor_user_id="contractor-1",
                    status="submitted",
                    status_label="submitted",
                    offer_amount=999.0,
                    created_at=_dt(),
                    updated_at=_dt(),
                    offer_workspace_url="/api/v1/offers/70/workspace",
                    contractor_full_name="Contractor",
                    contractor_phone=None,
                    contractor_mail=None,
                    contractor_inn=None,
                    contractor_company_name=None,
                    contractor_company_phone=None,
                    contractor_company_mail=None,
                    contractor_contact_phone=None,
                    contractor_contact_mail=None,
                    files=[],
                    unread_messages_count=0,
                )
            ],
        )

    monkeypatch.setattr(requests_api.RequestService, "get_request_details", _fake_get_request_details)

    def _fake_request_actions(*args, **kwargs):
        _ = (args, kwargs)
        return RequestActionsSchema(can_view_details=True, can_view_amounts=False)

    def _fake_offer_actions(*args, **kwargs):
        _ = (args, kwargs)
        return OfferActionsSchema(can_open_workspace=True)

    monkeypatch.setattr(requests_api.RequestActionBuilder, "build", staticmethod(_fake_request_actions))
    monkeypatch.setattr(requests_api.OfferActionBuilder, "build", staticmethod(_fake_offer_actions))

    response = test_client.get("/api/v1/requests/3")

    assert response.status_code == 200
    item = response.json()["data"]["item"]
    assert item["initial_amount"] is None
    assert item["final_amount"] is None
    assert "actions" in item
    assert item["offers"]
    assert "actions" in item["offers"][0]


def test_offer_workspace_contract_contains_request_offer_chat_actions(
    test_client,
    monkeypatch,
    set_current_user,
    make_current_user,
):
    user = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions={PermissionCodes.OFFERS_WORKSPACE_READ},
    )
    set_current_user(user)

    class _FakeOfferService:
        async def get_workspace(self, *, current_user, offer_id):
            _ = (current_user, offer_id)
            return SimpleNamespace(
                request=SimpleNamespace(
                    request_id=11,
                    description="Request",
                    status="open",
                    status_label="open",
                    initial_amount=500.0,
                    final_amount=400.0,
                    deadline_at=_dt(),
                    owner_user_id="owner-11",
                    owner_full_name="Owner",
                    created_at=_dt(),
                    updated_at=_dt(),
                    closed_at=None,
                    files=[],
                ),
                offer=SimpleNamespace(
                    offer_id=88,
                    status="submitted",
                    status_label="submitted",
                    offer_amount=390.0,
                    created_at=_dt(),
                    updated_at=_dt(),
                    files=[],
                ),
                offers=[],
                contractor=SimpleNamespace(
                    user_id="contractor-1",
                    full_name="Contractor",
                    phone=None,
                    mail=None,
                    company_name=None,
                    inn=None,
                    company_phone=None,
                    company_mail=None,
                    address=None,
                    note=None,
                ),
            )

    class _FakeResolver:
        async def resolve_workspace_context(self, *, current_user, offer_id):
            _ = (current_user, offer_id)
            return SimpleNamespace(
                offer_owner_user_id="contractor-1",
                request_owner_user_id="owner-11",
                request_id=11,
                offer_is_manual=False,
                can_create_new_offer=False,
                can_acknowledge_messages=True,
                offer_actions=OfferActionsSchema(can_open_workspace=True),
                chat_actions=ChatActionsSchema(can_view_messages=True),
            )

    monkeypatch.setattr(offers_api, "build_offer_service", lambda uow: _FakeOfferService())
    monkeypatch.setattr(offers_api, "_offer_action_resolver", lambda uow: _FakeResolver())
    monkeypatch.setattr(
        offers_api.RequestActionBuilder,
        "build",
        staticmethod(lambda *args, **kwargs: RequestActionsSchema(can_view_details=True, can_view_amounts=False)),
    )
    monkeypatch.setattr(
        offers_api.OfferActionBuilder,
        "build",
        staticmethod(lambda *args, **kwargs: OfferActionsSchema(can_open_workspace=True)),
    )

    response = test_client.get("/api/v1/offers/88/workspace")

    assert response.status_code == 200
    data = response.json()["data"]
    assert "permissions" not in data
    assert "actions" in data["request"]
    assert "actions" in data["offer"]
    assert "chat_actions" in data


def test_negative_authorization_file_download_forbidden_without_access(
    test_client,
    set_current_user,
    make_current_user,
):
    user = make_current_user(
        role_id=settings.contractor_role_id,
        permissions={PermissionCodes.REQUESTS_OPEN_READ},
    )
    set_current_user(user)

    response = test_client.get("/api/v1/files/1/download")

    assert response.status_code == 403


def test_negative_authorization_inactive_user_forbidden_even_with_permission(
    test_client,
    set_current_user,
    make_current_user,
):
    user = make_current_user(
        role_id=settings.lead_economist_role_id,
        status="inactive",
        permissions={PermissionCodes.FILES_DOWNLOAD},
    )
    set_current_user(user)

    response = test_client.get("/api/v1/files/1/download")

    assert response.status_code == 403


def test_negative_authorization_scope_forbidden_on_update(
    test_client,
    monkeypatch,
    set_current_user,
    make_current_user,
):
    user = make_current_user(
        role_id=settings.economist_role_id,
        permissions={PermissionCodes.REQUESTS_UPDATE},
    )
    set_current_user(user)

    async def _forbidden_update(self, *, current_user, request_id, data):
        _ = (self, current_user, request_id, data)
        raise Forbidden("Request is outside your management scope")

    monkeypatch.setattr(requests_api.RequestService, "update_request", _forbidden_update)

    response = test_client.patch(
        "/api/v1/requests/999",
        json={"status": "open"},
    )

    assert response.status_code == 403
