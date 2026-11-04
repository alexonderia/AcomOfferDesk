import asyncio
from dataclasses import replace
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import FastAPI

from app.api.dependencies import get_current_user
from app.api.v1 import system_status as api
from app.domain.auth_context import CurrentUser
from app.domain.exceptions import Forbidden
from app.services import system_status as module


ACTOR = CurrentUser('root', 'actor', 'session', 'superadmin', 1, 'active', frozenset())
PROBES = ['probe_database', 'probe_iam', 'probe_storage', 'probe_broker', 'probe_file_guard']


@pytest.fixture
def healthy(monkeypatch):
    monkeypatch.setattr(module.settings, 'file_guard_enabled', True)
    probes = {name: AsyncMock(return_value=module.ProbeResult('Проверка пройдена')) for name in PROBES}
    for name, probe in probes.items():
        monkeypatch.setattr(module, name, probe)
    return probes


@pytest.mark.asyncio
async def test_status_uses_allowlisted_settings_and_never_returns_secrets(healthy, monkeypatch):
    secret = 'private-service-password-and-token'
    for field in ['email_app_password', 's3_secret_key', 'iam_internal_service_token', 'jwt_secret']:
        monkeypatch.setattr(module.settings, field, secret)
    monkeypatch.setattr(module.settings, 'email_enabled', False)
    result = await module.SystemStatusService().get_status()
    assert result.overall == 'healthy'
    assert result.settings.email_enabled is False
    assert len(result.services) == 6
    assert result.services[0].response_ms is None
    assert all(item.response_ms >= 0 for item in result.services[1:])
    assert secret not in result.model_dump_json()
    assert result.checked_at.tzinfo is not None
    assert result.uptime_seconds >= 0


@pytest.mark.asyncio
async def test_failure_is_isolated_and_remote_exception_is_not_exposed(healthy):
    healthy['probe_iam'].side_effect = RuntimeError('https://private:secret@internal/private-key')
    result = await module.SystemStatusService().get_status()
    assert result.overall == 'degraded'
    assert next(item for item in result.services if item.key == 'iam').status == 'down'
    assert next(item for item in result.services if item.key == 'database').status == 'up'
    assert 'private' not in result.model_dump_json() and 'secret' not in result.model_dump_json()


@pytest.mark.asyncio
async def test_disabled_file_guard_is_not_probed_and_is_not_a_failure(healthy, monkeypatch):
    monkeypatch.setattr(module.settings, 'file_guard_enabled', False)
    result = await module.SystemStatusService().get_status()
    item = next(item for item in result.services if item.key == 'file_guard')
    assert item.status == 'disabled' and item.response_ms is None
    assert result.overall == 'healthy'
    healthy['probe_file_guard'].assert_not_awaited()


@pytest.mark.asyncio
async def test_unconfirmed_antivirus_is_degraded_not_healthy(healthy):
    healthy['probe_file_guard'].return_value = module.ProbeResult('Антивирус выключен', degraded=True)
    result = await module.SystemStatusService().get_status()
    assert result.overall == 'degraded'
    assert result.services[-1].status == 'degraded'


@pytest.mark.asyncio
async def test_timeout_does_not_prevent_other_results(healthy, monkeypatch):
    async def hang():
        await asyncio.sleep(10)
    healthy['probe_storage'].side_effect = hang
    monkeypatch.setattr(module, 'PROBE_TIMEOUT_SECONDS', 0.02)
    result = await asyncio.wait_for(module.SystemStatusService().get_status(), timeout=0.5)
    storage = next(item for item in result.services if item.key == 'storage')
    assert storage.status == 'down' and 'время' in storage.detail
    assert result.services[1].status == 'up'


@pytest.mark.asyncio
async def test_probes_run_in_parallel_and_requests_share_cache(healthy):
    started = 0
    ready = asyncio.Event()
    async def wait_for_others():
        nonlocal started
        started += 1
        if started == 5:
            ready.set()
        await asyncio.wait_for(ready.wait(), timeout=0.5)
        return module.ProbeResult('ok')
    for probe in healthy.values():
        probe.side_effect = wait_for_others
    service = module.SystemStatusService()
    results = await asyncio.gather(*(service.get_status() for _ in range(5)))
    assert all(result.overall == 'healthy' for result in results)
    assert len({result.checked_at for result in results}) == 1
    for probe in healthy.values():
        probe.assert_awaited_once()
    service._expires_at = 0
    await service.get_status()
    assert all(probe.await_count == 2 for probe in healthy.values())


@pytest.mark.asyncio
@pytest.mark.parametrize('role,status', [(role, 'active') for role in range(2, 9)] + [(1, 'inactive'), (1, 'review')])
async def test_non_superadmin_cannot_trigger_probes_or_read_cached_settings(healthy, monkeypatch, role, status):
    service = module.SystemStatusService()
    service.get_status = AsyncMock()
    monkeypatch.setattr(api, 'status_service', service)
    with pytest.raises(Forbidden):
        await api.get_system_status(response=MagicMock(), current_user=replace(ACTOR, role_id=role, status=status))
    service.get_status.assert_not_awaited()


@pytest.mark.asyncio
async def test_status_http_endpoint_is_not_cacheable(healthy, monkeypatch):
    monkeypatch.setattr(api, 'status_service', module.SystemStatusService())
    app = FastAPI()
    app.include_router(api.router, prefix='/api/v1')
    app.dependency_overrides[get_current_user] = lambda: ACTOR
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
        response = await client.get('/api/v1/system/status')
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'no-store'
    assert response.json()['data']['overall'] == 'healthy'


@pytest.mark.asyncio
@pytest.mark.parametrize('antivirus,expected', [('ready', False), ('disabled', True), (None, True)])
async def test_file_guard_probe_checks_antivirus_readiness(monkeypatch, antivirus, expected):
    factory = module.httpx.AsyncClient
    transport = httpx.MockTransport(lambda req: httpx.Response(200, json={'status': 'ok', 'antivirus': antivirus}))
    monkeypatch.setattr(module.httpx, 'AsyncClient', lambda **kwargs: factory(transport=transport, **kwargs))
    result = await module.probe_file_guard()
    assert result.degraded is expected


@pytest.mark.asyncio
async def test_iam_probe_requires_readiness_not_only_http_success(monkeypatch):
    factory = module.httpx.AsyncClient
    transport = httpx.MockTransport(lambda req: httpx.Response(200, json={'status': 'not_ready'}))
    monkeypatch.setattr(module.httpx, 'AsyncClient', lambda **kwargs: factory(transport=transport, **kwargs))
    with pytest.raises(ValueError):
        await module.probe_iam()


def test_storage_probe_only_checks_existing_bucket_and_closes_transport(monkeypatch):
    pool = MagicMock()
    storage = MagicMock()
    storage.bucket_exists.return_value = False
    monkeypatch.setattr(module.urllib3, 'PoolManager', lambda **kwargs: pool)
    monkeypatch.setattr(module, 'Minio', lambda *args, **kwargs: storage)
    with pytest.raises(ValueError):
        module._probe_storage_sync()
    storage.bucket_exists.assert_called_once_with(module.settings.s3_bucket)
    storage.make_bucket.assert_not_called()
    storage.put_object.assert_not_called()
    pool.clear.assert_called_once()


@pytest.mark.asyncio
async def test_broker_probe_authenticates_and_closes_without_publishing(monkeypatch):
    connection = MagicMock()
    connection.__aenter__ = AsyncMock(return_value=connection)
    connection.__aexit__ = AsyncMock()
    connect = AsyncMock(return_value=connection)
    monkeypatch.setattr(module.aio_pika, 'connect', connect)
    await module.probe_broker()
    connection.channel.assert_not_called()
    connection.__aexit__.assert_awaited_once()
