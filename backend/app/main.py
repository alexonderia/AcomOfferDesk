from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
import fcntl
import re

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1 import router as v1_router
from app.domain.exceptions import Conflict, Forbidden, NotFound, Unauthorized
from app.infrastructure.db import engine
from app.infrastructure.email_delivery_consumer import EmailDeliveryConsumerRuntime
from app.infrastructure.process_notification_consumer import ProcessNotificationConsumerRuntime
from app.realtime.runtime import (
    ChatRealtimeRuntime,
    UnifiedRealtimeRuntime,
    set_chat_runtime,
    set_unified_realtime_runtime,
)
from app.services.files import FileService

logger = logging.getLogger(__name__)

_GENERIC_PUBLIC_ERROR = "Произошла ошибка. Попробуйте повторить действие."
_DEFAULT_PUBLIC_ERROR_BY_STATUS = {
    401: "Сессия истекла. Войдите в систему заново.",
    403: "Недостаточно прав для выполнения действия.",
    404: "Данные не найдены или были удалены.",
    409: "Конфликт данных. Обновите страницу и попробуйте снова.",
}
_DIRECT_PUBLIC_DETAIL_TRANSLATIONS = {
    "Missing credentials": "Необходимо войти в систему.",
    "Invalid credentials": "Неверный логин или пароль.",
    "Invalid token": "Сессия истекла. Войдите в систему заново.",
    "Token expired": "Сессия истекла. Войдите в систему заново.",
    "Invalid token payload": "Сессия истекла. Войдите в систему заново.",
    "Invalid refresh": "Сессия истекла. Войдите в систему заново.",
    "Stale refresh token": "Сессия истекла. Войдите в систему заново.",
    "Broken bearer": "Сессия истекла. Войдите в систему заново.",
    "Authentication required": "Необходимо войти в систему.",
    "Unauthorized": "Сессия истекла. Войдите в систему заново.",
    "Forbidden": "Недостаточно прав для выполнения действия.",
    "Not found": "Данные не найдены или были удалены.",
    "Request not found": "Заявка не найдена.",
    "Offer not found": "Коммерческое предложение не найдено.",
    "Notification not found": "Уведомление не найдено.",
    "Message not found": "Сообщение не найдено.",
    "File not found": "Файл не найден.",
    "Insufficient permissions": "Недостаточно прав для выполнения действия.",
    "Insufficient permissions to view chat": "Недостаточно прав для просмотра чата.",
    "Insufficient permissions to send chat message": "Недостаточно прав для отправки сообщения в чат.",
    "Insufficient permissions to view workspace": "Недостаточно прав для просмотра рабочего пространства.",
    "Password is managed by the identity provider": "Пароль управляется провайдером аутентификации.",
    "Keycloak authentication is disabled": "Вход временно недоступен.",
    "Keycloak email is already used by another account": "Почта уже используется другим аккаунтом.",
}
_CONTAINS_PUBLIC_DETAIL_TRANSLATIONS: tuple[tuple[str, str], ...] = (
    ("missing credentials", "Необходимо войти в систему."),
    ("invalid token", "Сессия истекла. Войдите в систему заново."),
    ("token expired", "Сессия истекла. Войдите в систему заново."),
    ("unauthorized", "Сессия истекла. Войдите в систему заново."),
    ("forbidden", "Недостаточно прав для выполнения действия."),
    ("insufficient permissions", "Недостаточно прав для выполнения действия."),
    ("not found", "Данные не найдены или были удалены."),
    ("email is already used by another account", "Почта уже используется другим аккаунтом."),
)
_TECHNICAL_DETAIL_PATTERN = re.compile(
    r"traceback|stack\s*trace|sql|rabbitmq|smtp|psycopg|exception|validationerror|internal server error",
    re.IGNORECASE,
)


def _normalize_public_error_detail(*, status_code: int, detail: str | None) -> str:
    default_message = _DEFAULT_PUBLIC_ERROR_BY_STATUS.get(status_code, _GENERIC_PUBLIC_ERROR)
    normalized = (detail or "").strip()
    if not normalized:
        return default_message

    direct_match = _DIRECT_PUBLIC_DETAIL_TRANSLATIONS.get(normalized)
    if direct_match is not None:
        return direct_match

    lowered = normalized.lower()
    for fragment, translated in _CONTAINS_PUBLIC_DETAIL_TRANSLATIONS:
        if fragment in lowered:
            return translated

    if _TECHNICAL_DETAIL_PATTERN.search(normalized):
        return default_message

    has_cyrillic = bool(re.search(r"[А-Яа-яЁё]", normalized))
    has_latin = bool(re.search(r"[A-Za-z]", normalized))
    if has_cyrillic:
        return normalized
    if has_latin:
        return default_message
    return normalized

class _PollingLeaderLock:
    def __init__(self, lock_path: Path) -> None:
        self._lock_path = lock_path
        self._fd = None

    def try_acquire(self) -> bool:
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        fd = self._lock_path.open("a+")
        try:
            fcntl.flock(fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            fd.close()
            return False
        self._fd = fd
        return True

    def release(self) -> None:
        if self._fd is None:
            return
        try:
            fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        finally:
            self._fd.close()
            self._fd = None

async def _request_reply_polling_worker(stop_event: asyncio.Event) -> None:
    try:
        from app.services.process_request_reply_use_case import ProcessRequestReplyUseCase
    except ModuleNotFoundError as exc:
        logger.warning("Request reply background task disabled: module is unavailable: %s", exc)
        return

    try:
        use_case = ProcessRequestReplyUseCase.from_settings()
    except ValueError as exc:
        logger.warning("Request reply background task disabled: %s", exc)
        return

    poll_interval = max(5, settings.request_mailbox_poll_interval_seconds)
    while not stop_event.is_set():
        try:
            await use_case.execute()
        except Exception:
            logger.exception("Request reply background processing failed")

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=poll_interval)
        except TimeoutError:
            continue


@asynccontextmanager
async def lifespan(_: FastAPI):
    stop_event = asyncio.Event()
    leader_lock = _PollingLeaderLock(Path('/tmp/acom_offerdesk_reply_polling.lock'))
    is_leader = leader_lock.try_acquire()
    await FileService().ensure_bucket_exists()
    realtime_runtime = ChatRealtimeRuntime()
    unified_realtime_runtime = UnifiedRealtimeRuntime(manager=realtime_runtime.manager)
    set_chat_runtime(realtime_runtime)
    set_unified_realtime_runtime(unified_realtime_runtime)
    await realtime_runtime.start()
    email_delivery_runtime = EmailDeliveryConsumerRuntime()
    process_notification_runtime = ProcessNotificationConsumerRuntime()
    try:
        await email_delivery_runtime.start()
    except Exception:
        logger.exception("Email delivery consumer failed to start; backend will continue without it")
    try:
        await process_notification_runtime.start()
    except Exception:
        logger.exception("Process notification consumer failed to start; backend will continue without it")

    task: asyncio.Task[None] | None = None
    if is_leader:
        task = asyncio.create_task(_request_reply_polling_worker(stop_event))
    else:
        logger.info('Request reply background task skipped in current worker: leader lock is held by another worker')
    try:
        yield
    finally:
        stop_event.set()
        if task is not None:
            await task
        await email_delivery_runtime.stop()
        await process_notification_runtime.stop()
        await realtime_runtime.stop()
        if is_leader:
            leader_lock.release()


app = FastAPI(title="Order Backend", version="0.1.0", lifespan=lifespan)

cors_allow_origins = settings.resolved_cors_allow_origins
if cors_allow_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
app.include_router(v1_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(NotFound)
async def not_found_handler(request: Request, exc: NotFound) -> JSONResponse:
    _ = request
    return JSONResponse(
        status_code=404,
        content={"detail": _normalize_public_error_detail(status_code=404, detail=str(exc))},
    )


@app.exception_handler(Forbidden)
async def forbidden_handler(request: Request, exc: Forbidden) -> JSONResponse:
    _ = request
    return JSONResponse(
        status_code=403,
        content={"detail": _normalize_public_error_detail(status_code=403, detail=str(exc))},
    )


@app.exception_handler(Unauthorized)
async def unauthorized_handler(request: Request, exc: Unauthorized) -> JSONResponse:
    _ = request
    return JSONResponse(
        status_code=401,
        content={"detail": _normalize_public_error_detail(status_code=401, detail=str(exc))},
    )


@app.exception_handler(Conflict)
async def conflict_handler(request: Request, exc: Conflict) -> JSONResponse:
    _ = request
    return JSONResponse(
        status_code=409,
        content={"detail": _normalize_public_error_detail(status_code=409, detail=str(exc))},
    )
