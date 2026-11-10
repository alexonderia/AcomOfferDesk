from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.domain.exceptions import Conflict, Forbidden
from app.domain.permissions import PermissionCodes
from app.schemas.offers import ManualOfferEligibleContractorItem
from app.services.offers import OfferService
from app.services.users import ManualContractorService


@pytest.fixture
def manual_offer_context(make_current_user):
    owner = SimpleNamespace(id="economist-1", id_role=settings.economist_role_id)
    contractor = SimpleNamespace(id="contractor-1", id_role=settings.contractor_role_id, status="active")
    users = AsyncMock()
    users.get_by_id.side_effect = lambda user_id: {owner.id: owner, contractor.id: contractor}.get(user_id)
    users.list_contractors.return_value = [(contractor, None, None, None, None)]
    users.list_active_units.return_value = [(101, None), (102, None)]
    users.list_active_unit_memberships.return_value = [(owner.id, 101), (contractor.id, 101)]
    request = SimpleNamespace(id="request-1", id_user=owner.id, status="open")
    requests = AsyncMock()
    requests.get_by_id.return_value = request
    requests.is_hidden_for_contractor.return_value = False
    offers = AsyncMock()
    offers.get_contractor_offer_for_request.return_value = None
    offers.create.return_value = SimpleNamespace(id=60)
    service = OfferService(
        requests=requests, offers=offers, users=users, units=AsyncMock(),
        chats=AsyncMock(), files=AsyncMock(), messages=AsyncMock(),
        profiles=AsyncMock(), company_contacts=AsyncMock(),
    )
    return SimpleNamespace(
        service=service, owner=owner, contractor=contractor, users=users,
        requests=requests, request=request, offers=offers,
        actor=make_current_user(user_id=owner.id, permissions={PermissionCodes.OFFERS_MANUAL_CREATE}),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [None, "deleted", "submitted", "accepted", "rejected"])
async def test_existing_offer_stays_visible_with_server_selection_state(manual_offer_context, status):
    ctx = manual_offer_context
    ctx.offers.get_contractor_offer_for_request.return_value = (
        SimpleNamespace(status=status) if status is not None else None
    )

    items = await ctx.service.list_eligible_contractors_for_manual_offer(
        current_user=ctx.actor, request_id=ctx.request.id,
    )

    assert len(items) == 1
    item = ManualOfferEligibleContractorItem(**items[0].__dict__).model_dump()
    assert item["user_id"] == ctx.contractor.id
    assert item["can_select"] is (status in {None, "deleted"})
    assert item["disabled_reason"] == (
        None if status in {None, "deleted"}
        else "Данный контрагент уже приложил КП к текущей заявке"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("restriction", ["inactive", "hidden", "outside_scope", "operator_owner", "closed"])
async def test_existing_offer_does_not_bypass_other_list_restrictions(manual_offer_context, restriction):
    ctx = manual_offer_context
    ctx.offers.get_contractor_offer_for_request.return_value = SimpleNamespace(status="submitted")
    if restriction == "inactive":
        ctx.contractor.status = "inactive"
    elif restriction == "hidden":
        ctx.requests.is_hidden_for_contractor.return_value = True
    elif restriction == "outside_scope":
        ctx.users.list_active_unit_memberships.return_value = [(ctx.owner.id, 101), (ctx.contractor.id, 102)]
    elif restriction == "operator_owner":
        ctx.owner.id_role = settings.operator_role_id
    else:
        ctx.request.status = "closed"

    assert await ctx.service.list_eligible_contractors_for_manual_offer(
        current_user=ctx.actor, request_id=ctx.request.id,
    ) == []


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["submitted", "accepted", "rejected"])
async def test_disabled_contractor_cannot_be_submitted_directly(manual_offer_context, status):
    ctx = manual_offer_context
    ctx.offers.get_contractor_offer_for_request.return_value = SimpleNamespace(status=status)

    with pytest.raises(Conflict, match="уже существует КП"):
        await ctx.service.create_manual_offer(
            current_user=ctx.actor, request_id=ctx.request.id,
            contractor_user_id=ctx.contractor.id, contractor_data=None,
        )
    ctx.offers.create.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [None, "deleted"])
async def test_selectable_contractor_can_create_offer(manual_offer_context, status):
    ctx = manual_offer_context
    ctx.offers.get_contractor_offer_for_request.return_value = (
        SimpleNamespace(status=status) if status is not None else None
    )

    result = await ctx.service.create_manual_offer(
        current_user=ctx.actor, request_id=ctx.request.id,
        contractor_user_id=ctx.contractor.id, contractor_data=None,
    )

    assert result.offer_id == 60
    ctx.offers.create.assert_awaited_once_with(
        request_id=ctx.request.id, contractor_user_id=ctx.contractor.id, offer_amount=None,
    )


@pytest.mark.asyncio
async def test_list_requires_manual_offer_permission(manual_offer_context, make_current_user):
    ctx = manual_offer_context
    with pytest.raises(Forbidden):
        await ctx.service.list_eligible_contractors_for_manual_offer(
            current_user=make_current_user(user_id=ctx.owner.id), request_id=ctx.request.id,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("query", [
    {"company_name": "бетон"}, {"inn": "770708"}, {"company_mail": "office@"},
])
@pytest.mark.parametrize("offer_status", [None, "submitted", "deleted"])
async def test_request_duplicate_search_uses_offer_permission_and_selection_flags(manual_offer_context, query, offer_status):
    ctx = manual_offer_context
    ctx.contractor.created_at = ctx.contractor.updated_at = None
    company = SimpleNamespace(
        company_name="ООО Бетон", inn="7707083893", phone="+79991234567",
        mail="office@example.com", address=None, note=None,
    )
    row = (ctx.contractor, None, company, None, None)
    ctx.users.list_contractors.return_value = [row]
    ctx.users.list_contractors_page.return_value = ([row], 1)
    ctx.offers.get_contractor_offer_for_request.return_value = (
        SimpleNamespace(status=offer_status) if offer_status else None
    )

    items = await ctx.service.list_manual_offer_contractor_duplicates(
        current_user=ctx.actor, request_id=ctx.request.id, **query,
    )

    assert len(items) == 1
    assert items[0].user_id == ctx.contractor.id
    assert items[0].inn == "7707083893"
    assert items[0].can_select is (offer_status != "submitted")
    assert bool(items[0].disabled_reason) is (offer_status == "submitted")
    # Directory permission is independent and must remain protected.
    directory = ManualContractorService(ctx.users, AsyncMock(), AsyncMock(), AsyncMock(), AsyncMock())
    with pytest.raises(Forbidden):
        await directory.list_possible_duplicates(current_user=ctx.actor, **query)


@pytest.mark.asyncio
@pytest.mark.parametrize("restriction", ["inactive", "hidden", "outside_scope", "operator_owner", "closed", "foreign_owner", "no_permission"])
async def test_request_duplicate_search_does_not_leak_ineligible_contractors(manual_offer_context, make_current_user, restriction):
    ctx = manual_offer_context
    if restriction == "inactive":
        ctx.contractor.status = "inactive"
    elif restriction == "hidden":
        ctx.requests.is_hidden_for_contractor.return_value = True
    elif restriction == "outside_scope":
        ctx.users.list_active_unit_memberships.return_value = [(ctx.owner.id, 101), (ctx.contractor.id, 102)]
    elif restriction == "operator_owner":
        ctx.owner.id_role = settings.operator_role_id
    elif restriction == "closed":
        ctx.request.status = "closed"
    elif restriction == "foreign_owner":
        ctx.request.id_user = "another-economist"
    else:
        ctx.actor = make_current_user(user_id=ctx.owner.id)

    if restriction in {"foreign_owner", "no_permission"}:
        with pytest.raises(Forbidden):
            await ctx.service.list_manual_offer_contractor_duplicates(
                current_user=ctx.actor, request_id=ctx.request.id, company_name="Бетон",
            )
    else:
        assert await ctx.service.list_manual_offer_contractor_duplicates(
            current_user=ctx.actor, request_id=ctx.request.id, company_name="Бетон",
        ) == []
    ctx.users.list_contractors_page.assert_not_awaited()


@pytest.mark.asyncio
async def test_request_duplicate_search_filters_repository_results_to_authorized_ids(manual_offer_context):
    ctx = manual_offer_context
    outside_contractor = SimpleNamespace(id="outside", status="active", created_at=None, updated_at=None)
    company = SimpleNamespace(company_name="ООО Бетон", inn="7707083893", phone=None, mail=None, address=None, note=None)
    ctx.users.list_contractors_page.return_value = ([(outside_contractor, None, company, None, None)], 1)

    assert await ctx.service.list_manual_offer_contractor_duplicates(
        current_user=ctx.actor, request_id=ctx.request.id, company_name="Бетон",
    ) == []
