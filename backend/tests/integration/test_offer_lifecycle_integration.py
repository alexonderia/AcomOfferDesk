"""Integration-style tests for offer lifecycle business scenarios."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.api.v1 import offers as offers_api
from app.core.config import settings
from app.domain.exceptions import Forbidden
from app.domain.permissions import PermissionCodes
from app.schemas.actions import ChatActionsSchema, OfferActionsSchema, RequestActionsSchema


def _dt() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=14)


class _OfferRequestsRepo:
    def __init__(self, *, request_row: SimpleNamespace | None = None, visible_open: bool = True) -> None:
        self._request_row = request_row or SimpleNamespace(
            id=10,
            id_user="owner-1",
            status="open",
            description="Open request",
            deadline_at=_dt(),
            initial_amount=100.0,
            final_amount=100.0,
            created_at=_dt(),
            updated_at=_dt(),
            closed_at=None,
            id_offer=None,
            id_plan=None,
        )
        self._visible_open = visible_open

    async def get_visible_open_by_id_for_contractor(self, *, request_id: int, contractor_user_id: str):
        _ = contractor_user_id
        if not self._visible_open:
            return None
        if request_id != self._request_row.id:
            return None
        if self._request_row.status != "open":
            return None
        return self._request_row

    async def get_by_id(self, *, request_id: int):
        return self._request_row if request_id == self._request_row.id else None

    async def is_hidden_for_contractor(self, *, request_id: int, contractor_user_id: str) -> bool:
        _ = (request_id, contractor_user_id)
        return False


class _OfferRepo:
    def __init__(self) -> None:
        self._offers: dict[int, SimpleNamespace] = {}
        self._next_id = 100

    async def get_contractor_offer_for_request(self, *, request_id: int, contractor_user_id: str):
        for offer in self._offers.values():
            if offer.id_request == request_id and offer.id_user == contractor_user_id:
                return offer
        return None

    async def create(self, *, request_id: int, contractor_user_id: str, offer_amount: float | None = None):
        offer = SimpleNamespace(
            id=self._next_id,
            id_request=request_id,
            id_user=contractor_user_id,
            status="submitted",
            offer_amount=offer_amount,
            created_at=_dt(),
            updated_at=_dt(),
        )
        self._offers[self._next_id] = offer
        self._next_id += 1
        return offer

    async def get_by_id(self, *, offer_id: int):
        return self._offers.get(offer_id)

    async def update_amount(self, *, offer, offer_amount: float) -> None:
        offer.offer_amount = offer_amount

    async def update_status(self, *, offer, status: str) -> None:
        offer.status = status

    async def list_offer_files(self, *, offer_id: int):
        _ = offer_id
        return []

    async def list_offer_files_by_offer_ids(self, *, offer_ids):
        _ = offer_ids
        return []

    async def list_by_request(self, *, request_id: int):
        return [offer for offer in self._offers.values() if offer.id_request == request_id]

    async def get_chat(self, *, offer_id: int):
        return SimpleNamespace(id=offer_id, last_message_id=None, last_message_at=None)


class _NoopUsersRepo:
    async def get_by_id(self, user_id: str | None = None):
        _ = user_id
        return SimpleNamespace(id="contractor-1", id_role=settings.contractor_role_id, tg_user_id="tg-1")

    async def get_active_approved_contractor_tg_id(self, *, user_id: str, contractor_role_id: int):
        _ = (user_id, contractor_role_id)
        return None


class _NoopChatsRepo:
    async def get_chat_state_for_user(self, *, chat_id: int, user_id: str):
        _ = (chat_id, user_id)
        return None


class _NoopMessagesRepo:
    pass


class _NoopProfilesRepo:
    async def get_by_id(self, user_id: str):
        return SimpleNamespace(id=user_id, full_name="Name", phone=None, mail=None)


class _NoopCompanyContactsRepo:
    async def get_by_id(self, user_id: str):
        _ = user_id
        return None


class _OfferLifecycleUow:
    def __init__(self, *, request_row: SimpleNamespace | None = None, visible_open: bool = True) -> None:
        self.requests = _OfferRequestsRepo(request_row=request_row, visible_open=visible_open)
        self.offers = _OfferRepo()
        self.chats = _NoopChatsRepo()
        self.files = object()
        self.messages = _NoopMessagesRepo()
        self.profiles = _NoopProfilesRepo()
        self.company_contacts = _NoopCompanyContactsRepo()
        self.users = _NoopUsersRepo()
        self.user_status_periods = None
        self.feedback = None
        self.tg_users = None
        self.user_auth_accounts = None
        self.user_contact_channels = None
        self.economy_plans = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        _ = (exc_type, exc, tb)


def test_contractor_can_create_offer_for_open_request(test_client, set_uow, set_current_user, make_current_user):
    uow = _OfferLifecycleUow()
    set_uow(uow)
    contractor = make_current_user(
        user_id="contractor-1",
        role_id=settings.contractor_role_id,
        permissions={PermissionCodes.OFFERS_CREATE},
    )
    set_current_user(contractor)

    response = test_client.post("/api/v1/requests/10/offers", json={"offer_amount": 90.0})

    assert response.status_code == 200
    assert response.json()["data"]["request_id"] == 10


def test_contractor_cannot_create_offer_when_request_is_not_visible(
    test_client,
    set_uow,
    set_current_user,
    make_current_user,
):
    set_uow(_OfferLifecycleUow(visible_open=False))
    contractor = make_current_user(
        user_id="contractor-1",
        role_id=settings.contractor_role_id,
        permissions={PermissionCodes.OFFERS_CREATE},
    )
    set_current_user(contractor)

    response = test_client.post("/api/v1/requests/10/offers", json={"offer_amount": 90.0})

    assert response.status_code == 404


def test_contractor_can_edit_only_own_offer_amount(
    test_client,
    set_uow,
    set_current_user,
    make_current_user,
):
    uow = _OfferLifecycleUow()

    # Seed offer owned by another contractor.
    uow.offers._offers[200] = SimpleNamespace(
        id=200,
        id_request=10,
        id_user="contractor-2",
        status="submitted",
        offer_amount=100.0,
        created_at=_dt(),
        updated_at=_dt(),
    )
    set_uow(uow)
    contractor = make_current_user(
        user_id="contractor-1",
        role_id=settings.contractor_role_id,
        permissions={PermissionCodes.OFFERS_AMOUNT_UPDATE},
    )
    set_current_user(contractor)

    response = test_client.patch("/api/v1/offers/200", json={"offer_amount": 95.0})

    assert response.status_code == 403


def test_employee_with_manual_offer_permission_can_create_manual_offer(
    test_client,
    monkeypatch,
    set_current_user,
    make_current_user,
):
    class _FakeOfferService:
        async def create_manual_offer(
            self,
            *,
            current_user,
            request_id,
            contractor_user_id,
            contractor_data,
            offer_amount,
            files,
        ):
            _ = (contractor_user_id, contractor_data, offer_amount, files)
            if PermissionCodes.OFFERS_MANUAL_CREATE not in current_user.permissions:
                raise Forbidden("Insufficient permissions to create manual offer")
            return SimpleNamespace(
                offer_id=301,
                request_id=request_id,
                contractor_user_id="contractor-1",
                contractor_created=False,
            )

    monkeypatch.setattr(offers_api, "build_offer_service", lambda uow, file_service=None: _FakeOfferService())

    economist = make_current_user(
        role_id=settings.economist_role_id,
        permissions={PermissionCodes.OFFERS_MANUAL_CREATE},
    )
    set_current_user(economist)

    response = test_client.post(
        "/api/v1/requests/10/offers/manual",
        data={"contractor_mode": "existing", "contractor_user_id": "contractor-1"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["offer_id"] == 301


def test_accept_offer_requires_status_update_permission(
    test_client,
    set_uow,
    set_current_user,
    make_current_user,
):
    uow = _OfferLifecycleUow()
    uow.offers._offers[210] = SimpleNamespace(
        id=210,
        id_request=10,
        id_user="contractor-1",
        status="submitted",
        offer_amount=100.0,
        created_at=_dt(),
        updated_at=_dt(),
    )
    set_uow(uow)
    user = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions={PermissionCodes.REQUESTS_UPDATE},
    )
    set_current_user(user)

    response = test_client.patch("/api/v1/offers/210/status", json={"status": "accepted"})

    assert response.status_code == 403


def test_accepting_offer_changes_only_target_offer_status_in_current_implementation(
    test_client,
    set_uow,
    set_current_user,
    make_current_user,
):
    uow = _OfferLifecycleUow()
    uow.offers._offers[221] = SimpleNamespace(
        id=221,
        id_request=10,
        id_user="contractor-1",
        status="submitted",
        offer_amount=95.0,
        created_at=_dt(),
        updated_at=_dt(),
    )
    uow.offers._offers[222] = SimpleNamespace(
        id=222,
        id_request=10,
        id_user="contractor-2",
        status="submitted",
        offer_amount=97.0,
        created_at=_dt(),
        updated_at=_dt(),
    )
    set_uow(uow)
    user = make_current_user(
        user_id="owner-1",
        role_id=settings.lead_economist_role_id,
        permissions={PermissionCodes.OFFERS_STATUS_UPDATE, PermissionCodes.REQUESTS_UPDATE},
    )
    set_current_user(user)

    response = test_client.patch("/api/v1/offers/221/status", json={"status": "accepted"})

    assert response.status_code == 200
    assert uow.offers._offers[221].status == "accepted"
    assert uow.offers._offers[222].status == "submitted"


@pytest.mark.xfail(reason="Business rule is not implemented yet: closed/cancelled request guard on offer accept")
def test_cannot_accept_offer_for_closed_or_cancelled_request(
    test_client,
    set_uow,
    set_current_user,
    make_current_user,
):
    closed_request = SimpleNamespace(
        id=10,
        id_user="owner-1",
        status="closed",
        description="Closed request",
        deadline_at=_dt(),
        initial_amount=100.0,
        final_amount=100.0,
        created_at=_dt(),
        updated_at=_dt(),
        closed_at=_dt(),
        id_offer=None,
        id_plan=None,
    )
    uow = _OfferLifecycleUow(request_row=closed_request)
    uow.offers._offers[230] = SimpleNamespace(
        id=230,
        id_request=10,
        id_user="contractor-1",
        status="submitted",
        offer_amount=100.0,
        created_at=_dt(),
        updated_at=_dt(),
    )
    set_uow(uow)
    user = make_current_user(
        user_id="owner-1",
        role_id=settings.lead_economist_role_id,
        permissions={PermissionCodes.OFFERS_STATUS_UPDATE, PermissionCodes.REQUESTS_UPDATE},
    )
    set_current_user(user)

    response = test_client.patch("/api/v1/offers/230/status", json={"status": "accepted"})

    assert response.status_code == 409


def test_workspace_access_is_restricted_to_allowed_users(
    test_client,
    monkeypatch,
    set_current_user,
    make_current_user,
):
    class _FakeOfferService:
        async def get_workspace(self, *, current_user, offer_id):
            _ = offer_id
            if current_user.user_id != "contractor-1":
                raise Forbidden("Insufficient permissions to view workspace")
            return SimpleNamespace(
                request=SimpleNamespace(
                    request_id=10,
                    description="Request",
                    status="open",
                    status_label="open",
                    initial_amount=100.0,
                    final_amount=90.0,
                    deadline_at=_dt(),
                    owner_user_id="owner-1",
                    owner_full_name="Owner",
                    created_at=_dt(),
                    updated_at=_dt(),
                    closed_at=None,
                    files=[],
                ),
                offer=SimpleNamespace(
                    offer_id=400,
                    status="submitted",
                    status_label="submitted",
                    offer_amount=90.0,
                    created_at=_dt(),
                    updated_at=_dt(),
                    files=[],
                ),
                offers=[],
                contractor=SimpleNamespace(
                    user_id="contractor-1",
                    full_name="Contractor One",
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
                request_owner_user_id="owner-1",
                request_id=10,
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
        staticmethod(lambda *args, **kwargs: RequestActionsSchema(can_view_details=True, can_view_amounts=True)),
    )
    monkeypatch.setattr(
        offers_api.OfferActionBuilder,
        "build",
        staticmethod(lambda *args, **kwargs: OfferActionsSchema(can_open_workspace=True)),
    )

    outsider = make_current_user(
        user_id="contractor-2",
        role_id=settings.contractor_role_id,
        permissions={PermissionCodes.OFFERS_WORKSPACE_READ},
    )
    set_current_user(outsider)
    denied = test_client.get("/api/v1/offers/400/workspace")
    assert denied.status_code == 403

    owner = make_current_user(
        user_id="contractor-1",
        role_id=settings.contractor_role_id,
        permissions={PermissionCodes.OFFERS_WORKSPACE_READ},
    )
    set_current_user(owner)
    allowed = test_client.get("/api/v1/offers/400/workspace")
    assert allowed.status_code == 200
    assert "actions" in allowed.json()["data"]["offer"]
