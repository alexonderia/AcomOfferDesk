"""Integration-style tests for request lifecycle auth/enforcement scenarios."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.api.dependencies import get_current_user
from app.api.v1 import offers as offers_api
from app.api.v1 import requests as requests_api
from app.core.config import settings
from app.domain.exceptions import Forbidden, Unauthorized
from app.domain.permissions import PermissionCodes, get_role_permissions_map
from app.domain.policies import UserPolicy
from app.services.requests import OfferItem, RequestDetailItem


def _future_dt() -> datetime:
    return datetime.utcnow().replace(microsecond=0) + timedelta(days=30)


def _now() -> datetime:
    return datetime(2026, 5, 12, 12, 0, tzinfo=timezone.utc)


class _MutableRequestsRepo:
    def __init__(self, request_row: SimpleNamespace, *, accepted_offer_id: int | None = None) -> None:
        self.request_row = request_row
        self.accepted_offer_id = accepted_offer_id

    async def get_by_id(self, *, request_id: int):
        return self.request_row if self.request_row.id == request_id else None

    async def update_initial_amount(self, *, request, initial_amount: float) -> None:
        request.initial_amount = initial_amount

    async def update_final_amount(self, *, request, final_amount: float) -> None:
        request.final_amount = final_amount

    async def update_status(self, *, request, status: str, closed_at, chosen_offer_id) -> None:
        request.status = status
        request.closed_at = closed_at
        request.id_offer = chosen_offer_id

    async def get_latest_accepted_offer_id(self, *, request_id: int):
        _ = request_id
        return self.accepted_offer_id

    async def update_deadline(self, *, request, deadline_at: datetime) -> None:
        request.deadline_at = deadline_at

    async def update_owner(self, *, request, user_id: str) -> None:
        request.id_user = user_id

    async def update_plan(self, *, request, plan_id: int | None) -> None:
        request.id_plan = plan_id

    async def get_economy_plan_owner_user_id(self, *, plan_id: int):
        _ = plan_id
        return "owner-1"


class _OffersRepo:
    def __init__(self, offers_by_id: dict[int, SimpleNamespace] | None = None) -> None:
        self._offers_by_id = offers_by_id or {}

    async def get_by_id(self, *, offer_id: int):
        return self._offers_by_id.get(offer_id)

    async def list_contractor_tg_ids_for_request(self, *, request_id: int, contractor_role_id: int):
        _ = (request_id, contractor_role_id)
        return []


class _UsersRepo:
    def __init__(self, users_by_id: dict[str, SimpleNamespace] | None = None) -> None:
        self._users_by_id = users_by_id or {}

    async def get_by_id(self, user_id: str):
        return self._users_by_id.get(user_id)

    async def list_active_user_parent_pairs(self):
        return []


class _UserStatusPeriodsRepo:
    async def get_active_for_user(self, *, user_id: str):
        _ = user_id
        return None


class _RequestLifecycleUow:
    def __init__(self, request_row: SimpleNamespace, *, accepted_offer_amount: float | None = None) -> None:
        accepted_offer_id = 501 if accepted_offer_amount is not None else None
        offers_by_id = (
            {accepted_offer_id: SimpleNamespace(id=accepted_offer_id, offer_amount=accepted_offer_amount)}
            if accepted_offer_id is not None
            else {}
        )
        self.requests = _MutableRequestsRepo(request_row, accepted_offer_id=accepted_offer_id)
        self.files = object()
        self.users = _UsersRepo(
            users_by_id={
                "owner-1": SimpleNamespace(id="owner-1", id_parent=None, id_role=settings.economist_role_id),
                "owner-2": SimpleNamespace(id="owner-2", id_parent="owner-1", id_role=settings.economist_role_id),
            }
        )
        self.offers = _OffersRepo(offers_by_id=offers_by_id)
        self.user_status_periods = _UserStatusPeriodsRepo()
        self.profiles = None
        self.chats = None
        self.messages = None
        self.company_contacts = None
        self.feedback = None
        self.tg_users = None
        self.user_auth_accounts = None
        self.user_contact_channels = None
        self.economy_plans = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)


def _request_row(*, status: str = "open", initial: float = 100.0, final: float = 100.0) -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        id_user="owner-1",
        status=status,
        initial_amount=initial,
        final_amount=final,
        id_offer=None,
        closed_at=None,
        deadline_at=_future_dt(),
        created_at=_now(),
        updated_at=_now(),
        description="Request",
        id_plan=None,
    )


def _role_user(make_current_user, role_id: int):
    return make_current_user(
        user_id=f"user-{role_id}",
        role_id=role_id,
        permissions=set(get_role_permissions_map()[role_id]),
    )


@pytest.mark.parametrize(
    "role_id",
    [
        settings.superadmin_role_id,
        settings.lead_economist_role_id,
        settings.economist_role_id,
        settings.operator_role_id,
    ],
)
def test_allowed_roles_can_create_request(test_client, monkeypatch, set_current_user, make_current_user, role_id: int):
    user = _role_user(make_current_user, role_id)
    set_current_user(user)

    async def _guarded_create_request(
        self,
        *,
        current_user,
        deadline_at,
        description,
        initial_amount,
        id_plan,
        files,
        additional_emails,
        hidden_contractor_ids,
    ):
        _ = (self, deadline_at, description, initial_amount, id_plan, files, additional_emails, hidden_contractor_ids)
        UserPolicy.ensure_can_create_request(current_user)
        UserPolicy.ensure_can_view_normative_files(current_user)
        return 700, [701]

    monkeypatch.setattr(requests_api.RequestService, "create_request", _guarded_create_request)

    response = test_client.post(
        "/api/v1/requests",
        data={"deadline_at": _future_dt().isoformat(), "description": "Created in test"},
        files=[("files", ("evidence.txt", b"request payload", "text/plain"))],
    )

    assert response.status_code == 200
    assert response.json()["data"]["request_id"] == 700


@pytest.mark.parametrize(
    "role_id",
    [
        settings.admin_role_id,
        settings.project_manager_role_id,
        settings.contractor_role_id,
    ],
)
def test_forbidden_roles_cannot_create_request(test_client, monkeypatch, set_current_user, make_current_user, role_id: int):
    user = _role_user(make_current_user, role_id)
    set_current_user(user)

    async def _guarded_create_request(
        self,
        *,
        current_user,
        deadline_at,
        description,
        initial_amount,
        id_plan,
        files,
        additional_emails,
        hidden_contractor_ids,
    ):
        _ = (self, deadline_at, description, initial_amount, id_plan, files, additional_emails, hidden_contractor_ids)
        UserPolicy.ensure_can_create_request(current_user)
        UserPolicy.ensure_can_view_normative_files(current_user)
        return 700, [701]

    monkeypatch.setattr(requests_api.RequestService, "create_request", _guarded_create_request)

    response = test_client.post(
        "/api/v1/requests",
        data={"deadline_at": _future_dt().isoformat(), "description": "Created in test"},
        files=[("files", ("evidence.txt", b"request payload", "text/plain"))],
    )

    assert response.status_code == 403


def test_contractor_cannot_access_internal_request_representation(test_client, set_current_user, make_current_user):
    contractor = _role_user(make_current_user, settings.contractor_role_id)
    set_current_user(contractor)

    response = test_client.get("/api/v1/requests/1")

    assert response.status_code == 403


def test_contractor_can_access_contractor_view_only_when_permission_allows(
    test_client,
    monkeypatch,
    set_current_user,
    make_current_user,
):
    class _FakeOfferService:
        async def get_request_view(self, *, current_user, request_id):
            _ = request_id
            if PermissionCodes.REQUESTS_CONTRACTOR_VIEW_READ not in current_user.permissions:
                raise Forbidden("Insufficient permissions for contractor request view")
            return SimpleNamespace(
                request_id=11,
                description="Visible contractor request",
                status="open",
                status_label="open",
                deadline_at=_future_dt(),
                owner_user_id="owner-1",
                owner_full_name="Owner",
                files=[],
                existing_offer=None,
            )

    monkeypatch.setattr(offers_api, "build_offer_service", lambda uow: _FakeOfferService())

    denied_user = make_current_user(
        role_id=settings.contractor_role_id,
        permissions={PermissionCodes.OFFERS_CREATE},
    )
    set_current_user(denied_user)
    denied = test_client.get("/api/v1/requests/11/contractor-view")
    assert denied.status_code == 403

    allowed_user = make_current_user(
        role_id=settings.contractor_role_id,
        permissions={PermissionCodes.OFFERS_CREATE, PermissionCodes.REQUESTS_CONTRACTOR_VIEW_READ},
    )
    set_current_user(allowed_user)
    allowed = test_client.get("/api/v1/requests/11/contractor-view")

    assert allowed.status_code == 200
    assert "actions" in allowed.json()["data"]


def test_update_request_deadline_requires_deadline_permission(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    request_row = _request_row(status="open")
    set_uow(_RequestLifecycleUow(request_row))
    user = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions={PermissionCodes.REQUESTS_UPDATE},
    )
    set_current_user(user)

    response = test_client.patch(
        "/api/v1/requests/1",
        json={"deadline_at": _future_dt().isoformat()},
    )

    assert response.status_code == 403


def test_update_request_pricing_requires_pricing_and_amounts_permissions(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    request_row = _request_row(status="open")
    set_uow(_RequestLifecycleUow(request_row))
    user = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions={PermissionCodes.REQUESTS_UPDATE, PermissionCodes.REQUESTS_AMOUNTS_READ},
    )
    set_current_user(user)

    response = test_client.patch(
        "/api/v1/requests/1",
        json={"initial_amount": 200.0},
    )

    assert response.status_code == 403


def test_request_owner_change_requires_requests_owner_change_permission(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    request_row = _request_row(status="open")
    set_uow(_RequestLifecycleUow(request_row))
    user = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions={PermissionCodes.REQUESTS_UPDATE, PermissionCodes.REQUESTS_READ},
    )
    set_current_user(user)

    response = test_client.patch(
        "/api/v1/requests/1",
        json={"owner_user_id": "owner-2"},
    )

    assert response.status_code == 403


def test_invalid_request_status_transition_returns_409(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    request_row = _request_row(status="open")
    set_uow(_RequestLifecycleUow(request_row))
    user = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions={PermissionCodes.REQUESTS_UPDATE, PermissionCodes.REQUESTS_STATUS_UPDATE},
    )
    set_current_user(user)

    response = test_client.patch(
        "/api/v1/requests/1",
        json={"status": "archived"},
    )

    assert response.status_code == 409


def test_closed_request_requires_consistent_amounts_when_updated(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    request_row = _request_row(status="closed", initial=100.0, final=90.0)
    set_uow(_RequestLifecycleUow(request_row))
    user = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions={PermissionCodes.REQUESTS_UPDATE, PermissionCodes.REQUESTS_DEADLINE_UPDATE},
    )
    set_current_user(user)

    response = test_client.patch(
        "/api/v1/requests/1",
        json={"deadline_at": _future_dt().isoformat()},
    )

    assert response.status_code == 409


def test_cancelled_request_can_be_updated_with_permissions(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    request_row = _request_row(status="cancelled", initial=100.0, final=90.0)
    set_uow(_RequestLifecycleUow(request_row))
    user = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions={PermissionCodes.REQUESTS_UPDATE, PermissionCodes.REQUESTS_DEADLINE_UPDATE},
    )
    set_current_user(user)

    response = test_client.patch(
        "/api/v1/requests/1",
        json={"deadline_at": _future_dt().isoformat()},
    )

    assert response.status_code == 200


def test_request_can_be_closed_without_offers_when_final_matches_initial(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    request_row = _request_row(status="open", initial=120.0, final=120.0)
    set_uow(_RequestLifecycleUow(request_row))
    user = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions={PermissionCodes.REQUESTS_UPDATE, PermissionCodes.REQUESTS_STATUS_UPDATE},
    )
    set_current_user(user)

    response = test_client.patch(
        "/api/v1/requests/1",
        json={"status": "closed"},
    )

    assert response.status_code == 200


def test_request_can_be_closed_with_accepted_offer_amount(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    request_row = _request_row(status="open", initial=120.0, final=90.0)
    set_uow(_RequestLifecycleUow(request_row, accepted_offer_amount=90.0))
    user = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions={PermissionCodes.REQUESTS_UPDATE, PermissionCodes.REQUESTS_STATUS_UPDATE},
    )
    set_current_user(user)

    response = test_client.patch(
        "/api/v1/requests/1",
        json={"status": "closed"},
    )

    assert response.status_code == 200


def test_deleted_and_rejected_offers_do_not_break_request_stats_payload(
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

    async def _fake_get_request_details(self, *, current_user, request_id):
        _ = (self, current_user, request_id)
        return RequestDetailItem(
            request_id=9,
            description="Stats case",
            status="review",
            status_label="review",
            initial_amount=300.0,
            final_amount=300.0,
            deadline_at=_future_dt(),
            created_at=_now(),
            updated_at=_now(),
            closed_at=None,
            owner_user_id="owner-1",
            owner_full_name="Owner",
            chosen_offer_id=None,
            id_plan=None,
            count_submitted=3,
            count_deleted_alert=1,
            count_accepted_total=0,
            count_rejected_total=2,
            unread_messages_count=0,
            files=[],
            offers=[
                OfferItem(
                    offer_id=1,
                    contractor_user_id="contractor-1",
                    status="deleted",
                    status_label="deleted",
                    offer_amount=100.0,
                    created_at=_now(),
                    updated_at=_now(),
                    offer_workspace_url="/api/v1/offers/1/workspace",
                    contractor_full_name=None,
                    contractor_phone=None,
                    contractor_mail=None,
                    contractor_inn=None,
                    contractor_company_name=None,
                    contractor_company_phone=None,
                    contractor_company_mail=None,
                    contractor_contact_phone=None,
                    contractor_contact_mail=None,
                ),
                OfferItem(
                    offer_id=2,
                    contractor_user_id="contractor-2",
                    status="rejected",
                    status_label="rejected",
                    offer_amount=120.0,
                    created_at=_now(),
                    updated_at=_now(),
                    offer_workspace_url="/api/v1/offers/2/workspace",
                    contractor_full_name=None,
                    contractor_phone=None,
                    contractor_mail=None,
                    contractor_inn=None,
                    contractor_company_name=None,
                    contractor_company_phone=None,
                    contractor_company_mail=None,
                    contractor_contact_phone=None,
                    contractor_contact_mail=None,
                ),
            ],
        )

    monkeypatch.setattr(requests_api.RequestService, "get_request_details", _fake_get_request_details)
    response = test_client.get("/api/v1/requests/9")

    assert response.status_code == 200
    item = response.json()["data"]["item"]
    assert item["stats"]["count_submitted"] == 3
    assert item["stats"]["count_deleted_alert"] == 1
    assert item["stats"]["count_rejected_total"] == 2
    assert len(item["offers"]) == 2


def test_forbidden_role_gets_403_on_request_update(test_client, set_current_user, set_uow, make_current_user):
    contractor = _role_user(make_current_user, settings.contractor_role_id)
    set_current_user(contractor)
    set_uow(_RequestLifecycleUow(_request_row(status="open")))

    response = test_client.patch("/api/v1/requests/1", json={"status": "open"})

    assert response.status_code == 403


def test_anonymous_gets_401_on_protected_request_endpoint(test_client, api_app):
    async def _anonymous():
        raise Unauthorized("Missing credentials")

    api_app.dependency_overrides[get_current_user] = _anonymous
    response = test_client.patch("/api/v1/requests/1", json={"status": "open"})

    assert response.status_code == 401
