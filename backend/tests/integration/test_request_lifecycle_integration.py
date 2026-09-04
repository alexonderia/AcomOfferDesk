"""Integration-style tests for request lifecycle auth/enforcement scenarios."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.api.dependencies import get_current_user
from app.api.v1 import requests as requests_api
from app.core.config import settings
from app.domain.exceptions import Unauthorized
from app.domain.permissions import PermissionCodes, get_role_permissions_map
from app.domain.policies import UserPolicy
from app.services.requests import OfferItem, RequestDetailItem


def _future_dt() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=30)


def _now() -> datetime:
    return datetime(2026, 5, 12, 12, 0, tzinfo=timezone.utc)


class _MutableRequestsRepo:
    def __init__(
        self,
        request_row: SimpleNamespace,
        *,
        accepted_offer_id: int | None = None,
        has_submitted_offers: bool = False,
    ) -> None:
        self.request_row = request_row
        self.accepted_offer_id = accepted_offer_id
        self._has_submitted_offers = has_submitted_offers

    async def get_by_id(self, *, request_id: str):
        return self.request_row if str(self.request_row.id) == str(request_id) else None

    async def lock_offer_lifecycle(self, *, request_id: str) -> None:
        _ = request_id

    async def update_initial_amount(self, *, request, initial_amount: float) -> None:
        request.initial_amount = initial_amount

    async def update_final_amount(self, *, request, final_amount: float) -> None:
        request.final_amount = final_amount

    async def update_status(self, *, request, status: str, closed_at, chosen_offer_id) -> None:
        request.status = status
        request.closed_at = closed_at
        request.id_offer = chosen_offer_id

    async def get_latest_accepted_offer_id(self, *, request_id: str):
        _ = request_id
        return self.accepted_offer_id

    async def has_submitted_offers(self, *, request_id: str) -> bool:
        _ = request_id
        return self._has_submitted_offers

    async def update_deadline(self, *, request, deadline_at: datetime) -> None:
        request.deadline_at = deadline_at

    async def update_owner(self, *, request, user_id: str) -> None:
        request.id_user = user_id

    async def update_plan(self, *, request, plan_id: int | None) -> None:
        request.id_plan = plan_id

    async def get_economy_plan_owner_user_id(self, *, plan_id: int):
        _ = plan_id
        return "owner-1"

    async def list_open_with_files_for_contractor(self, *, contractor_user_id: str):
        _ = contractor_user_id
        return [(self.request_row, None)] if self.request_row.status == "open" else []


class _OffersRepo:
    def __init__(self, offers_by_id: dict[str, SimpleNamespace] | None = None) -> None:
        self._offers_by_id = offers_by_id or {}

    async def get_by_id(self, *, offer_id: int):
        return self._offers_by_id.get(offer_id)

    async def list_contractor_tg_ids_for_request(self, *, request_id: str, contractor_role_id: int):
        _ = (request_id, contractor_role_id)
        return []

    async def list_latest_contractor_offers_by_request_ids(self, *, contractor_user_id: str, request_ids: list[str]):
        _ = (contractor_user_id, request_ids)
        return []


class _UsersRepo:
    def __init__(self, users_by_id: dict[str, SimpleNamespace] | None = None) -> None:
        self._users_by_id = users_by_id or {}
        self._units: list[tuple[int, int | None]] = []
        self._unit_details: list[tuple[int, str, int | None]] = []
        self._memberships: list[tuple[str, int]] = []

        user_ids = set(self._users_by_id)
        if {"pm-1", "lead-1", "lead-2"} & user_ids:
            self._units = [(1, None), (2, 1), (3, 1)]
            self._unit_details = [
                (1, "Department A", None),
                (2, "Lead 1 Module", 1),
                (3, "Lead 2 Module", 1),
            ]
            if "pm-1" in user_ids:
                self._memberships.append(("pm-1", 1))
            if "lead-1" in user_ids:
                self._memberships.append(("lead-1", 2))
            if "lead-2" in user_ids:
                self._memberships.append(("lead-2", 3))
            if "econ-1" in user_ids:
                self._memberships.append(("econ-1", 2))
            if "econ-2" in user_ids:
                self._memberships.append(("econ-2", 3))
            if "owner-1" in user_ids:
                self._memberships.append(("owner-1", 2))
            if "user-1" in user_ids:
                self._memberships.append(("user-1", 1))
            if "contractor-1" in user_ids:
                self._memberships.append(("contractor-1", 1))
        elif user_ids:
            self._units = [(1, None)]
            self._unit_details = [(1, "Department A", None)]
            for user_id in sorted(user_ids):
                self._memberships.append((user_id, 1))

    async def get_by_id(self, user_id: str):
        return self._users_by_id.get(user_id)

    async def list_role_ids_by_user_ids(self, *, user_ids: list[str]):
        return [
            (user_id, self._users_by_id[user_id].id_role)
            for user_id in user_ids
            if user_id in self._users_by_id
        ]

    async def list_active_user_parent_pairs(self):
        return [
            (user.id, user.id_parent)
            for user in self._users_by_id.values()
        ]

    async def list_active_units(self):
        return list(self._units)

    async def list_active_unit_details(self):
        return list(self._unit_details)

    async def list_active_unit_memberships(self):
        return list(self._memberships)


class _UserStatusPeriodsRepo:
    async def get_active_for_user(self, *, user_id: str):
        _ = user_id
        return None


class _ContractorViewRequestsRepo:
    def __init__(self, request_row: SimpleNamespace) -> None:
        self._request_row = request_row

    async def get_visible_by_id_for_contractor(self, *, request_id: str, contractor_user_id: str):
        _ = contractor_user_id
        if str(request_id) != str(self._request_row.id):
            return None
        return self._request_row

    async def get_visible_open_by_id_for_contractor(self, *, request_id: str, contractor_user_id: str):
        request = await self.get_visible_by_id_for_contractor(
            request_id=request_id,
            contractor_user_id=contractor_user_id,
        )
        return request if request is not None and request.status == "open" else None

    async def list_files(self, *, request_id: str):
        _ = request_id
        return []


class _ContractorViewOffersRepo:
    async def get_contractor_offer_for_request(self, *, request_id: str, contractor_user_id: str):
        _ = (request_id, contractor_user_id)
        return None

    async def list_offer_files(self, *, offer_id: int):
        _ = offer_id
        return []


class _ContractorViewProfilesRepo:
    async def get_by_id(self, user_id: str):
        return SimpleNamespace(id=user_id, full_name="Owner")


class _NullUserContactChannelsRepo:
    async def get_primary_by_type(self, *, user_id: str, channel_type: str, include_inactive: bool = False):
        _ = (user_id, channel_type, include_inactive)
        return None

    async def list_by_user(self, *, user_id: str, channel_types: list[str], include_inactive: bool = True):
        _ = (user_id, channel_types, include_inactive)
        return []

    async def upsert_channel(
        self,
        *,
        user_id: str,
        channel_type: str,
        channel_value: str,
        is_verified: bool,
        is_primary: bool,
    ):
        _ = (user_id, is_primary)
        return SimpleNamespace(
            id=1,
            channel_type=channel_type,
            channel_value=channel_value,
            is_active=True,
            is_verified=is_verified,
        )

    async def flush(self) -> None:
        return None


class _NullUserNotificationPreferencesRepo:
    async def get_by_channel_id_and_type(self, *, channel_id: int, notification_type: str):
        _ = (channel_id, notification_type)
        return None

    async def list_by_channel_ids(self, *, channel_ids: list[int]):
        _ = channel_ids
        return []

    async def upsert(self, *, channel_id: int, notification_type: str, is_enabled: bool) -> None:
        _ = (channel_id, notification_type, is_enabled)


class _ContractorViewUow:
    def __init__(self, request_row: SimpleNamespace) -> None:
        self.requests = _ContractorViewRequestsRepo(request_row)
        self.offers = _ContractorViewOffersRepo()
        self.profiles = _ContractorViewProfilesRepo()
        self.chats = object()
        self.files = object()
        self.messages = object()
        self.company_contacts = object()
        self.users = _UsersRepo(
            users_by_id={
                "pm-1": SimpleNamespace(id="pm-1", id_parent=None, id_role=settings.project_manager_role_id),
                "lead-1": SimpleNamespace(id="lead-1", id_parent="pm-1", id_role=settings.lead_economist_role_id),
                "owner-1": SimpleNamespace(id="owner-1", id_parent="lead-1", id_role=settings.economist_role_id),
                "contractor-1": SimpleNamespace(
                    id="contractor-1",
                    id_parent=None,
                    id_role=settings.contractor_role_id,
                ),
                "user-1": SimpleNamespace(
                    id="user-1",
                    id_parent=None,
                    id_role=settings.contractor_role_id,
                ),
            }
        )
        self.units = object()
        self.user_contact_channels = _NullUserContactChannelsRepo()
        self.user_notification_preferences = _NullUserNotificationPreferencesRepo()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)


class _RequestLifecycleUow:
    def __init__(
        self,
        request_row: SimpleNamespace,
        *,
        accepted_offer_amount: float | None = None,
        has_accepted_offer: bool = False,
        has_submitted_offers: bool = False,
        users_by_id: dict[str, SimpleNamespace] | None = None,
    ) -> None:
        accepted_offer_id = 501 if has_accepted_offer or accepted_offer_amount is not None else None
        offers_by_id = (
            {accepted_offer_id: SimpleNamespace(id=accepted_offer_id, offer_amount=accepted_offer_amount)}
            if accepted_offer_id is not None
            else {}
        )
        self.requests = _MutableRequestsRepo(
            request_row,
            accepted_offer_id=accepted_offer_id,
            has_submitted_offers=has_submitted_offers,
        )
        self.files = object()
        self.users = _UsersRepo(
            users_by_id=users_by_id
            or {
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
        self.user_auth_accounts = None
        self.user_contact_channels = None
        self.user_notification_preferences = None
        self.economy_plans = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)


def _request_row(
    *,
    status: str = "open",
    initial: float = 100.0,
    final: float = 100.0,
    owner_user_id: str = "owner-1",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        id_user=owner_user_id,
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


def _department_users_tree() -> dict[str, SimpleNamespace]:
    return {
        "pm-1": SimpleNamespace(id="pm-1", id_parent=None, id_role=settings.project_manager_role_id),
        "lead-1": SimpleNamespace(id="lead-1", id_parent="pm-1", id_role=settings.lead_economist_role_id),
        "lead-2": SimpleNamespace(id="lead-2", id_parent="pm-1", id_role=settings.lead_economist_role_id),
        "econ-1": SimpleNamespace(id="econ-1", id_parent="lead-1", id_role=settings.economist_role_id),
        "econ-2": SimpleNamespace(id="econ-2", id_parent="lead-2", id_role=settings.economist_role_id),
    }


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
        request_id,
        deadline_at,
        description,
        initial_amount,
        id_plan,
        normative_file_id,
        files,
        additional_emails,
        hidden_contractor_ids,
    ):
        _ = (self, request_id, deadline_at, description, initial_amount, id_plan, normative_file_id, files, additional_emails, hidden_contractor_ids)
        UserPolicy.ensure_can_create_request(current_user)
        UserPolicy.ensure_can_view_normative_files(current_user)
        return "700", [701]

    monkeypatch.setattr(requests_api.RequestService, "create_request", _guarded_create_request)

    response = test_client.post(
        "/api/v1/requests",
        data={
            "id": "REQ-700",
            "deadline_at": _future_dt().isoformat(),
            "description": "Created in test",
            "initial_amount": "0",
            "normative_file_id": "1",
        },
        files=[("files", ("evidence.txt", b"request payload", "text/plain"))],
    )

    assert response.status_code == 200
    assert response.json()["data"]["request_id"] == "700"


def test_request_creation_requires_initial_amount(test_client, set_current_user, make_current_user):
    set_current_user(_role_user(make_current_user, settings.lead_economist_role_id))

    response = test_client.post(
        "/api/v1/requests",
        data={
            "id": "REQ-701",
            "deadline_at": _future_dt().isoformat(),
            "normative_file_id": "1",
        },
        files=[("files", ("evidence.txt", b"request payload", "text/plain"))],
    )

    assert response.status_code == 422


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
        request_id,
        deadline_at,
        description,
        initial_amount,
        id_plan,
        normative_file_id,
        files,
        additional_emails,
        hidden_contractor_ids,
    ):
        _ = (self, request_id, deadline_at, description, initial_amount, id_plan, normative_file_id, files, additional_emails, hidden_contractor_ids)
        UserPolicy.ensure_can_create_request(current_user)
        UserPolicy.ensure_can_view_normative_files(current_user)
        return "700", [701]

    monkeypatch.setattr(requests_api.RequestService, "create_request", _guarded_create_request)

    response = test_client.post(
        "/api/v1/requests",
        data={
            "id": "REQ-700",
            "deadline_at": _future_dt().isoformat(),
            "description": "Created in test",
            "initial_amount": "0",
            "normative_file_id": "1",
        },
        files=[("files", ("evidence.txt", b"request payload", "text/plain"))],
    )

    assert response.status_code == 403


def test_contractor_cannot_access_internal_request_representation(test_client, set_current_user, make_current_user):
    contractor = _role_user(make_current_user, settings.contractor_role_id)
    set_current_user(contractor)

    response = test_client.get("/api/v1/requests/1")

    assert response.status_code == 403


def test_operator_request_becomes_visible_to_contractor_only_after_assignment(
    test_client,
    set_uow,
    set_current_user,
    make_current_user,
):
    request_row = _request_row(owner_user_id="operator-1")
    users_by_id = {
        "pm-1": SimpleNamespace(id="pm-1", id_parent=None, id_role=settings.project_manager_role_id),
        "lead-1": SimpleNamespace(id="lead-1", id_parent="pm-1", id_role=settings.lead_economist_role_id),
        "econ-1": SimpleNamespace(id="econ-1", id_parent="lead-1", id_role=settings.economist_role_id),
        "operator-1": SimpleNamespace(id="operator-1", id_parent=None, id_role=settings.operator_role_id),
        "contractor-1": SimpleNamespace(id="contractor-1", id_parent=None, id_role=settings.contractor_role_id),
    }
    uow = _RequestLifecycleUow(request_row, users_by_id=users_by_id)
    uow.users._memberships.append(("operator-1", 1))
    set_uow(uow)

    contractor = make_current_user(
        user_id="contractor-1",
        role_id=settings.contractor_role_id,
        permissions={PermissionCodes.REQUESTS_OPEN_READ},
    )
    set_current_user(contractor)
    before_assignment = test_client.get("/api/v1/requests/open")

    assert before_assignment.status_code == 200
    assert before_assignment.json()["data"]["items"] == []

    assigner = make_current_user(
        user_id="superadmin-1",
        role_id=settings.superadmin_role_id,
        permissions={
            PermissionCodes.REQUESTS_UPDATE,
            PermissionCodes.REQUESTS_OWNER_CHANGE,
            PermissionCodes.REQUESTS_READ,
        },
    )
    set_current_user(assigner)
    assignment = test_client.patch("/api/v1/requests/1", json={"owner_user_id": "econ-1"})

    assert assignment.status_code == 200
    assert request_row.id_user == "econ-1"

    set_current_user(contractor)
    after_assignment = test_client.get("/api/v1/requests/open")

    assert after_assignment.status_code == 200
    assert [item["request_id"] for item in after_assignment.json()["data"]["items"]] == ["1"]


def test_contractor_can_access_contractor_view_only_when_permission_allows(
    test_client,
    set_uow,
    set_current_user,
    make_current_user,
):
    request_row = SimpleNamespace(
        id=11,
        id_user="owner-1",
        status="open",
        description="Visible contractor request",
        deadline_at=_future_dt(),
    )
    set_uow(_ContractorViewUow(request_row))

    denied_user = make_current_user(
        role_id=settings.contractor_role_id,
        permissions={PermissionCodes.OFFERS_CREATE},
    )
    set_current_user(denied_user)
    denied = test_client.get("/api/v1/requests/11/contractor-view")
    assert denied.status_code == 403

    allowed_user = make_current_user(
        role_id=settings.contractor_role_id,
        permissions={PermissionCodes.REQUESTS_CONTRACTOR_VIEW_READ},
    )
    set_current_user(allowed_user)
    allowed = test_client.get("/api/v1/requests/11/contractor-view")

    assert allowed.status_code == 200
    assert "actions" in allowed.json()["data"]


def test_review_contractor_cannot_access_protected_request_actions_even_with_permission(
    test_client,
    set_uow,
    set_current_user,
    make_current_user,
):
    request_row = SimpleNamespace(
        id=11,
        id_user="owner-1",
        status="open",
        description="Visible contractor request",
        deadline_at=_future_dt(),
    )
    set_uow(_ContractorViewUow(request_row))
    review_contractor = make_current_user(
        role_id=settings.contractor_role_id,
        status="review",
        permissions={PermissionCodes.REQUESTS_CONTRACTOR_VIEW_READ},
    )
    set_current_user(review_contractor)

    response = test_client.get("/api/v1/requests/11/contractor-view")

    assert response.status_code == 403


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


def test_request_owner_can_be_changed_with_required_permissions(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    request_row = _request_row(status="open")
    set_uow(_RequestLifecycleUow(request_row))
    user = make_current_user(
        user_id="superadmin-1",
        role_id=settings.superadmin_role_id,
        permissions={
            PermissionCodes.REQUESTS_UPDATE,
            PermissionCodes.REQUESTS_OWNER_CHANGE,
            PermissionCodes.REQUESTS_READ,
        },
    )
    set_current_user(user)

    response = test_client.patch(
        "/api/v1/requests/1",
        json={"owner_user_id": "owner-2"},
    )

    assert response.status_code == 200
    assert request_row.id_user == "owner-2"


def test_request_update_deadline_succeeds_with_required_permissions(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    request_row = _request_row(status="open")
    set_uow(_RequestLifecycleUow(request_row))
    user = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions={PermissionCodes.REQUESTS_UPDATE, PermissionCodes.REQUESTS_DEADLINE_UPDATE},
    )
    set_current_user(user)
    new_deadline = _future_dt()

    response = test_client.patch(
        "/api/v1/requests/1",
        json={"deadline_at": new_deadline.isoformat()},
    )

    assert response.status_code == 200


def test_invalid_request_status_transition_returns_409(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    request_row = _request_row(status="open")
    set_uow(_RequestLifecycleUow(request_row))
    user = make_current_user(
        user_id="owner-1",
        role_id=settings.lead_economist_role_id,
        permissions={PermissionCodes.REQUESTS_UPDATE, PermissionCodes.REQUESTS_STATUS_UPDATE},
    )
    set_current_user(user)

    response = test_client.patch(
        "/api/v1/requests/1",
        json={"status": "archived"},
    )

    assert response.status_code == 409


def test_department_request_update_without_department_status_update_cannot_change_foreign_request_status(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    request_row = _request_row(status="open", owner_user_id="econ-2")
    set_uow(_RequestLifecycleUow(request_row, users_by_id=_department_users_tree()))
    user = make_current_user(
        user_id="lead-1",
        role_id=settings.lead_economist_role_id,
        permissions={
            PermissionCodes.REQUESTS_STATUS_UPDATE,
            PermissionCodes.DEPARTMENT_REQUESTS_UPDATE,
        },
    )
    set_current_user(user)

    response = test_client.patch(
        "/api/v1/requests/1",
        json={"status": "review"},
    )

    assert response.status_code == 403


def test_department_status_update_allows_changing_foreign_request_status_inside_department_scope(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    request_row = _request_row(status="open", owner_user_id="econ-2")
    set_uow(_RequestLifecycleUow(request_row, users_by_id=_department_users_tree()))
    user = make_current_user(
        user_id="lead-1",
        role_id=settings.lead_economist_role_id,
        permissions={PermissionCodes.DEPARTMENT_REQUESTS_STATUS_UPDATE},
    )
    set_current_user(user)

    response = test_client.patch(
        "/api/v1/requests/1",
        json={"status": "review"},
    )

    assert response.status_code == 200


def test_department_requests_update_without_department_assign_cannot_change_foreign_request_owner(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    request_row = _request_row(status="open", owner_user_id="econ-2")
    set_uow(_RequestLifecycleUow(request_row, users_by_id=_department_users_tree()))
    user = make_current_user(
        user_id="lead-1",
        role_id=settings.lead_economist_role_id,
        permissions={
            PermissionCodes.REQUESTS_READ,
            PermissionCodes.REQUESTS_OWNER_CHANGE,
            PermissionCodes.DEPARTMENT_REQUESTS_UPDATE,
        },
    )
    set_current_user(user)

    response = test_client.patch(
        "/api/v1/requests/1",
        json={"owner_user_id": "econ-1"},
    )

    assert response.status_code == 403


def test_lead_can_change_subordinate_request_owner_to_self_inside_management_scope(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    request_row = _request_row(status="open", owner_user_id="econ-1")
    set_uow(_RequestLifecycleUow(request_row, users_by_id=_department_users_tree()))
    user = make_current_user(
        user_id="lead-1",
        role_id=settings.lead_economist_role_id,
        permissions={
            PermissionCodes.REQUESTS_READ,
            PermissionCodes.REQUESTS_OWNER_CHANGE,
        },
    )
    set_current_user(user)

    response = test_client.patch(
        "/api/v1/requests/1",
        json={"owner_user_id": "lead-1"},
    )

    assert response.status_code == 200
    assert request_row.id_user == "lead-1"


def test_department_assign_allows_changing_foreign_request_owner_inside_department_scope(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    request_row = _request_row(status="open", owner_user_id="econ-2")
    set_uow(_RequestLifecycleUow(request_row, users_by_id=_department_users_tree()))
    user = make_current_user(
        user_id="lead-1",
        role_id=settings.lead_economist_role_id,
        permissions={PermissionCodes.DEPARTMENT_REQUESTS_ASSIGN},
    )
    set_current_user(user)

    response = test_client.patch(
        "/api/v1/requests/1",
        json={"owner_user_id": "econ-1"},
    )

    assert response.status_code == 200
    assert request_row.id_user == "econ-1"


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
        user_id="owner-1",
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
        user_id="owner-1",
        role_id=settings.lead_economist_role_id,
        permissions={PermissionCodes.REQUESTS_UPDATE, PermissionCodes.REQUESTS_STATUS_UPDATE},
    )
    set_current_user(user)

    response = test_client.patch(
        "/api/v1/requests/1",
        json={"status": "closed"},
    )

    assert response.status_code == 200


def test_request_can_be_closed_with_initial_amount_when_offer_is_accepted(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    request_row = _request_row(status="open", initial=100.0, final=100.0)
    set_uow(_RequestLifecycleUow(request_row, accepted_offer_amount=80.0))
    set_current_user(
        make_current_user(
            user_id="owner-1",
            role_id=settings.lead_economist_role_id,
            permissions={PermissionCodes.REQUESTS_UPDATE, PermissionCodes.REQUESTS_STATUS_UPDATE},
        )
    )

    response = test_client.patch("/api/v1/requests/1", json={"status": "closed"})

    assert response.status_code == 200
    assert request_row.status == "closed"
    assert request_row.id_offer == 501


@pytest.mark.parametrize(
    ("accepted_offer_amount", "final_amount"),
    [(80.0, 90.0), (None, 90.0)],
)
def test_request_closure_rejects_final_amount_outside_allowed_values(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
    accepted_offer_amount,
    final_amount,
):
    request_row = _request_row(status="open", initial=100.0, final=final_amount)
    set_uow(_RequestLifecycleUow(request_row, accepted_offer_amount=accepted_offer_amount))
    set_current_user(
        make_current_user(
            user_id="owner-1",
            role_id=settings.lead_economist_role_id,
            permissions={PermissionCodes.REQUESTS_UPDATE, PermissionCodes.REQUESTS_STATUS_UPDATE},
        )
    )

    response = test_client.patch("/api/v1/requests/1", json={"status": "closed"})

    assert response.status_code == 409
    assert response.json()["detail"] == "Итоговая сумма должна совпадать с начальной суммой или суммой принятого КП"
    assert request_row.status == "open"
    assert request_row.closed_at is None
    assert request_row.id_offer is None


def test_request_can_be_closed_with_initial_amount_when_accepted_offer_has_no_amount(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    request_row = _request_row(status="open", initial=100.0, final=100.0)
    set_uow(_RequestLifecycleUow(request_row, has_accepted_offer=True))
    set_current_user(
        make_current_user(
            user_id="owner-1",
            role_id=settings.lead_economist_role_id,
            permissions={PermissionCodes.REQUESTS_UPDATE, PermissionCodes.REQUESTS_STATUS_UPDATE},
        )
    )

    response = test_client.patch("/api/v1/requests/1", json={"status": "closed"})

    assert response.status_code == 200
    assert request_row.id_offer == 501


def test_request_with_zero_initial_amount_can_be_closed_with_positive_final_amount(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    request_row = _request_row(status="open", initial=0.0, final=123.45)
    set_uow(_RequestLifecycleUow(request_row))
    set_current_user(
        make_current_user(
            user_id="owner-1",
            role_id=settings.lead_economist_role_id,
            permissions={PermissionCodes.REQUESTS_UPDATE, PermissionCodes.REQUESTS_STATUS_UPDATE},
        )
    )

    response = test_client.patch("/api/v1/requests/1", json={"status": "closed"})

    assert response.status_code == 200
    assert request_row.status == "closed"


def test_request_without_initial_amount_cannot_be_closed(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    request_row = _request_row(status="open", initial=None, final=123.45)
    set_uow(_RequestLifecycleUow(request_row))
    set_current_user(
        make_current_user(
            user_id="owner-1",
            role_id=settings.lead_economist_role_id,
            permissions={PermissionCodes.REQUESTS_UPDATE, PermissionCodes.REQUESTS_STATUS_UPDATE},
        )
    )

    response = test_client.patch("/api/v1/requests/1", json={"status": "closed"})

    assert response.status_code == 409
    assert request_row.status == "open"
    assert request_row.closed_at is None
    assert request_row.id_offer is None


def test_request_with_zero_initial_amount_rejects_non_positive_final_amount(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    request_row = _request_row(status="open", initial=0.0, final=0.0)
    set_uow(_RequestLifecycleUow(request_row))
    set_current_user(
        make_current_user(
            user_id="owner-1",
            role_id=settings.lead_economist_role_id,
            permissions={PermissionCodes.REQUESTS_UPDATE, PermissionCodes.REQUESTS_STATUS_UPDATE},
        )
    )

    response = test_client.patch("/api/v1/requests/1", json={"status": "closed"})

    assert response.status_code == 409
    assert request_row.status == "open"


def test_request_cannot_be_closed_while_submitted_offer_exists(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    request_row = _request_row(status="open", initial=100.0, final=100.0)
    set_uow(_RequestLifecycleUow(request_row, has_submitted_offers=True))
    set_current_user(
        make_current_user(
            user_id="owner-1",
            role_id=settings.lead_economist_role_id,
            permissions={PermissionCodes.REQUESTS_UPDATE, PermissionCodes.REQUESTS_STATUS_UPDATE},
        )
    )

    response = test_client.patch("/api/v1/requests/1", json={"status": "closed"})

    assert response.status_code == 409
    assert response.json()["detail"] == "Нельзя закрыть заявку, пока есть нерассмотренные коммерческие предложения."
    assert request_row.status == "open"
    assert request_row.closed_at is None
    assert request_row.id_offer is None


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
            owner_phone=None,
            owner_mail=None,
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
