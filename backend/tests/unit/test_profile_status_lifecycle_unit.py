from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.domain.permissions import PermissionCodes
from app.repositories.offers import OfferRepository
from app.repositories.requests import RequestRepository
from app.services import users as module
from app.services.requests import RequestService


@pytest_asyncio.fixture
async def lifecycle_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        for statement in [
            "CREATE TABLE users (id TEXT PRIMARY KEY, id_role INTEGER, status TEXT)",
            "CREATE TABLE requests (id TEXT PRIMARY KEY, id_user TEXT, status TEXT, description TEXT, "
            "deadline_at TIMESTAMP, created_at TIMESTAMP, updated_at TIMESTAMP, closed_at TIMESTAMP, "
            "id_offer INTEGER, id_plan INTEGER, initial_amount NUMERIC, final_amount NUMERIC)",
            "CREATE TABLE offers (id INTEGER PRIMARY KEY, id_request TEXT, id_user TEXT, status TEXT, "
            "offer_amount NUMERIC, created_at TIMESTAMP, updated_at TIMESTAMP)",
        ]:
            await connection.exec_driver_sql(statement)
    async with AsyncSession(engine) as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_unassigned_requests_include_blocked_owners_within_scope_only(lifecycle_session):
    session = lifecycle_session
    await session.execute(text("INSERT INTO users VALUES "
        "('operator', :operator, 'active'), ('active', :staff, 'active'), "
        "('inactive', :staff, 'inactive'), ('blocked', :staff, 'blacklist'), ('outside', :staff, 'blacklist')"),
        {"operator": settings.operator_role_id, "staff": settings.economist_role_id})
    for owner in ["operator", "active", "inactive", "blocked", "outside"]:
        for status in ["open", "review", "closed", "cancelled"]:
            await session.execute(text("INSERT INTO requests (id, id_user, status) VALUES (:id, :owner, :status)"),
                                  {"id": f"{owner}-{status}", "owner": owner, "status": status})
    repo = RequestRepository(session)
    rows = await repo.list_unassigned_requests(operator_role_id=settings.operator_role_id,
        unavailable_owner_ids=["active", "inactive", "blocked"])
    assert {row.id for row in rows} == {
        f"{owner}-{status}" for owner in ["operator", "inactive", "blocked"] for status in ["open", "review"]
    }
    assert await repo.list_unassigned_requests(operator_role_id=settings.operator_role_id, owner_ids=[]) == []
    counters = await repo.count_in_progress_requests_by_owner(owner_ids=["active", "inactive", "blocked"])
    assert {(owner, status, count) for owner, status, count in counters} == {
        ("active", "open", 1), ("active", "review", 1)
    }


@pytest.mark.asyncio
async def test_only_accepted_offers_on_active_requests_are_candidates(lifecycle_session):
    session = lifecycle_session
    for index, status in enumerate(["open", "review", "closed", "cancelled"], start=1):
        await session.execute(text("INSERT INTO requests (id, status) VALUES (:id, :status)"),
                              {"id": str(index), "status": status})
        for offer_status in ["accepted", "submitted", "rejected", "deleted"]:
            await session.execute(text("INSERT INTO offers (id_request, id_user, status) VALUES (:id, 'contractor', :status)"),
                                  {"id": str(index), "status": offer_status})
    candidates = await OfferRepository(session).list_accepted_for_contractor(user_id="contractor")
    assert {(offer.id_request, offer.status) for offer in candidates} == {("1", "accepted"), ("2", "accepted")}


@pytest.mark.asyncio
@pytest.mark.parametrize("owner_status, request_status, reason", [
    ("inactive", "open", "неактивен"),
    ("blacklist", "review", "в чёрном списке"),
    ("active", "open", None),
    ("inactive", "closed", None),
    ("blacklist", "cancelled", None),
])
async def test_request_owner_warning_is_limited_to_active_unassigned_requests(
    make_current_user, owner_status, request_status, reason,
):
    requests, users = AsyncMock(), AsyncMock()
    request = SimpleNamespace(id="234", id_user="owner", status=request_status, id_plan=None,
        description="Заявка", initial_amount=100, final_amount=None, deadline_at=None,
        created_at=None, updated_at=None, closed_at=None, id_offer=None)
    requests.get_with_stats.return_value = (request, None, None)
    requests.list_files.return_value = []
    requests.list_offers_with_files_and_contacts.return_value = []
    users.map_statuses.return_value = {"owner": owner_status}
    service = RequestService(requests=requests, files=AsyncMock(), users=users,
                             offers=AsyncMock(), user_status_periods=AsyncMock())
    result = await service.get_request_details(request_id="234", current_user=make_current_user(
        role_id=settings.superadmin_role_id, permissions={PermissionCodes.REQUESTS_READ}))
    if reason:
        assert "Заявка не распределена" in result.owner_warning
        assert reason in result.owner_warning
    else:
        assert result.owner_warning is None
    requests.list_with_stats_and_files.return_value = [(request, None, None, 0)]
    items = await service.list_requests(current_user=make_current_user(
        role_id=settings.superadmin_role_id, permissions={PermissionCodes.REQUESTS_READ}))
    assert items[0].owner_warning == result.owner_warning


def status_service(user, monkeypatch):
    users = AsyncMock()
    users.get_by_id.return_value = user
    async def update_status(target, status):
        target.status = status
    users.update_status.side_effect = update_status
    profiles = AsyncMock()
    profiles.get_by_id.return_value = None
    requests, offers = AsyncMock(), AsyncMock()
    hooks, published = [], []
    async def publish(event):
        published.append(event)
        return True
    managers = AsyncMock(return_value=[
        SimpleNamespace(user_id="manager", status="active"),
        SimpleNamespace(user_id="manager", status="active"),
        SimpleNamespace(user_id="blocked-manager", status="inactive"),
    ])
    monkeypatch.setattr(module.UnitHierarchyService, "get_user_managers", managers)
    service = module.UserStatusService(users, profiles, requests=requests, offers=offers,
        after_commit_hook_registrar=hooks.append, process_event_publisher=publish)
    return service, requests, offers, hooks, published


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["inactive", "blacklist"])
async def test_blocking_employee_notifies_active_managers_after_commit(make_current_user, monkeypatch, status):
    user = SimpleNamespace(id="employee", id_role=settings.economist_role_id, status="active")
    service, requests, offers, hooks, published = status_service(user, monkeypatch)
    requests.list_in_progress_requests_by_owner_ids.return_value = [SimpleNamespace(id="REQ-1"), SimpleNamespace(id="REQ-2")]
    actor = make_current_user(user_id="manager", role_id=settings.superadmin_role_id,
                              permissions={PermissionCodes.USERS_STATUS_UPDATE})
    await service.update_statuses(current_user=actor, user_id=user.id, user_status=status)
    assert published == []
    for hook in hooks:
        await hook()
    warnings = [event for event in published if event.event_type == "system.warning"]
    assert {event.request_id for event in warnings} == {"REQ-1", "REQ-2"}
    assert all(event.payload["recipient_user_ids"] == ["manager"] for event in warnings)
    assert all(event.payload["link_url"] == f"/requests/{event.request_id}" for event in warnings)
    assert all("нераспределённой" in event.payload["body"] for event in warnings)
    hooks.clear()
    await service.update_statuses(current_user=actor, user_id=user.id, user_status=status)
    assert hooks == []
    offers.update_status.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["inactive", "blacklist"])
async def test_blocking_contractor_rejects_active_accepted_offers_and_preserves_history(make_current_user, monkeypatch, status):
    user = SimpleNamespace(id="contractor", id_role=settings.contractor_role_id, status="active")
    service, requests, offers, hooks, published = status_service(user, monkeypatch)
    candidates = [SimpleNamespace(id=index, id_request=str(index), status="accepted") for index in range(1, 5)]
    offers.list_accepted_for_contractor.return_value = candidates
    offers.get_by_id.side_effect = lambda *, offer_id: candidates[offer_id - 1]
    requests.get_by_id.side_effect = lambda *, request_id: SimpleNamespace(
        id=request_id, id_user="owner", status={"1": "open", "2": "review", "3": "closed", "4": "cancelled"}[request_id])
    async def update_offer(*, offer, status):
        offer.status = status
    offers.update_status.side_effect = update_offer
    actor = make_current_user(role_id=settings.superadmin_role_id, permissions={PermissionCodes.USERS_STATUS_UPDATE})
    await service.update_statuses(current_user=actor, user_id=user.id, user_status=status)
    assert [offer.status for offer in candidates] == ["rejected", "rejected", "accepted", "accepted"]
    assert published == []
    for hook in hooks:
        await hook()
    assert {event.offer_id for event in published if event.event_type == "offer.status_changed"} == {1, 2}

