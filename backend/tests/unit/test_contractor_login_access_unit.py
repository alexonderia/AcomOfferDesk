from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.core.datetime_utils import utc_now
from app.domain.exceptions import AuthenticationUnavailable, Forbidden, NotFound
from app.domain.permissions import PermissionCodes
from app.services.contractors import ContractorService


@pytest.fixture
def context(make_current_user):
    user = SimpleNamespace(id="contractor-1", id_role=settings.contractor_role_id, status="active")
    binding = SimpleNamespace(id_user=user.id, external_subject_id="account-1", is_active=True)
    users = AsyncMock()
    users.list_by_ids_with_profiles_and_roles.return_value = [(user, None, None)]
    users.list_active_units.return_value = [(10, None), (20, None)]
    users.list_active_unit_memberships.return_value = [("viewer", 10), (user.id, 10)]
    bindings = AsyncMock()
    bindings.list_for_users.return_value = [binding]
    state = SimpleNamespace(id="account-1", login=user.id, role="contractor", auth_status="active",
        role_active=True, password_set=True, required_actions=(), password_locked_until=None)
    iam = AsyncMock()
    iam.get_credential_state.return_value = state
    service = ContractorService(users, AsyncMock(), AsyncMock(), user_auth_accounts=bindings, iam_client=iam)
    actor = make_current_user(user_id="viewer", permissions={PermissionCodes.CONTRACTORS_READ})
    return SimpleNamespace(user=user, binding=binding, users=users, bindings=bindings, state=state,
        iam=iam, service=service, actor=actor)


@pytest.mark.asyncio
@pytest.mark.parametrize("case,expected", [
    ("ready", "available"), ("no_binding", "not_granted"), ("inactive_binding", "blocked"),
    ("inactive_user", "blocked"), ("blacklist_user", "blocked"), ("review_user", "pending"),
    ("pending_iam", "pending"), ("blocked_iam", "blocked"), ("disabled_iam", "blocked"),
    ("no_password", "password_not_set"), ("inactive_role", "blocked"), ("missing_role_state", "unknown"),
    ("profile_required", "setup_required"), ("locked_password", "temporarily_locked"),
    ("expired_lock", "available"), ("wrong_login", "unknown"), ("wrong_role", "unknown"),
    ("wrong_subject", "unknown"), ("missing_account", "not_granted"), ("iam_down", "unknown"),
])
async def test_login_access_uses_authoritative_account_state(context, case, expected):
    ctx = context
    if case == "no_binding": ctx.bindings.list_for_users.return_value = []
    elif case == "inactive_binding": ctx.binding.is_active = False
    elif case.endswith("_user"): ctx.user.status = case.removesuffix("_user")
    elif case.endswith("_iam"): ctx.state.auth_status = case.removesuffix("_iam")
    elif case == "no_password": ctx.state.password_set = False
    elif case == "inactive_role": ctx.state.role_active = False
    elif case == "missing_role_state": ctx.state.role_active = None
    elif case == "profile_required": ctx.state.required_actions = ("complete_profile",)
    elif case == "locked_password": ctx.state.password_locked_until = (utc_now() + timedelta(minutes=2)).isoformat()
    elif case == "expired_lock": ctx.state.password_locked_until = (utc_now() - timedelta(minutes=2)).isoformat()
    elif case == "wrong_login": ctx.state.login = "another-user"
    elif case == "wrong_role": ctx.state.role = "economist"
    elif case == "wrong_subject": ctx.state.id = "another-subject"
    elif case == "missing_account": ctx.iam.get_credential_state.side_effect = NotFound()
    elif case == "iam_down": ctx.iam.get_credential_state.side_effect = AuthenticationUnavailable()

    [result] = await ctx.service.check_login_access(current_user=ctx.actor, contractor_ids=[ctx.user.id])

    assert result.state == expected
    assert result.user_id == ctx.user.id
    assert result.label and result.description
    if case in {"no_binding", "inactive_binding", "inactive_user", "blacklist_user", "review_user"}:
        ctx.iam.get_credential_state.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("case,error", [("permission", Forbidden), ("scope", Forbidden), ("missing", NotFound), ("employee", NotFound)])
async def test_login_access_checks_permission_scope_and_target_before_iam(context, make_current_user, case, error):
    ctx = context
    if case == "permission": ctx.actor = make_current_user(user_id="viewer")
    elif case == "scope": ctx.users.list_active_unit_memberships.return_value = [("viewer", 10), (ctx.user.id, 20)]
    elif case == "missing": ctx.users.list_by_ids_with_profiles_and_roles.return_value = []
    else: ctx.user.id_role = settings.economist_role_id
    with pytest.raises(error):
        await ctx.service.check_login_access(current_user=ctx.actor, contractor_ids=[ctx.user.id])
    ctx.iam.get_credential_state.assert_not_awaited()
    ctx.bindings.list_for_users.assert_not_awaited()


@pytest.mark.asyncio
async def test_users_read_fallback_and_deduplicated_batch(context, make_current_user):
    ctx = context
    result = await ctx.service.check_login_access(
        current_user=make_current_user(user_id="viewer", permissions={PermissionCodes.USERS_READ}),
        contractor_ids=[ctx.user.id, ctx.user.id],
    )
    assert len(result) == 1 and result[0].state == "available"
    ctx.iam.get_credential_state.assert_awaited_once()
    ctx.bindings.list_for_users.assert_awaited_once_with(user_ids=[ctx.user.id], provider="iam")


@pytest.mark.asyncio
@pytest.mark.parametrize("outside_scope", [False, True])
async def test_offer_contractor_info_permission_checks_login_access_in_same_unit_scope(context, make_current_user, outside_scope):
    ctx = context
    actor = make_current_user(user_id="viewer", permissions={PermissionCodes.OFFERS_CONTRACTOR_INFO_READ})
    if outside_scope:
        ctx.users.list_active_unit_memberships.return_value = [("viewer", 10), (ctx.user.id, 20)]
        with pytest.raises(Forbidden):
            await ctx.service.check_login_access(current_user=actor, contractor_ids=[ctx.user.id])
        ctx.iam.get_credential_state.assert_not_awaited()
    else:
        [result] = await ctx.service.check_login_access(current_user=actor, contractor_ids=[ctx.user.id])
        assert result.state == "available"


@pytest.mark.asyncio
async def test_contractor_offer_info_permission_cannot_inspect_other_identity(context, make_current_user):
    ctx = context
    actor = make_current_user(user_id="viewer", role_id=settings.contractor_role_id,
                              permissions={PermissionCodes.OFFERS_CONTRACTOR_INFO_READ})
    with pytest.raises(Forbidden):
        await ctx.service.check_login_access(current_user=actor, contractor_ids=[ctx.user.id])
    ctx.iam.get_credential_state.assert_not_awaited()


@pytest.mark.asyncio
async def test_contractor_can_check_own_access_with_offer_info_permission(context, make_current_user):
    ctx = context
    actor = make_current_user(user_id=ctx.user.id, role_id=settings.contractor_role_id,
                              permissions={PermissionCodes.OFFERS_CONTRACTOR_INFO_READ})
    [result] = await ctx.service.check_login_access(current_user=actor, contractor_ids=[ctx.user.id])
    assert result.state == 'available'
    ctx.iam.get_credential_state.assert_awaited_once_with(account_id=ctx.binding.external_subject_id)
