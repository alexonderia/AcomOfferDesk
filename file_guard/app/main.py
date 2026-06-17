from __future__ import annotations

import asyncio
import hashlib
import logging

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

from .config import settings
from .scanner import FileScanner, ScanUnavailableError
from .schemas import ScanResponse


def _configure_application_logging() -> None:
    app_logger = logging.getLogger("app")
    uvicorn_error_logger = logging.getLogger("uvicorn.error")

    if uvicorn_error_logger.handlers:
        app_logger.handlers = uvicorn_error_logger.handlers
        app_logger.setLevel(uvicorn_error_logger.level or logging.INFO)
        app_logger.propagate = False
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


_configure_application_logging()

app = FastAPI(title="file_guard", version="0.1.0")
_scanner = FileScanner()
logger = logging.getLogger(__name__)


@app.get("/health")
async def health() -> JSONResponse:
    if settings.require_antivirus and not settings.antivirus_enabled:
        logger.error(
            "Проверка здоровья file_guard: антивирус обязателен (FILE_GUARD_REQUIRE_ANTIVIRUS=true), "
            "но отключён (FILE_GUARD_ANTIVIRUS_ENABLED=false)"
        )
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "reason_code": "file_scan_unavailable"},
        )
    if settings.antivirus_enabled and not _scanner.is_ready():
        logger.warning("Проверка здоровья file_guard: сервис запущен, но антивирус пока не готов")
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "reason_code": "file_scan_unavailable"},
        )
    logger.info(
        "Проверка здоровья file_guard: сервис готов к работе, antivirus=%s",
        ("disabled" if not settings.antivirus_enabled else "ready"),
    )
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "antivirus": ("disabled" if not settings.antivirus_enabled else "ready"),
        },
    )


async def _read_upload_bytes(file: UploadFile) -> tuple[bytes, bool]:
    content = bytearray()
    chunk_size = settings.upload_read_chunk_bytes
    while chunk := await file.read(chunk_size):
        content.extend(chunk)
        if len(content) > settings.max_file_size_bytes:
            return bytes(content), True
    return bytes(content), False


@app.post("/scan", response_model=ScanResponse)
async def scan(file: UploadFile = File(...)) -> ScanResponse | JSONResponse:
    logger.info(
        "Принят запрос на проверку файла: filename=%s content_type=%s",
        file.filename or "",
        file.content_type or "application/octet-stream",
    )
    if settings.require_antivirus and not settings.antivirus_enabled:
        logger.error(
            "Отклоняем проверку: антивирус обязателен, но отключён настройкой FILE_GUARD_ANTIVIRUS_ENABLED=false"
        )
        return JSONResponse(
            status_code=503,
            content={
                "detail": "File scan is temporarily unavailable",
                "reason_code": "file_scan_unavailable",
            },
        )
    content_bytes, exceeded_limit = await _read_upload_bytes(file)
    if exceeded_limit:
        logger.warning(
            "Файл превысил лимит размера при потоковом чтении: filename=%s size_bytes=%s",
            file.filename or "",
            len(content_bytes),
        )
        return ScanResponse(
            allowed=False,
            reason_code="file_too_large",
            message="File exceeds maximum size",
            detected_mime="application/octet-stream",
            size_bytes=len(content_bytes),
            sha256=hashlib.sha256(content_bytes).hexdigest(),
        )
    try:
        # scan_bytes is blocking (libmagic, zip parsing, ClamAV socket). Run it off the
        # event loop and enforce a hard deadline so a slow/malicious input cannot tie up
        # the worker indefinitely. Timeout is treated as fail-closed (503).
        verdict = await asyncio.wait_for(
            asyncio.to_thread(
                _scanner.scan_bytes,
                original_name=file.filename or "",
                content_bytes=content_bytes,
            ),
            timeout=settings.scan_timeout_seconds,
        )
    except asyncio.TimeoutError:
        logger.error(
            "Превышен таймаут проверки файла: filename=%s timeout_seconds=%s",
            file.filename or "",
            settings.scan_timeout_seconds,
        )
        return JSONResponse(
            status_code=503,
            content={
                "detail": "File scan is temporarily unavailable",
                "reason_code": "file_scan_unavailable",
            },
        )
    except ScanUnavailableError:
        logger.exception(
            "Обязательная зависимость проверки файла недоступна: filename=%s",
            file.filename or "",
        )
        return JSONResponse(
            status_code=503,
            content={
                "detail": "File scan is temporarily unavailable",
                "reason_code": "file_scan_unavailable",
            },
        )
    logger.info(
        "Возвращаем итог проверки файла: filename=%s allowed=%s reason_code=%s",
        file.filename or "",
        verdict.allowed,
        verdict.reason_code,
    )
    return ScanResponse(
        allowed=verdict.allowed,
        reason_code=verdict.reason_code,
        message=verdict.message,
        detected_mime=verdict.detected_mime,
        size_bytes=verdict.size_bytes,
        sha256=verdict.sha256,
    )
