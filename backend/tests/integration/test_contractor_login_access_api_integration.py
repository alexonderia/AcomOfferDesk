from unittest.mock import AsyncMock

import pytest

from app.api.v1 import contractors as contractors_api
from app.domain.permissions import PermissionCodes
from app.services.contractors import ContractorLoginAccessResult


def test_login_access_requires_read_permission(test_client, set_current_user, make_current_user):
    set_current_user(make_current_user())
    response = test_client.get('/api/v1/contractors/login-access', params={'contractor_id': 'contractor-1'})
    assert response.status_code == 403


def test_login_access_returns_only_public_status_metadata(test_client, set_current_user, make_current_user, monkeypatch):
    set_current_user(make_current_user(permissions={PermissionCodes.CONTRACTORS_READ}))
    method = AsyncMock(return_value=[ContractorLoginAccessResult(
        user_id='contractor-1', state='available', label='Вход доступен', description='Учётная запись готова к входу.',
    )])
    monkeypatch.setattr(contractors_api.ContractorService, 'check_login_access', method)
    response = test_client.get('/api/v1/contractors/login-access', params={'contractor_id': 'contractor-1'})
    assert response.status_code == 200
    [item] = response.json()['data']['items']
    assert set(item) == {'user_id', 'state', 'label', 'description'}
    assert item['state'] == 'available'
    assert method.await_args.kwargs['contractor_ids'] == ['contractor-1']


@pytest.mark.parametrize('params', [{}, [('contractor_id', f'contractor-{i}') for i in range(101)]])
def test_login_access_rejects_missing_or_oversized_batches(test_client, set_current_user, make_current_user, monkeypatch, params):
    set_current_user(make_current_user(permissions={PermissionCodes.CONTRACTORS_READ}))
    method = AsyncMock()
    monkeypatch.setattr(contractors_api.ContractorService, 'check_login_access', method)
    response = test_client.get('/api/v1/contractors/login-access', params=params)
    assert response.status_code == 422
    method.assert_not_awaited()
