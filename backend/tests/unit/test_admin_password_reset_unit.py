from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI

from app.api.dependencies import get_current_user, get_uow
from app.api.v1.users import router
from app.domain.auth_context import CurrentUser
from app.domain.exceptions import Conflict, Forbidden, NotFound
from app.infrastructure.iam_client import IamClient
from app.models.orm_models import User
from app.schemas.users import UserPasswordResetRequest
from app.services.user_password_reset import reset_user_password
from app.api.action_flags import UserActionBuilder, ContractorActionBuilder


PASSWORD = 'Replacement password 456'
ACTOR = CurrentUser('root', 'actor-id', 'session-id', 'superadmin', 1, 'active', frozenset({'users.password.update'}))


@pytest.fixture
def setup_reset(monkeypatch):
    uow = SimpleNamespace(
        users=SimpleNamespace(get_by_id=AsyncMock(return_value=User(id='employee', id_role=6, status='active'))),
        user_auth_accounts=SimpleNamespace(get_by_user_provider=AsyncMock(return_value=SimpleNamespace(
            is_active=True, external_subject_id='target-id',
        ))),
    )
    client = SimpleNamespace(
        get_credential_state=AsyncMock(return_value=SimpleNamespace(login='employee', role='economist')),
        reset_user_password=AsyncMock(),
    )
    monkeypatch.setattr('app.services.user_password_reset.IamClient', lambda: client)
    uow.users.list_active_units = AsyncMock(return_value=[(10, None), (11, 10), (20, None)])
    uow.users.list_active_unit_memberships = AsyncMock(return_value=[('admin', 10), ('employee', 11)])
    return uow, client


@pytest.mark.asyncio
@pytest.mark.parametrize('target_role_id,iam_role', [(2, 'admin'), (3, 'contractor'), (6, 'economist')])
async def test_admin_can_reset_users_in_own_department_including_nested_units(setup_reset, target_role_id, iam_role):
    uow, client = setup_reset
    actor = replace(ACTOR, user_id='admin', system_role='admin', role_id=2)
    uow.users.get_by_id.return_value = User(id='employee', id_role=target_role_id, status='active')
    client.get_credential_state.return_value = SimpleNamespace(login='employee', role=iam_role)
    await reset_user_password(uow, current_user=actor, user_id='employee', new_password=PASSWORD)
    client.reset_user_password.assert_awaited_once_with(
        account_id='target-id', new_password=PASSWORD, actor_account_id='actor-id', actor_session_id='session-id',
        department_scope_verified=True,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize('memberships', [
    [('admin', 10), ('employee', 20)], [('employee', 11)], [('admin', 10)], [],
    [('admin', 10), ('employee', 999)],
])
async def test_admin_cannot_reset_outside_active_department_scope(setup_reset, memberships):
    uow, client = setup_reset
    uow.users.list_active_unit_memberships.return_value = memberships
    actor = replace(ACTOR, user_id='admin', system_role='admin', role_id=2)
    with pytest.raises(Forbidden):
        await reset_user_password(uow, current_user=actor, user_id='employee', new_password=PASSWORD)
    client.get_credential_state.assert_not_awaited()
    client.reset_user_password.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize('role_id', [1, 2])
async def test_reset_requires_verified_password_permission_even_for_privileged_roles(setup_reset, role_id):
    uow, client = setup_reset
    with pytest.raises(Forbidden):
        await reset_user_password(uow, current_user=replace(ACTOR, role_id=role_id, permissions=frozenset()), user_id='employee', new_password=PASSWORD)
    client.reset_user_password.assert_not_awaited()


@pytest.mark.parametrize('actor_role,in_scope,expected', [(1, False, True), (2, True, True), (2, False, False), (4, True, False)])
def test_password_action_uses_same_policy_for_employee_and_contractor_lists(actor_role, in_scope, expected):
    actor = replace(ACTOR, role_id=actor_role)
    staff = UserActionBuilder.build_list_item(actor, target_user_id='employee', target_role_id=6,
                                            is_in_password_reset_scope=in_scope)
    contractor = ContractorActionBuilder.build_contractor_actions(actor, target_user_id='contractor',
                                                                  is_in_password_reset_scope=in_scope)
    assert staff.can_reset_password is expected
    assert contractor.can_reset_password is expected
    assert not UserActionBuilder.build_list_item(actor, target_user_id=actor.user_id, target_role_id=actor_role,
                                                 is_in_password_reset_scope=True).can_reset_password
    assert not UserActionBuilder.build_list_item(actor, target_user_id='root-2', target_role_id=1,
                                                 is_in_password_reset_scope=True).can_reset_password


@pytest.mark.asyncio
async def test_reset_routes_exact_target_and_actor_without_old_password(setup_reset):
    uow, client = setup_reset
    await reset_user_password(uow, current_user=ACTOR, user_id='employee', new_password=PASSWORD)
    client.reset_user_password.assert_awaited_once_with(
        account_id='target-id', new_password=PASSWORD, actor_account_id='actor-id', actor_session_id='session-id',
    )


@pytest.mark.asyncio
@pytest.mark.parametrize('status', ['active', 'inactive', 'review', 'blacklist'])
async def test_contractor_initial_password_uses_persisted_role_and_preserves_business_status(setup_reset, status):
    uow, client = setup_reset
    target = User(id='contractor', id_role=3, status=status)
    uow.users.get_by_id.return_value = target
    client.get_credential_state.return_value = SimpleNamespace(login='contractor', role='contractor', password_set=False)

    await reset_user_password(uow, current_user=ACTOR, user_id='contractor', new_password=PASSWORD)

    client.reset_user_password.assert_awaited_once_with(
        account_id='target-id', new_password=PASSWORD, actor_account_id='actor-id', actor_session_id='session-id',
    )
    assert target.id_role == 3
    assert target.status == status


@pytest.mark.asyncio
@pytest.mark.parametrize('role_id,status', [(role, 'active') for role in range(3, 9)] + [(1, 'inactive'), (1, 'review'), (2, 'inactive')])
async def test_only_active_privileged_roles_may_reset(setup_reset, role_id, status):
    uow, client = setup_reset
    with pytest.raises(Forbidden):
        await reset_user_password(uow, current_user=replace(ACTOR, role_id=role_id, status=status), user_id='employee', new_password=PASSWORD)
    client.reset_user_password.assert_not_awaited()
    uow.users.get_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_superadmin_target_and_self_are_protected(setup_reset):
    uow, client = setup_reset
    for user_id, role_id in [('employee', 1), ('root', 6)]:
        uow.users.get_by_id.return_value = User(id=user_id, id_role=role_id, status='active')
        with pytest.raises(Forbidden):
            await reset_user_password(uow, current_user=ACTOR, user_id=user_id, new_password=PASSWORD)
    client.reset_user_password.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_or_mismatched_identity_never_resets_another_account(setup_reset):
    uow, client = setup_reset
    uow.users.get_by_id.return_value = None
    with pytest.raises(NotFound):
        await reset_user_password(uow, current_user=ACTOR, user_id='employee', new_password=PASSWORD)
    uow.users.get_by_id.return_value = User(id='employee', id_role=6, status='active')
    for binding in (None, SimpleNamespace(is_active=False)):
        uow.user_auth_accounts.get_by_user_provider.return_value = binding
        with pytest.raises(Conflict):
            await reset_user_password(uow, current_user=ACTOR, user_id='employee', new_password=PASSWORD)
    uow.user_auth_accounts.get_by_user_provider.return_value = SimpleNamespace(is_active=True, external_subject_id='target-id')
    for login, role in [('different-user', 'economist'), ('employee', 'superadmin')]:
        client.get_credential_state.return_value = SimpleNamespace(login=login, role=role)
        with pytest.raises(Conflict):
            await reset_user_password(uow, current_user=ACTOR, user_id='employee', new_password=PASSWORD)
    client.reset_user_password.assert_not_awaited()


@pytest.mark.parametrize('password,confirmation', [('short', 'short'), ('x' * 129, 'x' * 129), (PASSWORD, PASSWORD + '!')])
def test_reset_payload_validates_policy_and_confirmation(password, confirmation):
    with pytest.raises(ValueError):
        UserPasswordResetRequest(new_password=password, password_confirmation=confirmation)


@pytest.mark.asyncio
async def test_http_reset_returns_empty_response_without_exposing_password(setup_reset):
    uow, client = setup_reset
    class Uow:
        users = uow.users
        user_auth_accounts = uow.user_auth_accounts
        async def __aenter__(self): return self
        async def __aexit__(self, *_args): return None
    app = FastAPI()
    app.include_router(router, prefix='/api/v1')
    app.dependency_overrides[get_current_user] = lambda: ACTOR
    app.dependency_overrides[get_uow] = Uow
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as browser:
        response = await browser.post('/api/v1/users/employee/password/reset', json={
            'new_password': PASSWORD, 'password_confirmation': PASSWORD,
        })
    assert response.status_code == 204 and not response.content
    client.reset_user_password.assert_awaited_once()


@pytest.mark.asyncio
async def test_iam_client_uses_internal_reset_endpoint_with_actor_context():
    seen = []
    def handle(request):
        seen.append(request)
        return httpx.Response(204)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handle), base_url='http://iam') as transport:
        await IamClient(transport).reset_user_password(
            account_id='target', new_password=PASSWORD, actor_account_id='actor', actor_session_id='session',
        )
    assert seen[0].url.path == '/internal/accounts/target/password/reset'
    assert 'current_password' not in seen[0].content.decode()
    assert seen[0].headers['X-Acom-Service-Token']
