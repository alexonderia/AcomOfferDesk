from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime

import aio_pika
import httpx
import urllib3
from minio import Minio
from sqlalchemy import text

from app.core.config import settings
from app.infrastructure.db import engine
from app.schemas.system_status import RuntimeSettingsSchema, ServiceStatusSchema, SystemStatusData


logger = logging.getLogger(__name__)
CACHE_TTL_SECONDS = 15
PROBE_TIMEOUT_SECONDS = 3.0
STARTED_AT = time.monotonic()


@dataclass(frozen=True)
class ProbeResult:
    detail: str
    degraded: bool = False


async def probe_database() -> ProbeResult:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    return ProbeResult("Подключение и запрос к базе выполнены")


async def probe_iam() -> ProbeResult:
    async with httpx.AsyncClient(timeout=2.0, follow_redirects=False, trust_env=False) as client:
        response = await client.get(f"{settings.iam_internal_base_url.rstrip('/')}/health/ready")
        response.raise_for_status()
        if response.json().get("status") != "ok":
            raise ValueError("IAM not ready")
    return ProbeResult("Авторизация и база IAM готовы к работе")


def _probe_storage_sync() -> ProbeResult:
    pool = urllib3.PoolManager(timeout=urllib3.Timeout(connect=1.0, read=1.0), retries=False)
    try:
        client = Minio(
            settings.s3_endpoint, access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key, secure=settings.s3_secure, http_client=pool,
        )
        if not client.bucket_exists(settings.s3_bucket):
            raise ValueError("Storage bucket unavailable")
    finally:
        pool.clear()
    return ProbeResult("Хранилище доступно, доступ к бакету подтверждён")


async def probe_storage() -> ProbeResult:
    return await asyncio.to_thread(_probe_storage_sync)


async def probe_broker() -> ProbeResult:
    async with await aio_pika.connect(settings.rabbitmq_url, timeout=2.0):
        pass
    return ProbeResult("Подключение к брокеру с учётными данными выполнено")


async def probe_file_guard() -> ProbeResult:
    async with httpx.AsyncClient(timeout=2.0, follow_redirects=False, trust_env=False) as client:
        response = await client.get(f"{settings.file_guard_url.rstrip('/')}/health")
        response.raise_for_status()
        data = response.json()
        if data.get("status") != "ok":
            raise ValueError("File guard not ready")
    if data.get("antivirus") != "ready":
        return ProbeResult("Сервис отвечает; антивирусная проверка не включена или не подтверждена", degraded=True)
    return ProbeResult("Сервис и антивирус готовы к проверке файлов")


class SystemStatusService:
    """Read-only probes, bounded waits and a per-process cache shared by admin requests."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._cached: SystemStatusData | None = None
        self._expires_at = 0.0

    async def _measure(
        self, key: str, name: str, probe: Callable[[], Awaitable[ProbeResult]], *, enabled: bool = True,
    ) -> ServiceStatusSchema:
        if not enabled:
            return ServiceStatusSchema(
                key=key, name=name, status="disabled", response_ms=None,
                detail="Отключён настройкой приложения; проверка не выполнялась",
            )
        started = time.monotonic()
        try:
            async with asyncio.timeout(PROBE_TIMEOUT_SECONDS):
                result = await probe()
            detail = result.detail
            status = "degraded" if result.degraded else "up"
        except Exception as exc:
            logger.warning("system_status_probe_failed service=%s error_type=%s", key, type(exc).__name__)
            status = "down"
            detail = "Проверка не завершилась за отведённое время" if isinstance(exc, TimeoutError) else "Проверка доступности не пройдена"
        return ServiceStatusSchema(
            key=key, name=name, status=status,
            response_ms=round((time.monotonic() - started) * 1000, 1), detail=detail,
        )

    async def get_status(self) -> SystemStatusData:
        async with self._lock:
            if self._cached is not None and time.monotonic() < self._expires_at:
                return self._cached
            services = await asyncio.gather(
                self._measure("database", "База данных", probe_database),
                self._measure("iam", "Авторизация (IAM)", probe_iam),
                self._measure("storage", "Хранилище файлов", probe_storage),
                self._measure("broker", "Брокер сообщений", probe_broker),
                self._measure("file_guard", "Проверка файлов", probe_file_guard, enabled=settings.file_guard_enabled),
            )
            services.insert(0, ServiceStatusSchema(
                key="backend", name="Приложение (API)", status="up", response_ms=None,
                detail="Обрабатывает текущий запрос панели",
            ))
            self._cached = SystemStatusData(
                checked_at=datetime.now(UTC),
                overall="degraded" if any(s.status in {"down", "degraded"} for s in services) else "healthy",
                uptime_seconds=int(time.monotonic() - STARTED_AT),
                cache_ttl_seconds=CACHE_TTL_SECONDS, probe_timeout_seconds=PROBE_TIMEOUT_SECONDS,
                settings=RuntimeSettingsSchema(
                    environment=settings.app_env, email_enabled=settings.email_enabled,
                    smtp_configured=bool(settings.smtp_host and settings.email_address and settings.email_app_password),
                    imap_configured=bool(settings.imap_host and settings.imap_username and settings.imap_password),
                    file_guard_enabled=settings.file_guard_enabled,
                    secure_cookies=settings.refresh_cookie_secure,
                    cookie_samesite=settings.refresh_cookie_samesite,
                    signed_file_link_ttl_seconds=settings.s3_presigned_get_ttl_seconds,
                    websocket_ticket_ttl_seconds=settings.ws_ticket_ttl_seconds,
                ),
                services=services,
            )
            self._expires_at = time.monotonic() + CACHE_TTL_SECONDS
            return self._cached
