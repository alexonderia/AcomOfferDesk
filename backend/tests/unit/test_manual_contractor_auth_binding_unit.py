from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.domain.exceptions import AuthenticationUnavailable
from app.services import iam_bindings
from app.services.offers import OfferService
from app.services.users import ManualContractorCreateInput, ManualContractorService


@pytest.fixture
def creation_context(monkeypatch, make_current_user):
    owner = SimpleNamespace(id="economist-1", id_role=settings.economist_role_id)
    stored_users = {owner.id: owner}
    stored_companies = {}
    memberships = [(owner.id, 101)]
    users = AsyncMock()
    users.exists.side_effect = lambda user_id: user_id in stored_users
    users.get_by_id.side_effect = lambda user_id: stored_users.get(user_id)
    users.add.side_effect = lambda user: stored_users.update({user.id: user})
    users.find_matching_contractor_user_ids.return_value = []
    users.list_active_units.return_value = [(101, None)]
    users.list_active_unit_memberships.side_effect = lambda: list(memberships)
    companies = AsyncMock()
    companies.add.side_effect = lambda company: stored_companies.update({company.id: company})
    companies.get_by_id.side_effect = lambda user_id: stored_companies.get(user_id)
    units = AsyncMock()
    units.list_units.return_value = [SimpleNamespace(id=101, id_parent=None, is_active=True)]
    units.get_member.return_value = None
    units.add_member.side_effect = lambda member: memberships.append((member.id_user, member.id_unit))
    bindings = AsyncMock()
    bindings.get_by_user_provider.return_value = None
    bindings.get_conflicting_subject.return_value = None
    iam = SimpleNamespace(put_account=AsyncMock(side_effect=lambda **kw: SimpleNamespace(
        id=kw["account_id"], login=kw["login"], role=kw["role"], auth_status=kw["auth_status"],
    )))
    monkeypatch.setattr(iam_bindings, "IamClient", lambda: iam)
    requests = AsyncMock()
    requests.get_by_id.return_value = SimpleNamespace(id="request-1", id_user=owner.id, status="open")
    requests.is_hidden_for_contractor.return_value = False
    offers = AsyncMock()
    offers.get_contractor_offer_for_request.return_value = None
    offers.create.return_value = SimpleNamespace(id=60)
    shared = dict(users=users, profiles=AsyncMock(), company_contacts=companies,
                  user_auth_accounts=bindings, units=units)
    return SimpleNamespace(
        directory=ManualContractorService(**shared),
        offer_service=OfferService(**shared, requests=requests, offers=offers,
                                  chats=AsyncMock(), files=AsyncMock(), messages=AsyncMock()),
        offers=offers, iam=iam, bindings=bindings, users=stored_users, memberships=memberships,
        actor=make_current_user(user_id=owner.id, permissions={"offers.manual.create", "contractors.manual.create"}),
        data=ManualContractorCreateInput(company_name="ООО Бетон", inn="7707083893", company_phone="+79991234567"),
    )


async def create_from_path(ctx, path):
    if path == "directory":
        result = await ctx.directory.create_manual_contractor(current_user=ctx.actor, data=ctx.data)
        assert result.created
        return result.user_id
    result = await ctx.offer_service.create_manual_offer(
        current_user=ctx.actor, request_id="request-1", contractor_user_id=None, contractor_data=ctx.data,
    )
    assert result.contractor_created
    assert result.offer_id == 60
    return result.contractor_user_id


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["directory", "manual_offer"])
async def test_new_contractor_always_gets_iam_identity_without_email_or_password(creation_context, path):
    ctx = creation_context
    user_id = await create_from_path(ctx, path)

    ctx.iam.put_account.assert_awaited_once()
    provisioned = ctx.iam.put_account.await_args.kwargs
    assert provisioned["login"] == user_id
    assert provisioned["role"] == "contractor"
    assert provisioned["auth_status"] == "active"
    ctx.bindings.add.assert_awaited_once()
    binding = ctx.bindings.add.await_args.args[0]
    assert binding.id_user == user_id
    assert binding.external_subject_id == str(provisioned["account_id"])
    assert binding.is_active
    assert binding.external_email is None
    assert ctx.users[user_id].status == "active"
    assert (user_id, 101) in ctx.memberships


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["directory", "manual_offer"])
async def test_iam_failure_cannot_complete_contractor_or_offer_creation(creation_context, path):
    ctx = creation_context
    ctx.iam.put_account.side_effect = AuthenticationUnavailable()

    with pytest.raises(AuthenticationUnavailable):
        await create_from_path(ctx, path)

    ctx.bindings.add.assert_not_awaited()
    ctx.offers.create.assert_not_awaited()
