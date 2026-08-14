"""P1 backend contract coverage for existing API surface.

These tests keep the integration contour in-memory: no SMTP, S3/MinIO,
Keycloak, or external database is contacted.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.api.dependencies import get_current_user
from app.api.v1 import auth as auth_api
from app.api.v1 import normative_files as normative_files_api
from app.api.v1 import offers as offers_api
from app.api.v1 import plans as plans_api
from app.api.v1 import requests as requests_api
from app.core.config import settings
from app.core.email_token import EmailVerificationTokenCodec
from app.domain.exceptions import Forbidden
from app.domain.permissions import PermissionCodes
from app.domain.policies import UserPolicy
from app.services import file_upload_guard as file_upload_guard_module
from app.services import offers as offers_service_module
from app.services import requests as requests_service_module


def _dt() -> datetime:
    return datetime(2026, 5, 13, 10, 0, tzinfo=timezone.utc)


class _DashboardUsersRepo:
    def __init__(self, *, rows=None, parent_pairs=None) -> None:
        self._rows = rows or []
        self._parent_pairs = parent_pairs or []

    async def get_by_id(self, user_id: str):
        for user, _profile, _role in self._rows:
            if user.id == user_id:
                return user
        return None

    async def list_staff_with_profiles_and_roles_for_dashboard(self, *, role_ids):
        return [row for row in self._rows if row[0].id_role in role_ids]

    async def list_active_user_parent_pairs(self):
        return self._parent_pairs


class _DashboardRequestsRepo:
    def __init__(self, *, closed_rows=None) -> None:
        self._closed_rows = closed_rows or []

    async def count_in_progress_requests_by_owner(self, *, owner_ids):
        _ = owner_ids
        return []

    async def list_unassigned_requests(self, *, operator_role_id, owner_ids):
        _ = (operator_role_id, owner_ids)
        return []

    async def list_in_progress_requests_by_owner_ids(self, *, owner_ids):
        _ = owner_ids
        return []

    async def list_closed_requests_with_chosen_offer_by_owner_ids(self, *, owner_ids):
        return [row for row in self._closed_rows if row[0].id_user in owner_ids]


class _DashboardStatusPeriodsRepo:
    async def list_active_for_users(self, *, user_ids):
        _ = user_ids
        return {}

    async def list_next_for_users(self, *, user_ids):
        _ = user_ids
        return []


class _DashboardPlansRepo:
    async def list_by_ids(self, *, plan_ids):
        return [SimpleNamespace(id=plan_id, name=f"Plan {plan_id}") for plan_id in plan_ids]


class _DashboardUow:
    def __init__(self, *, users=None, requests=None) -> None:
        self.users = users or _DashboardUsersRepo()
        self.requests = requests or _DashboardRequestsRepo()
        self.user_status_periods = _DashboardStatusPeriodsRepo()
        self.economy_plans = _DashboardPlansRepo()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)


class _FeedbackRepo:
    def __init__(self) -> None:
        self.created: list[str] = []
        self.items = [SimpleNamespace(id=7, text="existing feedback")]

    async def create(self, *, text: str):
        self.created.append(text)
        return SimpleNamespace(id=42, text=text)

    async def list_items(self):
        return self.items


class _FeedbackUow:
    def __init__(self, repo: _FeedbackRepo | None = None) -> None:
        self.feedback = repo or _FeedbackRepo()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)


class _PreparedFileService:
    created_request_files: list[dict] = []
    created_offer_files: list[dict] = []
    deleted_files: list[int] = []

    def __init__(self, files=None) -> None:
        self._files = files

    async def prepare_upload(self, upload):
        return SimpleNamespace(
            original_name=upload.filename,
            content_bytes=await upload.read(),
            mime_type=upload.content_type or "text/plain",
        )

    async def prepare_bytes(self, *, original_name, content_bytes, mime_type=None):
        return SimpleNamespace(
            original_name=original_name,
            content_bytes=content_bytes,
            mime_type=mime_type or "text/plain",
        )

    async def create_request_file(self, *, request_id: str, upload):
        self.created_request_files.append({"request_id": request_id, "name": upload.original_name})
        return SimpleNamespace(id=501)

    async def create_offer_file(self, *, offer_id: int, upload):
        self.created_offer_files.append({"offer_id": offer_id, "name": upload.original_name})
        return SimpleNamespace(id=601)

    async def create_normative_file(self, *, upload):
        _ = upload
        return SimpleNamespace(id=701)

    async def delete_file(self, *, file_id: int) -> None:
        self.deleted_files.append(file_id)

    async def cleanup_tracked_objects(self) -> None:
        return None


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


class _RequestFilesRepo:
    def __init__(self, *, detached: bool = True) -> None:
        self.attached: list[tuple[int, int]] = []
        self.detached = detached

    async def get_by_id(self, *, request_id: str):
        return SimpleNamespace(id=request_id, id_user="owner-1", status="open")

    async def attach_file(self, *, request_id: str, file_id: int) -> None:
        self.attached.append((request_id, file_id))

    async def detach_file(self, *, request_id: str, file_id: int) -> bool:
        _ = (request_id, file_id)
        return self.detached


class _RequestFilesUow:
    def __init__(self, *, requests_repo=None) -> None:
        self.requests = requests_repo or _RequestFilesRepo()
        self.files = object()
        self.users = object()
        self.offers = object()
        self.user_status_periods = object()
        self.economy_plans = None
        self.user_contact_channels = None
        self.user_notification_preferences = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)


class _DownloadFilesRepo:
    def __init__(self, *, exists: bool = True, normative: bool = False) -> None:
        self.exists = exists
        self.normative = normative

    async def get_by_id(self, file_id: int):
        if not self.exists:
            return None
        return SimpleNamespace(
            id=file_id,
            id_storage_object=99,
            original_name="linked.txt",
            mime_type="text/plain",
            storage_object=SimpleNamespace(id=99, storage_bucket="bucket", storage_key="key"),
        )

    async def is_normative_file(self, *, file_id: int) -> bool:
        _ = file_id
        return self.normative


class _DownloadRequestsRepo:
    def __init__(self, *, linked: bool = False, owner_user_id: str | None = None) -> None:
        self.linked = linked
        self.owner_user_id = owner_user_id

    async def is_file_linked_to_visible_open_request(self, *, contractor_user_id: str, file_id: int) -> bool:
        _ = (contractor_user_id, file_id)
        return self.linked

    async def get_open_request_identity_by_request_file_id(self, *, file_id: int):
        _ = file_id
        if not self.linked:
            return None
        return ("77", self.owner_user_id or "owner-1")

    async def is_hidden_for_contractor(self, *, request_id: str, contractor_user_id: str) -> bool:
        _ = (request_id, contractor_user_id)
        return False

    async def get_request_owner_id_by_request_file_id(self, *, file_id: int) -> str | None:
        _ = file_id
        return self.owner_user_id


class _DownloadOffersRepo:
    def __init__(
        self,
        *,
        linked_offer: bool = False,
        linked_message: bool = False,
        owner_from_offer_file: str | None = None,
        owner_from_message_file: str | None = None,
    ) -> None:
        self.linked_offer = linked_offer
        self.linked_message = linked_message
        self.owner_from_offer_file = owner_from_offer_file
        self.owner_from_message_file = owner_from_message_file

    async def is_file_linked_to_contractor(self, *, contractor_user_id: str, file_id: int) -> bool:
        _ = (contractor_user_id, file_id)
        return self.linked_offer

    async def is_message_file_linked_to_contractor(self, *, contractor_user_id: str, file_id: int) -> bool:
        _ = (contractor_user_id, file_id)
        return self.linked_message

    async def get_request_owner_id_by_offer_file_id(self, *, file_id: int) -> str | None:
        _ = file_id
        return self.owner_from_offer_file

    async def get_request_owner_id_by_message_file_id(self, *, file_id: int) -> str | None:
        _ = file_id
        return self.owner_from_message_file


class _DownloadUow:
    def __init__(
        self,
        *,
        files_repo: _DownloadFilesRepo | None = None,
        requests_repo: _DownloadRequestsRepo | None = None,
        offers_repo: _DownloadOffersRepo | None = None,
        users_repo=None,
    ) -> None:
        self.files = files_repo or _DownloadFilesRepo()
        self.requests = requests_repo or _DownloadRequestsRepo()
        self.offers = offers_repo or _DownloadOffersRepo()
        self.users = users_repo or _DownloadUsersRepo()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)


class _DownloadUsersRepo:
    def __init__(self, *, users=None, parent_pairs=None) -> None:
        self._users = users or {
            "pm-1": SimpleNamespace(id="pm-1", id_role=settings.project_manager_role_id, id_parent=None),
            "lead-1": SimpleNamespace(id="lead-1", id_role=settings.lead_economist_role_id, id_parent="pm-1"),
            "owner-1": SimpleNamespace(id="owner-1", id_role=settings.economist_role_id, id_parent="lead-1"),
            "contractor-1": SimpleNamespace(id="contractor-1", id_role=settings.contractor_role_id, id_parent=None),
        }
        self._parent_pairs = parent_pairs or []
        self._units = [(1, None), (2, 1)]
        self._unit_details = [
            (1, "Department A", None),
            (2, "Lead 1 Module", 1),
        ]
        self._memberships: list[tuple[str, int]] = []
        user_ids = set(self._users)
        if "pm-1" in user_ids:
            self._memberships.append(("pm-1", 1))
        if "lead-1" in user_ids:
            self._memberships.append(("lead-1", 2))
        if "owner-1" in user_ids:
            self._memberships.append(("owner-1", 2))
        if "contractor-1" in user_ids:
            self._memberships.append(("contractor-1", 1))
        if "lead-2" in user_ids:
            self._units.append((3, 1))
            self._unit_details.append((3, "Lead 2 Module", 1))
            self._memberships.append(("lead-2", 3))
        if "owner-2" in user_ids:
            if all(unit_id != 3 for unit_id, _parent_id in self._units):
                self._units.append((3, 1))
                self._unit_details.append((3, "Lead 2 Module", 1))
            self._memberships.append(("owner-2", 3))
        if "econ-1" in user_ids and ("econ-1", 2) not in self._memberships:
            self._memberships.append(("econ-1", 2))
        if "outside-1" in user_ids:
            self._units.extend([(10, None), (11, 10)])
            self._unit_details.extend(
                [
                    (10, "Department B", None),
                    (11, "Other Lead Module", 10),
                ]
            )
            self._memberships.append(("outside-1", 11))
        if "other-lead" in user_ids and ("other-lead", 11) not in self._memberships:
            self._memberships.append(("other-lead", 11))
        if "pm-2" in user_ids and ("pm-2", 10) not in self._memberships:
            self._memberships.append(("pm-2", 10))

    async def get_by_id(self, user_id: str):
        return self._users.get(user_id)

    async def list_active_user_parent_pairs(self):
        return self._parent_pairs

    async def list_active_units(self):
        return list(self._units)

    async def list_active_unit_details(self):
        return list(self._unit_details)

    async def list_active_unit_memberships(self):
        return list(self._memberships)


class _OfferFilesOffersRepo:
    def __init__(self, *, detached: bool = True) -> None:
        self.attached: list[tuple[int, int]] = []
        self.detached = detached

    async def get_by_id(self, *, offer_id: int):
        return SimpleNamespace(id=offer_id, id_request="10", id_user="contractor-1", status="submitted")

    async def attach_file(self, *, offer_id: int, file_id: int) -> None:
        self.attached.append((offer_id, file_id))

    async def detach_file(self, *, offer_id: int, file_id: int) -> bool:
        _ = (offer_id, file_id)
        return self.detached


class _OfferFilesRequestsRepo:
    async def get_by_id(self, *, request_id: str):
        return SimpleNamespace(id=request_id, id_user="owner-1", status="open")

    async def is_hidden_for_contractor(self, *, request_id: str, contractor_user_id: str) -> bool:
        _ = (request_id, contractor_user_id)
        return False


class _OfferFilesUsersRepo:
    def __init__(self, *, users=None) -> None:
        self._users = users or {}
        self._units = [(1, None), (2, 1)]
        self._unit_details = [
            (1, "Department A", None),
            (2, "Lead 1 Module", 1),
        ]
        self._memberships = [
            ("owner-1", 2),
            ("contractor-1", 1),
            ("other-contractor", 1),
        ]

    async def get_by_id(self, user_id: str | None = None, **kwargs):
        resolved_user_id = user_id or kwargs["user_id"]
        if resolved_user_id in self._users:
            return self._users[resolved_user_id]
        return SimpleNamespace(
            id=resolved_user_id,
            id_role=settings.contractor_role_id,
            id_parent=None,
        )

    async def get_active_approved_contractor_max_id(self, *, user_id: str, contractor_role_id: int):
        _ = (user_id, contractor_role_id)
        return None

    async def list_active_units(self):
        return list(self._units)

    async def list_active_unit_details(self):
        return list(self._unit_details)

    async def list_active_unit_memberships(self):
        memberships = list(self._memberships)
        for user_id, user in self._users.items():
            if getattr(user, "id_role", None) == settings.contractor_role_id and (user_id, 1) not in memberships:
                memberships.append((user_id, 1))
            if user_id == "owner-1" and (user_id, 2) not in memberships:
                memberships.append((user_id, 2))
        return memberships


class _OfferFilesUow:
    def __init__(self, *, offers_repo=None, users_repo=None) -> None:
        self.offers = offers_repo or _OfferFilesOffersRepo()
        self.requests = _OfferFilesRequestsRepo()
        self.users = users_repo or _OfferFilesUsersRepo()
        self.units = object()
        self.files = object()
        self.chats = object()
        self.messages = object()
        self.profiles = object()
        self.company_contacts = object()
        self.user_contact_channels = _NullUserContactChannelsRepo()
        self.user_notification_preferences = _NullUserNotificationPreferencesRepo()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)


class _NormativeFilesRepo:
    def __init__(self, *, existing_file_id: int | None = None) -> None:
        self.existing_file_id = existing_file_id
        self.upserts: list[tuple[int, int]] = []
        self.created: list[tuple[int, int, str]] = []

    async def get_normative_file_id(self, *, normative_id: int):
        _ = normative_id
        return self.existing_file_id

    async def supports_normative_status_column(self):
        return True

    async def get_next_normative_file_id(self):
        return 1 if self.existing_file_id is None else 2

    async def create_normative_file_record(self, *, normative_id: int, file_id: int, status: str = "actual") -> None:
        self.created.append((normative_id, file_id, status))

    async def upsert_normative_file(self, *, normative_id: int, file_id: int, status: str = "actual") -> None:
        self.upserts.append((normative_id, file_id))

    async def list_normative_files(self, *, status: str | None = None):
        return []

    async def get_normative_file_row(self, *, normative_id: int):
        return None

    async def update_normative_file_status(self, *, normative_id: int, status: str) -> bool:
        _ = (normative_id, status)
        return False


class _NormativeUow:
    def __init__(self, repo: _NormativeFilesRepo | None = None) -> None:
        self.files = repo or _NormativeFilesRepo()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)


class _ManualEmailNotifications:
    def __init__(
        self,
        profiles,
        requests,
        users=None,
        files=None,
        *,
        after_commit_hook_registrar=None,
    ) -> None:
        _ = (profiles, requests, users, files, after_commit_hook_registrar)
        self.calls: list[dict] = []

    async def notify_request_to_additional_emails(
        self,
        *,
        request_id: str,
        additional_emails: list[str],
        initiator_user_id: str | None = None,
    ) -> None:
        self.calls.append(
            {
                "request_id": request_id,
                "additional_emails": additional_emails,
                "initiator_user_id": initiator_user_id,
            }
        )


class _ManualEmailRequestsRepo:
    async def get_by_id(self, *, request_id: str):
        return SimpleNamespace(id=request_id, id_user="owner-1", status="open")


class _ManualEmailUow:
    def __init__(self) -> None:
        self.requests = _ManualEmailRequestsRepo()
        self.files = object()
        self.users = object()
        self.offers = object()
        self.user_status_periods = object()
        self.economy_plans = None
        self.profiles = object()
        self.user_contact_channels = None
        self.user_notification_preferences = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)


class _ProfilesRepo:
    def __init__(self, *, mail_exists: bool = False, update_result: bool = True) -> None:
        self.mail_exists = mail_exists
        self.update_result = update_result
        self.updated: list[tuple[str, str]] = []
        self.sent_to: list[str] = []

    async def get_by_id(self, user_id: str):
        return SimpleNamespace(id=user_id, mail="old@example.com")

    async def exists_by_mail(self, *, email: str, exclude_user_id: str | None = None):
        _ = (email, exclude_user_id)
        return self.mail_exists

    async def update_mail_after_verification(self, *, user_id: str, email: str) -> bool:
        self.updated.append((user_id, email))
        return self.update_result


class _ProfilesUow:
    def __init__(self, repo: _ProfilesRepo) -> None:
        self.profiles = repo
        self.user_contact_channels = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)


def _clear_current_user_override(api_app) -> None:
    api_app.dependency_overrides.pop(get_current_user, None)


def test_dashboard_responsibility_allows_empty_data_for_allowed_role(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    user = make_current_user(
        role_id=settings.project_manager_role_id,
        permissions={PermissionCodes.DASHBOARD_PROCESS_READ, PermissionCodes.DASHBOARD_SAVINGS_READ},
    )
    set_current_user(user)
    set_uow(_DashboardUow())

    response = test_client.get("/api/v1/dashboard/responsibility")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["tree"] == []
    assert data["savings"]["total_closed_requests"] == 0
    assert data["savings"]["items"] == []


@pytest.mark.parametrize("role_id", [settings.project_manager_role_id, settings.lead_economist_role_id, settings.superadmin_role_id])
def test_dashboard_responsibility_allows_project_manager_lead_economist_and_superadmin(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
    role_id,
):
    set_current_user(
        make_current_user(
            role_id=role_id,
            permissions={PermissionCodes.DASHBOARD_PROCESS_READ, PermissionCodes.DASHBOARD_SAVINGS_READ},
        )
    )
    set_uow(_DashboardUow())

    response = test_client.get("/api/v1/dashboard/responsibility")

    assert response.status_code == 200


def test_dashboard_responsibility_serializes_savings_numeric_edges(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    staff_user = SimpleNamespace(id="lead-1", id_role=settings.lead_economist_role_id, id_parent=None)
    staff_profile = SimpleNamespace(full_name="Lead One")
    staff_role = SimpleNamespace(role="lead_economist")
    closed_request = SimpleNamespace(
        id=10,
        id_user="lead-1",
        initial_amount=1000,
        final_amount=800,
        closed_at=_dt(),
        id_plan=5,
    )
    accepted_offer = SimpleNamespace(offer_amount=800)
    user = make_current_user(
        user_id="lead-1",
        role_id=settings.lead_economist_role_id,
        permissions={PermissionCodes.DASHBOARD_PROCESS_READ, PermissionCodes.DASHBOARD_SAVINGS_READ},
    )
    set_current_user(user)
    set_uow(
        _DashboardUow(
            users=_DashboardUsersRepo(rows=[(staff_user, staff_profile, staff_role)]),
            requests=_DashboardRequestsRepo(closed_rows=[(closed_request, accepted_offer, staff_profile)]),
        )
    )

    response = test_client.get("/api/v1/dashboard/responsibility")

    assert response.status_code == 200
    savings = response.json()["data"]["savings"]
    assert savings["total_closed_requests"] == 1
    assert savings["total_with_savings"] == 1
    assert savings["total_savings_amount"] == 200.0
    assert savings["items"][0]["plan_name"] == "Plan 5"


def test_dashboard_responsibility_serializes_negative_and_zero_savings_without_nan_or_infinity(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    staff_user = SimpleNamespace(id="lead-1", id_role=settings.lead_economist_role_id, id_parent=None)
    staff_profile = SimpleNamespace(full_name="Lead One")
    staff_role = SimpleNamespace(role="lead_economist")
    closed_rows = [
        (
            SimpleNamespace(id=11, id_user="lead-1", initial_amount=1000, final_amount=1200, closed_at=_dt(), id_plan=None),
            SimpleNamespace(offer_amount=1200),
            staff_profile,
        ),
        (
            SimpleNamespace(id=12, id_user="lead-1", initial_amount=500, final_amount=500, closed_at=_dt(), id_plan=None),
            SimpleNamespace(offer_amount=500),
            staff_profile,
        ),
    ]
    set_current_user(
        make_current_user(
            user_id="lead-1",
            role_id=settings.lead_economist_role_id,
            permissions={PermissionCodes.DASHBOARD_PROCESS_READ, PermissionCodes.DASHBOARD_SAVINGS_READ},
        )
    )
    set_uow(
        _DashboardUow(
            users=_DashboardUsersRepo(rows=[(staff_user, staff_profile, staff_role)]),
            requests=_DashboardRequestsRepo(closed_rows=closed_rows),
        )
    )

    response = test_client.get("/api/v1/dashboard/responsibility")

    assert response.status_code == 200
    assert "NaN" not in response.text
    assert "Infinity" not in response.text


@pytest.mark.parametrize(
    ("role_id", "permissions", "status"),
    [
        (settings.economist_role_id, set(), "active"),
        (settings.project_manager_role_id, {PermissionCodes.DASHBOARD_PROCESS_READ}, "active"),
        (settings.project_manager_role_id, {PermissionCodes.DASHBOARD_SAVINGS_READ}, "active"),
        (
            settings.project_manager_role_id,
            {PermissionCodes.DASHBOARD_PROCESS_READ, PermissionCodes.DASHBOARD_SAVINGS_READ},
            "inactive",
        ),
        (
            settings.project_manager_role_id,
            {PermissionCodes.DASHBOARD_PROCESS_READ, PermissionCodes.DASHBOARD_SAVINGS_READ},
            "blacklist",
        ),
    ],
)
def test_dashboard_responsibility_denies_forbidden_permissions_and_statuses(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
    role_id,
    permissions,
    status,
):
    set_current_user(make_current_user(role_id=role_id, status=status, permissions=permissions))
    set_uow(_DashboardUow())

    response = test_client.get("/api/v1/dashboard/responsibility")

    assert response.status_code == 403


def test_dashboard_responsibility_denies_anonymous_user(api_app, test_client, set_uow):
    _clear_current_user_override(api_app)
    set_uow(_DashboardUow())

    response = test_client.get("/api/v1/dashboard/responsibility")

    assert response.status_code == 401


def _empty_plan_dashboard():
    return SimpleNamespace(
        period="2026-05",
        period_start=date(2026, 5, 1),
        period_end=date(2026, 5, 31),
        can_create_root_plan=True,
        root_plan_exists=False,
        summary=SimpleNamespace(
            total_plan_amount=Decimal("0"),
            total_fact_amount=Decimal("0"),
            total_period_fact_amount=Decimal("0"),
            total_remaining_amount=Decimal("0"),
            total_progress_percent=Decimal("0"),
            total_period_progress_percent=Decimal("0"),
        ),
        request_stats=SimpleNamespace(
            total_requests=0,
            distributed_requests=0,
            unallocated_requests=0,
            request_fact_amount=Decimal("0"),
            unallocated_amount=Decimal("0"),
            completion_percent=Decimal("0"),
        ),
        tree=None,
        trees=[],
    )


def test_plans_dashboard_endpoint_allows_empty_data_for_plans_permission(
    test_client,
    monkeypatch,
    set_current_user,
    make_current_user,
):
    set_current_user(
        make_current_user(
            role_id=settings.project_manager_role_id,
            permissions={PermissionCodes.DASHBOARD_PLANS_READ},
        )
    )

    async def _fake_get_dashboard_plan_tab(self, *, period, current_user):
        _ = (self, period)
        UserPolicy.ensure_can_view_plan(current_user)
        return _empty_plan_dashboard()

    monkeypatch.setattr(plans_api.PlanService, "get_dashboard_plan_tab", _fake_get_dashboard_plan_tab)

    response = test_client.get("/api/v1/plans", params={"period": "2026-05"})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["period"] == "2026-05"
    assert data["root_plan_exists"] is False
    assert data["summary"]["total_plan_amount"] == 0.0


def test_plans_dashboard_endpoint_passes_period_filter_to_service(
    test_client,
    monkeypatch,
    set_current_user,
    make_current_user,
):
    captured = {}
    set_current_user(make_current_user(role_id=settings.project_manager_role_id, permissions={PermissionCodes.DASHBOARD_PLANS_READ}))

    async def _fake_get_dashboard_plan_tab(self, *, period, current_user):
        _ = (self, current_user)
        captured["period"] = period
        return _empty_plan_dashboard()

    monkeypatch.setattr(plans_api.PlanService, "get_dashboard_plan_tab", _fake_get_dashboard_plan_tab)

    response = test_client.get("/api/v1/plans", params={"period": "2026-05"})

    assert response.status_code == 200
    assert captured["period"] == "2026-05"


def test_plans_dashboard_endpoint_passes_date_range_filter_to_service(
    test_client,
    monkeypatch,
    set_current_user,
    make_current_user,
):
    captured = {}
    set_current_user(make_current_user(role_id=settings.project_manager_role_id, permissions={PermissionCodes.DASHBOARD_PLANS_READ}))

    async def _fake_get_dashboard_plan_tab_by_range(self, *, date_from, date_to, current_user):
        _ = (self, current_user)
        captured["date_from"] = date_from
        captured["date_to"] = date_to
        return _empty_plan_dashboard()

    monkeypatch.setattr(plans_api.PlanService, "get_dashboard_plan_tab_by_range", _fake_get_dashboard_plan_tab_by_range)

    response = test_client.get("/api/v1/plans", params={"date_from": "2026-05-01", "date_to": "2026-05-31"})

    assert response.status_code == 200
    assert str(captured["date_from"]) == "2026-05-01"
    assert str(captured["date_to"]) == "2026-05-31"


def test_plans_dashboard_endpoint_denies_missing_plans_permission(
    test_client,
    monkeypatch,
    set_current_user,
    make_current_user,
):
    set_current_user(make_current_user(role_id=settings.economist_role_id, permissions=set()))

    async def _fake_get_dashboard_plan_tab(self, *, period, current_user):
        _ = (self, period)
        UserPolicy.ensure_can_view_plan(current_user)
        raise Forbidden("should not be reached")

    monkeypatch.setattr(plans_api.PlanService, "get_dashboard_plan_tab", _fake_get_dashboard_plan_tab)

    response = test_client.get("/api/v1/plans", params={"period": "2026-05"})

    assert response.status_code == 403


def test_plans_dashboard_denies_anonymous_user(api_app, test_client):
    _clear_current_user_override(api_app)

    response = test_client.get("/api/v1/plans", params={"period": "2026-05"})

    assert response.status_code == 401


def test_plans_tree_forwards_hierarchy_filter_to_service(
    test_client,
    monkeypatch,
    set_current_user,
    make_current_user,
):
    captured = {}
    set_current_user(make_current_user(role_id=settings.project_manager_role_id, permissions={PermissionCodes.DASHBOARD_PLANS_READ}))

    async def _fake_get_plan_tree(self, *, period, root_user_id, current_user):
        _ = (self, current_user)
        captured["period"] = period
        captured["root_user_id"] = root_user_id
        return SimpleNamespace(
            plan_id=1,
            plan_name="Root",
            id_parent_plan=None,
            user_id="pm-1",
            user_name="PM",
            user_role="project_manager",
            parent_user_id_snapshot=None,
            period_start=date(2026, 5, 1),
            period_end=date(2026, 5, 31),
            plan_amount=Decimal("0"),
            delegated_amount=Decimal("0"),
            personal_plan_amount=Decimal("0"),
            unallocated_amount=Decimal("0"),
            fact_amount_self=Decimal("0"),
            fact_amount_subtree=Decimal("0"),
            period_fact_amount=Decimal("0"),
            period_progress_percent=Decimal("0"),
            in_progress_requests_count=0,
            remaining_amount=Decimal("0"),
            progress_percent=Decimal("0"),
            available_actions=SimpleNamespace(
                create_child_plan=False,
                create_subplan=False,
                delegate_plan=False,
                edit_plan=False,
                delete_child_plan=False,
                activate_plan=False,
                close_plan=False,
                view_plan=True,
            ),
            children=[],
        )

    monkeypatch.setattr(plans_api.PlanService, "get_plan_tree", _fake_get_plan_tree)

    response = test_client.get("/api/v1/plans/tree", params={"period": "2026-05", "root_user_id": "pm-1"})

    assert response.status_code == 200
    assert captured == {"period": "2026-05", "root_user_id": "pm-1"}


def test_feedback_create_accepts_authenticated_payload_and_ignores_unexpected_fields(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    repo = _FeedbackRepo()
    set_current_user(make_current_user(permissions={PermissionCodes.FEEDBACK_CREATE}))
    set_uow(_FeedbackUow(repo))

    response = test_client.post(
        "/api/v1/feedback",
        json={"text": "  useful signal  ", "unexpected": "ignored"},
    )

    assert response.status_code == 200
    assert response.json() == {"data": {"feedback_id": 42}}
    assert repo.created == ["useful signal"]


def test_feedback_create_denies_anonymous_user(api_app, test_client):
    _clear_current_user_override(api_app)

    response = test_client.post("/api/v1/feedback", json={"text": "anonymous"})

    assert response.status_code == 401


def test_feedback_create_validates_payload(test_client, set_current_user, make_current_user):
    set_current_user(make_current_user(permissions={PermissionCodes.FEEDBACK_CREATE}))

    response = test_client.post("/api/v1/feedback", json={"text": ""})

    assert response.status_code == 422


def test_feedback_create_validates_too_long_payload(test_client, set_current_user, make_current_user):
    set_current_user(make_current_user(permissions={PermissionCodes.FEEDBACK_CREATE}))

    response = test_client.post("/api/v1/feedback", json={"text": "x" * 3001})

    assert response.status_code == 422


def test_feedback_list_allows_superadmin_and_denies_non_superadmin(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    set_uow(_FeedbackUow())
    set_current_user(make_current_user(role_id=settings.superadmin_role_id, permissions={PermissionCodes.FEEDBACK_READ}))

    response = test_client.get("/api/v1/feedback")

    assert response.status_code == 200
    assert response.json()["data"]["items"] == [{"id": 7, "text": "existing feedback"}]

    set_current_user(make_current_user(role_id=settings.economist_role_id, permissions={PermissionCodes.FEEDBACK_CREATE}))
    denied_response = test_client.get("/api/v1/feedback")

    assert denied_response.status_code == 403


def test_normative_file_upload_allows_create_permission(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    monkeypatch.setattr(normative_files_api, "FileService", _PreparedFileService)
    files_repo = _NormativeFilesRepo()
    set_current_user(
        make_current_user(
            role_id=settings.lead_economist_role_id,
            permissions={PermissionCodes.NORMATIVE_FILES_CREATE},
        )
    )
    set_uow(_NormativeUow(files_repo))

    response = test_client.post(
        "/api/v1/normative-files",
        files={"file": ("norm.txt", b"normative text", "text/plain")},
    )

    assert response.status_code == 200
    assert response.json() == {"data": {"normative_id": 1, "file_id": 701}}
    assert files_repo.created == [(1, 701, "actual")]


@pytest.mark.parametrize(
    ("role_id", "permissions", "status"),
    [
        (settings.operator_role_id, {PermissionCodes.NORMATIVE_FILES_READ}, "active"),
        (settings.economist_role_id, {PermissionCodes.NORMATIVE_FILES_READ}, "active"),
        (settings.admin_role_id, set(), "active"),
        (settings.lead_economist_role_id, {PermissionCodes.NORMATIVE_FILES_CREATE}, "inactive"),
        (settings.lead_economist_role_id, {PermissionCodes.NORMATIVE_FILES_CREATE}, "blacklist"),
    ],
)
def test_normative_file_upload_denies_forbidden_roles_and_statuses(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
    role_id,
    permissions,
    status,
):
    monkeypatch.setattr(normative_files_api, "FileService", _PreparedFileService)
    set_current_user(make_current_user(role_id=role_id, status=status, permissions=permissions))
    set_uow(_NormativeUow())

    response = test_client.post(
        "/api/v1/normative-files/1",
        files={"file": ("norm.txt", b"normative text", "text/plain")},
    )

    assert response.status_code == 403


def test_normative_file_upload_rejects_duplicate(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    monkeypatch.setattr(normative_files_api, "FileService", _PreparedFileService)
    set_current_user(make_current_user(permissions={PermissionCodes.NORMATIVE_FILES_CREATE}))
    set_uow(_NormativeUow(_NormativeFilesRepo(existing_file_id=100)))

    response = test_client.post(
        "/api/v1/normative-files/1",
        files={"file": ("norm.txt", b"normative text", "text/plain")},
    )

    assert response.status_code == 409


def test_normative_file_upload_denies_anonymous_user(api_app, test_client, monkeypatch, set_uow):
    _clear_current_user_override(api_app)
    monkeypatch.setattr(normative_files_api, "FileService", _PreparedFileService)
    set_uow(_NormativeUow())

    response = test_client.post(
        "/api/v1/normative-files/1",
        files={"file": ("norm.txt", b"normative text", "text/plain")},
    )

    assert response.status_code == 401


def test_request_file_upload_and_delete_contracts(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    monkeypatch.setattr(requests_api, "FileService", _PreparedFileService)
    monkeypatch.setattr(requests_service_module, "FileService", _PreparedFileService)
    request_repo = _RequestFilesRepo()
    set_uow(_RequestFilesUow(requests_repo=request_repo))
    set_current_user(
        make_current_user(
            user_id="owner-1",
            role_id=settings.economist_role_id,
            permissions={PermissionCodes.REQUESTS_FILES_UPLOAD, PermissionCodes.REQUESTS_FILES_DELETE, PermissionCodes.REQUESTS_UPDATE},
        )
    )

    upload_response = test_client.post(
        "/api/v1/requests/10/files",
        files={"file": ("request.txt", b"request file", "text/plain")},
    )
    delete_response = test_client.delete("/api/v1/requests/10/files/501")

    assert upload_response.status_code == 200
    assert upload_response.json() == {"data": {"request_id": "10", "file_id": 501}}
    assert request_repo.attached == [("10", 501)]
    assert delete_response.status_code == 200
    assert delete_response.json() == {"data": {"request_id": "10", "file_id": 501}}


def test_request_file_upload_denies_forbidden_role(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    monkeypatch.setattr(requests_api, "FileService", _PreparedFileService)
    set_uow(_RequestFilesUow())
    set_current_user(make_current_user(role_id=settings.operator_role_id, permissions={PermissionCodes.REQUESTS_UPDATE}))

    response = test_client.post(
        "/api/v1/requests/10/files",
        files={"file": ("request.txt", b"request file", "text/plain")},
    )

    assert response.status_code == 403


def test_request_file_upload_denies_anonymous_user(api_app, test_client, monkeypatch, set_uow):
    _clear_current_user_override(api_app)
    monkeypatch.setattr(requests_api, "FileService", _PreparedFileService)
    set_uow(_RequestFilesUow())

    response = test_client.post(
        "/api/v1/requests/10/files",
        files={"file": ("request.txt", b"request file", "text/plain")},
    )

    assert response.status_code == 401


def test_request_file_delete_missing_attachment_returns_404(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    monkeypatch.setattr(requests_api, "FileService", _PreparedFileService)
    monkeypatch.setattr(requests_service_module, "FileService", _PreparedFileService)
    set_uow(_RequestFilesUow(requests_repo=_RequestFilesRepo(detached=False)))
    set_current_user(
        make_current_user(
            user_id="owner-1",
            role_id=settings.economist_role_id,
            permissions={PermissionCodes.REQUESTS_FILES_DELETE, PermissionCodes.REQUESTS_UPDATE},
        )
    )

    response = test_client.delete("/api/v1/requests/10/files/999")

    assert response.status_code == 404


@pytest.mark.parametrize(
    ("filename", "payload", "expected_status"),
    [
        ("bad.exe", b"not allowed", 422),
        ("empty.pdf", b"", 422),
    ],
)
def test_request_file_upload_rejects_unsupported_and_empty_files(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
    filename,
    payload,
    expected_status,
):
    async def _scan(self, *, original_name: str, content_bytes: bytes, content_type: str | None):
        _ = (self, content_bytes, content_type)
        if original_name.endswith(".exe"):
            raise file_upload_guard_module.UploadRejected(
                reason_code="file_type_not_allowed",
                detail="Тип файла не разрешен.",
            )
        raise file_upload_guard_module.UploadRejected(
            reason_code="empty_file",
            detail="Файл пустой.",
        )

    monkeypatch.setattr(file_upload_guard_module.FileUploadGuardService, "scan_bytes", _scan)
    set_uow(_RequestFilesUow())
    set_current_user(
        make_current_user(
            user_id="owner-1",
            role_id=settings.economist_role_id,
            permissions={PermissionCodes.REQUESTS_FILES_UPLOAD, PermissionCodes.REQUESTS_UPDATE},
        )
    )

    response = test_client.post(
        "/api/v1/requests/10/files",
        files={"file": (filename, payload, "application/pdf")},
    )

    assert response.status_code == expected_status


def test_request_file_upload_rejects_oversized_file(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    monkeypatch.setattr(settings, "max_upload_size_bytes", 1)
    set_uow(_RequestFilesUow())
    set_current_user(
        make_current_user(
            user_id="owner-1",
            role_id=settings.economist_role_id,
            permissions={PermissionCodes.REQUESTS_FILES_UPLOAD, PermissionCodes.REQUESTS_UPDATE},
        )
    )

    response = test_client.post(
        "/api/v1/requests/10/files",
        files={"file": ("big.pdf", b"ab", "application/pdf")},
    )

    assert response.status_code == 422


def test_offer_file_upload_delete_and_missing_attachment_contracts(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    monkeypatch.setattr(offers_api, "FileService", _PreparedFileService)
    monkeypatch.setattr(offers_service_module, "FileService", _PreparedFileService)
    offers_repo = _OfferFilesOffersRepo()
    set_uow(_OfferFilesUow(offers_repo=offers_repo))
    set_current_user(
        make_current_user(
            user_id="contractor-1",
            role_id=settings.contractor_role_id,
            permissions={PermissionCodes.OFFERS_FILES_UPLOAD, PermissionCodes.OFFERS_FILES_DELETE},
        )
    )

    upload_response = test_client.post(
        "/api/v1/offers/20/files",
        files={"file": ("offer.txt", b"offer file", "text/plain")},
    )
    delete_response = test_client.delete("/api/v1/offers/20/files/601")

    assert upload_response.status_code == 200
    assert upload_response.json() == {"data": {"offer_id": 20, "file_id": 601}}
    assert offers_repo.attached == [(20, 601)]
    assert delete_response.status_code == 200
    assert delete_response.json() == {"data": {"offer_id": 20, "file_id": 601}}

    set_uow(_OfferFilesUow(offers_repo=_OfferFilesOffersRepo(detached=False)))
    missing_response = test_client.delete("/api/v1/offers/20/files/999")

    assert missing_response.status_code == 404


def test_offer_file_upload_denies_non_owner_contractor(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    monkeypatch.setattr(offers_api, "FileService", _PreparedFileService)
    monkeypatch.setattr(offers_service_module, "FileService", _PreparedFileService)
    set_uow(_OfferFilesUow())
    set_current_user(
        make_current_user(
            user_id="other-contractor",
            role_id=settings.contractor_role_id,
            permissions={PermissionCodes.OFFERS_FILES_UPLOAD},
        )
    )

    response = test_client.post(
        "/api/v1/offers/20/files",
        files={"file": ("offer.txt", b"offer file", "text/plain")},
    )

    assert response.status_code == 403


def test_offer_file_delete_denies_non_owner_contractor(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    monkeypatch.setattr(offers_api, "FileService", _PreparedFileService)
    monkeypatch.setattr(offers_service_module, "FileService", _PreparedFileService)
    set_uow(_OfferFilesUow())
    set_current_user(
        make_current_user(
            user_id="other-contractor",
            role_id=settings.contractor_role_id,
            permissions={PermissionCodes.OFFERS_FILES_DELETE},
        )
    )

    response = test_client.delete("/api/v1/offers/20/files/601")

    assert response.status_code == 403


def test_offer_file_delete_denies_internal_user_without_file_permissions(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    monkeypatch.setattr(offers_api, "FileService", _PreparedFileService)
    monkeypatch.setattr(offers_service_module, "FileService", _PreparedFileService)
    set_uow(_OfferFilesUow())
    set_current_user(
        make_current_user(
            user_id="lead-1",
            role_id=settings.lead_economist_role_id,
            permissions={
                PermissionCodes.REQUESTS_UPDATE,
                PermissionCodes.OFFERS_MANUAL_CREATE,
            },
        )
    )

    response = test_client.delete("/api/v1/offers/20/files/601")

    assert response.status_code == 403


def test_offer_file_delete_denies_internal_user_outside_hierarchy_scope(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    monkeypatch.setattr(offers_api, "FileService", _PreparedFileService)
    monkeypatch.setattr(offers_service_module, "FileService", _PreparedFileService)
    users_repo = _OfferFilesUsersRepo(
        users={
            "owner-1": SimpleNamespace(
                id="owner-1",
                id_role=settings.economist_role_id,
                id_parent="lead-2",
            ),
            "lead-2": SimpleNamespace(
                id="lead-2",
                id_role=settings.lead_economist_role_id,
                id_parent="pm-1",
            ),
            "pm-1": SimpleNamespace(
                id="pm-1",
                id_role=settings.project_manager_role_id,
                id_parent=None,
            ),
        }
    )
    set_uow(_OfferFilesUow(users_repo=users_repo))
    set_current_user(
        make_current_user(
            user_id="lead-1",
            role_id=settings.lead_economist_role_id,
            permissions={
                PermissionCodes.OFFERS_FILES_DELETE,
                PermissionCodes.REQUESTS_UPDATE,
            },
        )
    )

    response = test_client.delete("/api/v1/offers/20/files/601")

    assert response.status_code == 403


def test_offer_file_upload_denies_anonymous_user(api_app, test_client, monkeypatch, set_uow):
    _clear_current_user_override(api_app)
    monkeypatch.setattr(offers_api, "FileService", _PreparedFileService)
    set_uow(_OfferFilesUow())

    response = test_client.post(
        "/api/v1/offers/20/files",
        files={"file": ("offer.txt", b"offer file", "text/plain")},
    )

    assert response.status_code == 401


def test_file_download_allows_contractor_for_linked_open_request(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    async def _fake_read_bytes(self, *, db_file):
        _ = (self, db_file)
        return b"linked-content"

    monkeypatch.setattr(requests_api.FileService, "read_bytes", _fake_read_bytes)
    set_uow(_DownloadUow(requests_repo=_DownloadRequestsRepo(linked=True)))
    set_current_user(
        make_current_user(
            user_id="contractor-1",
            role_id=settings.contractor_role_id,
            permissions={PermissionCodes.FILES_DOWNLOAD},
        )
    )

    response = test_client.get("/api/v1/files/77/download")

    assert response.status_code == 200
    assert response.content == b"linked-content"


def test_file_download_denies_contractor_for_unlinked_foreign_file(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    async def _fake_read_bytes(self, *, db_file):
        _ = (self, db_file)
        return b"must-not-be-used"

    monkeypatch.setattr(requests_api.FileService, "read_bytes", _fake_read_bytes)
    set_uow(_DownloadUow())
    set_current_user(
        make_current_user(
            user_id="contractor-1",
            role_id=settings.contractor_role_id,
            permissions={PermissionCodes.FILES_DOWNLOAD},
        )
    )

    response = test_client.get("/api/v1/files/77/download")

    assert response.status_code == 403


def test_file_download_returns_not_found_for_missing_file(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    set_uow(_DownloadUow(files_repo=_DownloadFilesRepo(exists=False)))
    set_current_user(
        make_current_user(
            user_id="owner-1",
            role_id=settings.lead_economist_role_id,
            permissions={PermissionCodes.FILES_DOWNLOAD, PermissionCodes.REQUESTS_READ},
        )
    )

    response = test_client.get("/api/v1/files/404/download")

    assert response.status_code == 404


def test_file_download_denies_internal_user_outside_standard_scope(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    async def _fake_read_bytes(self, *, db_file):
        _ = (self, db_file)
        return b"must-not-be-used"

    monkeypatch.setattr(requests_api.FileService, "read_bytes", _fake_read_bytes)
    users_repo = _DownloadUsersRepo(
        users={
            "lead-1": SimpleNamespace(id="lead-1", id_role=settings.lead_economist_role_id, id_parent="pm-1"),
            "pm-1": SimpleNamespace(id="pm-1", id_role=settings.project_manager_role_id, id_parent=None),
            "owner-1": SimpleNamespace(id="owner-1", id_role=settings.economist_role_id, id_parent="lead-1"),
            "outside-1": SimpleNamespace(id="outside-1", id_role=settings.economist_role_id, id_parent="other-lead"),
            "other-lead": SimpleNamespace(id="other-lead", id_role=settings.lead_economist_role_id, id_parent="pm-2"),
            "pm-2": SimpleNamespace(id="pm-2", id_role=settings.project_manager_role_id, id_parent=None),
        },
        parent_pairs=[
            ("lead-1", "pm-1"),
            ("owner-1", "lead-1"),
            ("outside-1", "other-lead"),
            ("other-lead", "pm-2"),
        ],
    )
    set_uow(
        _DownloadUow(
            requests_repo=_DownloadRequestsRepo(owner_user_id="outside-1"),
            users_repo=users_repo,
        )
    )
    set_current_user(
        make_current_user(
            user_id="lead-1",
            role_id=settings.lead_economist_role_id,
            permissions={PermissionCodes.FILES_DOWNLOAD, PermissionCodes.REQUESTS_READ},
        )
    )

    response = test_client.get("/api/v1/files/77/download")

    assert response.status_code == 403


def test_file_download_allows_department_request_read_for_department_scope(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    async def _fake_read_bytes(self, *, db_file):
        _ = (self, db_file)
        return b"department-linked"

    monkeypatch.setattr(requests_api.FileService, "read_bytes", _fake_read_bytes)
    users_repo = _DownloadUsersRepo(
        users={
            "econ-1": SimpleNamespace(id="econ-1", id_role=settings.economist_role_id, id_parent="lead-1"),
            "lead-1": SimpleNamespace(id="lead-1", id_role=settings.lead_economist_role_id, id_parent="pm-1"),
            "pm-1": SimpleNamespace(id="pm-1", id_role=settings.project_manager_role_id, id_parent=None),
            "owner-2": SimpleNamespace(id="owner-2", id_role=settings.economist_role_id, id_parent="lead-2"),
            "lead-2": SimpleNamespace(id="lead-2", id_role=settings.lead_economist_role_id, id_parent="pm-1"),
        },
        parent_pairs=[
            ("econ-1", "lead-1"),
            ("lead-1", "pm-1"),
            ("owner-2", "lead-2"),
            ("lead-2", "pm-1"),
        ],
    )
    set_uow(
        _DownloadUow(
            requests_repo=_DownloadRequestsRepo(owner_user_id="owner-2"),
            users_repo=users_repo,
        )
    )
    set_current_user(
        make_current_user(
            user_id="econ-1",
            role_id=settings.economist_role_id,
            permissions={PermissionCodes.FILES_DOWNLOAD, PermissionCodes.DEPARTMENT_REQUESTS_READ},
        )
    )

    response = test_client.get("/api/v1/files/77/download")

    assert response.status_code == 200
    assert response.content == b"department-linked"


def test_file_download_denies_offer_file_without_offer_workspace_permission(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    async def _fake_read_bytes(self, *, db_file):
        _ = (self, db_file)
        return b"must-not-be-used"

    monkeypatch.setattr(requests_api.FileService, "read_bytes", _fake_read_bytes)
    users_repo = _DownloadUsersRepo(
        users={
            "lead-1": SimpleNamespace(id="lead-1", id_role=settings.lead_economist_role_id, id_parent="pm-1"),
            "pm-1": SimpleNamespace(id="pm-1", id_role=settings.project_manager_role_id, id_parent=None),
            "owner-1": SimpleNamespace(id="owner-1", id_role=settings.economist_role_id, id_parent="lead-1"),
        },
        parent_pairs=[
            ("lead-1", "pm-1"),
            ("owner-1", "lead-1"),
        ],
    )
    set_uow(
        _DownloadUow(
            requests_repo=_DownloadRequestsRepo(owner_user_id=None),
            offers_repo=_DownloadOffersRepo(owner_from_offer_file="owner-1"),
            users_repo=users_repo,
        )
    )
    set_current_user(
        make_current_user(
            user_id="lead-1",
            role_id=settings.lead_economist_role_id,
            permissions={PermissionCodes.FILES_DOWNLOAD, PermissionCodes.REQUESTS_READ},
        )
    )

    response = test_client.get("/api/v1/files/77/download")

    assert response.status_code == 403


def test_file_download_allows_offer_file_with_offer_workspace_permission(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    async def _fake_read_bytes(self, *, db_file):
        _ = (self, db_file)
        return b"offer-file"

    monkeypatch.setattr(requests_api.FileService, "read_bytes", _fake_read_bytes)
    users_repo = _DownloadUsersRepo(
        users={
            "lead-1": SimpleNamespace(id="lead-1", id_role=settings.lead_economist_role_id, id_parent="pm-1"),
            "pm-1": SimpleNamespace(id="pm-1", id_role=settings.project_manager_role_id, id_parent=None),
            "owner-1": SimpleNamespace(id="owner-1", id_role=settings.economist_role_id, id_parent="lead-1"),
        },
        parent_pairs=[
            ("lead-1", "pm-1"),
            ("owner-1", "lead-1"),
        ],
    )
    set_uow(
        _DownloadUow(
            requests_repo=_DownloadRequestsRepo(owner_user_id=None),
            offers_repo=_DownloadOffersRepo(owner_from_offer_file="owner-1"),
            users_repo=users_repo,
        )
    )
    set_current_user(
        make_current_user(
            user_id="lead-1",
            role_id=settings.lead_economist_role_id,
            permissions={PermissionCodes.FILES_DOWNLOAD, PermissionCodes.OFFERS_WORKSPACE_READ},
        )
    )

    response = test_client.get("/api/v1/files/77/download")

    assert response.status_code == 200
    assert response.content == b"offer-file"


def test_manual_request_email_notification_endpoint_deduplicates_and_uses_fake_transport(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    fake_notifications: _ManualEmailNotifications | None = None

    def _factory(
        profiles,
        requests,
        users,
        files=None,
        *,
        after_commit_hook_registrar=None,
    ):
        nonlocal fake_notifications
        fake_notifications = _ManualEmailNotifications(
            profiles,
            requests,
            users,
            files,
            after_commit_hook_registrar=after_commit_hook_registrar,
        )
        return fake_notifications

    monkeypatch.setattr(requests_api, "EmailNotificationService", _factory)
    set_uow(_ManualEmailUow())
    set_current_user(
        make_current_user(
            user_id="owner-1",
            role_id=settings.economist_role_id,
            permissions={PermissionCodes.REQUESTS_EMAIL_NOTIFICATIONS_SEND, PermissionCodes.REQUESTS_UPDATE},
        )
    )

    response = test_client.post(
        "/api/v1/requests/55/email-notifications",
        json={"additional_emails": ["USER@example.com", "user@example.com", " second@example.com ", ""]},
    )

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "request_id": "55",
            "sent_to": ["user@example.com", "second@example.com"],
        }
    }
    assert fake_notifications is not None
    assert fake_notifications.calls == [
        {
            "request_id": "55",
            "additional_emails": ["user@example.com", "second@example.com"],
            "initiator_user_id": "owner-1",
        }
    ]


def test_manual_request_email_notification_denies_forbidden_role(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    monkeypatch.setattr(requests_api, "EmailNotificationService", _ManualEmailNotifications)
    set_uow(_ManualEmailUow())
    set_current_user(make_current_user(role_id=settings.operator_role_id, permissions={PermissionCodes.REQUESTS_UPDATE}))

    response = test_client.post(
        "/api/v1/requests/55/email-notifications",
        json={"additional_emails": ["user@example.com"]},
    )

    assert response.status_code == 403


def test_manual_request_email_notification_requires_safe_recipient(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    monkeypatch.setattr(requests_api, "EmailNotificationService", _ManualEmailNotifications)
    set_uow(_ManualEmailUow())
    set_current_user(
        make_current_user(
            user_id="owner-1",
            role_id=settings.economist_role_id,
            permissions={PermissionCodes.REQUESTS_EMAIL_NOTIFICATIONS_SEND, PermissionCodes.REQUESTS_UPDATE},
        )
    )

    response = test_client.post(
        "/api/v1/requests/55/email-notifications",
        json={"additional_emails": ["  "]},
    )

    assert response.status_code == 409


def test_request_email_verification_uses_fake_mail_sender(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    sent: list[dict] = []

    async def _fake_send(self, *, email, verification_link, recipient_context):
        _ = self
        sent.append(
            {
                "email": email,
                "verification_link": verification_link,
                "recipient_context": recipient_context,
            }
        )

    auth_api.EmailVerificationService._request_locks.clear()
    monkeypatch.setattr(settings, "web_base_url", "https://web.acom.example")
    monkeypatch.setattr(settings, "email_verification_secret", "test-secret")
    monkeypatch.setattr(auth_api.EmailVerificationService, "_send_verification_email", _fake_send)
    set_current_user(make_current_user(user_id="profile-1", permissions={PermissionCodes.PROFILE_MANAGE_OWN}))
    set_uow(_ProfilesUow(_ProfilesRepo()))

    response = test_client.post(
        "/api/v1/auth/request-email-verification",
        json={"email": "new@example.com"},
    )

    assert response.status_code == 200
    assert sent[0]["email"] == "new@example.com"
    assert sent[0]["verification_link"].startswith("https://web.acom.example/verify-email?token=")
    assert sent[0]["recipient_context"] == {"user_login": "profile-1"}


@pytest.mark.parametrize("update_result", [True, False])
def test_verify_email_valid_token_updates_or_reports_repeat(
    test_client,
    monkeypatch,
    set_uow,
    update_result,
):
    monkeypatch.setattr(settings, "email_verification_secret", "test-secret")
    profiles = _ProfilesRepo(update_result=update_result)
    set_uow(_ProfilesUow(profiles))
    token = asyncio.run(
        EmailVerificationTokenCodec(secret="test-secret", ttl_seconds=3600).create_profile_token(
            user_id="profile-1",
            email="verified@example.com",
        )
    )

    response = test_client.get("/api/v1/auth/verify-email", params={"token": token})

    assert response.status_code == 200
    assert profiles.updated == [("profile-1", "verified@example.com")]
    if update_result:
        assert "Email" in response.json()["detail"]
    else:
        assert "Email" in response.json()["detail"]


@pytest.mark.parametrize(
    "token",
    [
        "not-a-valid-verification-token.value",
        asyncio.run(
            EmailVerificationTokenCodec(secret="test-secret", ttl_seconds=-1).create_profile_token(
                user_id="profile-1",
                email="expired@example.com",
            )
        ),
    ],
)
def test_verify_email_rejects_invalid_and_expired_tokens(test_client, monkeypatch, set_uow, token):
    monkeypatch.setattr(settings, "email_verification_secret", "test-secret")
    set_uow(_ProfilesUow(_ProfilesRepo()))

    response = test_client.get("/api/v1/auth/verify-email", params={"token": token})

    assert response.status_code == 401


def test_verify_email_rejects_token_when_email_belongs_to_another_user(test_client, monkeypatch, set_uow):
    monkeypatch.setattr(settings, "email_verification_secret", "test-secret")
    set_uow(_ProfilesUow(_ProfilesRepo(mail_exists=True)))
    token = asyncio.run(
        EmailVerificationTokenCodec(secret="test-secret", ttl_seconds=3600).create_profile_token(
            user_id="profile-1",
            email="taken@example.com",
        )
    )

    response = test_client.get("/api/v1/auth/verify-email", params={"token": token})

    assert response.status_code == 409


@pytest.mark.parametrize("status", ["inactive", "blacklist"])
def test_request_email_verification_denies_inactive_and_blacklist_users(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
    status,
):
    set_current_user(
        make_current_user(
            role_id=settings.contractor_role_id,
            status=status,
            permissions={PermissionCodes.PROFILE_MANAGE_OWN},
        )
    )
    set_uow(_ProfilesUow(_ProfilesRepo()))

    response = test_client.post(
        "/api/v1/auth/request-email-verification",
        json={"email": "blocked@example.com"},
    )

    assert response.status_code == 403
