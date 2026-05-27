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

_GENERIC_PUBLIC_ERROR = "РџСЂРѕРёР·РѕС€Р»Р° РѕС€РёР±РєР°. РџРѕРїСЂРѕР±СѓР№С‚Рµ РїРѕРІС‚РѕСЂРёС‚СЊ РґРµР№СЃС‚РІРёРµ."
_DEFAULT_PUBLIC_ERROR_BY_STATUS = {
    401: "РЎРµСЃСЃРёСЏ РёСЃС‚РµРєР»Р°. Р’РѕР№РґРёС‚Рµ РІ СЃРёСЃС‚РµРјСѓ Р·Р°РЅРѕРІРѕ.",
    403: "РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ РґРµР№СЃС‚РІРёСЏ.",
    404: "Р”Р°РЅРЅС‹Рµ РЅРµ РЅР°Р№РґРµРЅС‹ РёР»Рё Р±С‹Р»Рё СѓРґР°Р»РµРЅС‹.",
    409: "РљРѕРЅС„Р»РёРєС‚ РґР°РЅРЅС‹С…. РћР±РЅРѕРІРёС‚Рµ СЃС‚СЂР°РЅРёС†Сѓ Рё РїРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°.",
}
_DIRECT_PUBLIC_DETAIL_TRANSLATIONS = {
    "Missing credentials": "РќРµРѕР±С…РѕРґРёРјРѕ РІРѕР№С‚Рё РІ СЃРёСЃС‚РµРјСѓ.",
    "Invalid credentials": "РќРµРІРµСЂРЅС‹Р№ Р»РѕРіРёРЅ РёР»Рё РїР°СЂРѕР»СЊ.",
    "Invalid token": "РЎРµСЃСЃРёСЏ РёСЃС‚РµРєР»Р°. Р’РѕР№РґРёС‚Рµ РІ СЃРёСЃС‚РµРјСѓ Р·Р°РЅРѕРІРѕ.",
    "Token expired": "РЎРµСЃСЃРёСЏ РёСЃС‚РµРєР»Р°. Р’РѕР№РґРёС‚Рµ РІ СЃРёСЃС‚РµРјСѓ Р·Р°РЅРѕРІРѕ.",
    "Invalid token payload": "РЎРµСЃСЃРёСЏ РёСЃС‚РµРєР»Р°. Р’РѕР№РґРёС‚Рµ РІ СЃРёСЃС‚РµРјСѓ Р·Р°РЅРѕРІРѕ.",
    "Invalid refresh": "РЎРµСЃСЃРёСЏ РёСЃС‚РµРєР»Р°. Р’РѕР№РґРёС‚Рµ РІ СЃРёСЃС‚РµРјСѓ Р·Р°РЅРѕРІРѕ.",
    "Stale refresh token": "РЎРµСЃСЃРёСЏ РёСЃС‚РµРєР»Р°. Р’РѕР№РґРёС‚Рµ РІ СЃРёСЃС‚РµРјСѓ Р·Р°РЅРѕРІРѕ.",
    "Broken bearer": "РЎРµСЃСЃРёСЏ РёСЃС‚РµРєР»Р°. Р’РѕР№РґРёС‚Рµ РІ СЃРёСЃС‚РµРјСѓ Р·Р°РЅРѕРІРѕ.",
    "Authentication required": "РќРµРѕР±С…РѕРґРёРјРѕ РІРѕР№С‚Рё РІ СЃРёСЃС‚РµРјСѓ.",
    "Unauthorized": "РЎРµСЃСЃРёСЏ РёСЃС‚РµРєР»Р°. Р’РѕР№РґРёС‚Рµ РІ СЃРёСЃС‚РµРјСѓ Р·Р°РЅРѕРІРѕ.",
    "Forbidden": "РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ РґРµР№СЃС‚РІРёСЏ.",
    "Not found": "Р”Р°РЅРЅС‹Рµ РЅРµ РЅР°Р№РґРµРЅС‹ РёР»Рё Р±С‹Р»Рё СѓРґР°Р»РµРЅС‹.",
    "Request not found": "Р—Р°СЏРІРєР° РЅРµ РЅР°Р№РґРµРЅР°.",
    "Offer not found": "РљРѕРјРјРµСЂС‡РµСЃРєРѕРµ РїСЂРµРґР»РѕР¶РµРЅРёРµ РЅРµ РЅР°Р№РґРµРЅРѕ.",
    "Notification not found": "РЈРІРµРґРѕРјР»РµРЅРёРµ РЅРµ РЅР°Р№РґРµРЅРѕ.",
    "Message not found": "РЎРѕРѕР±С‰РµРЅРёРµ РЅРµ РЅР°Р№РґРµРЅРѕ.",
    "File not found": "Р¤Р°Р№Р» РЅРµ РЅР°Р№РґРµРЅ.",
    "Insufficient permissions": "РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ РґРµР№СЃС‚РІРёСЏ.",
    "Insufficient permissions to edit request": "РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ Р·Р°СЏРІРєРё: РґРѕСЃС‚СѓРї РѕРіСЂР°РЅРёС‡РµРЅ РёРµСЂР°СЂС…РёРµР№/РїРѕРґСЂР°Р·РґРµР»РµРЅРёРµРј.",
    "Insufficient permissions to edit offer": "РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ РёР·РјРµРЅРµРЅРёСЏ РљРџ: С‚СЂРµР±СѓРµС‚СЃСЏ `offers.update` РёР»Рё `delegation.department.offers.update` РІ РґРѕРїСѓСЃС‚РёРјРѕРј СЃРєРѕСѓРїРµ.",
    "Insufficient permissions to update offer amount": "РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ РёР·РјРµРЅРµРЅРёСЏ СЃСѓРјРјС‹ РљРџ: С‚СЂРµР±СѓРµС‚СЃСЏ РїСЂР°РІРѕ РёР·РјРµРЅРµРЅРёСЏ СЃСѓРјРјС‹ РІ РґРѕРїСѓСЃС‚РёРјРѕРј РєРѕРЅС‚СѓСЂРµ.",
    "Insufficient permissions to upload offer files": "РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ Р·Р°РіСЂСѓР·РєРё С„Р°Р№Р»РѕРІ РљРџ: С‚СЂРµР±СѓРµС‚СЃСЏ РїСЂР°РІРѕ Р·Р°РіСЂСѓР·РєРё С„Р°Р№Р»РѕРІ РІ РґРѕРїСѓСЃС‚РёРјРѕРј РєРѕРЅС‚СѓСЂРµ.",
    "Insufficient permissions to delete offer files": "РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ СѓРґР°Р»РµРЅРёСЏ С„Р°Р№Р»РѕРІ РљРџ: С‚СЂРµР±СѓРµС‚СЃСЏ РїСЂР°РІРѕ СѓРґР°Р»РµРЅРёСЏ С„Р°Р№Р»РѕРІ РІ РґРѕРїСѓСЃС‚РёРјРѕРј РєРѕРЅС‚СѓСЂРµ.",
    "Insufficient permissions to update request status": "РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ РёР·РјРµРЅРµРЅРёСЏ СЃС‚Р°С‚СѓСЃР° Р·Р°СЏРІРєРё: С‚СЂРµР±СѓРµС‚СЃСЏ `requests.status.update` РёР»Рё `delegation.department.requests.status_update` РІ РґРѕРїСѓСЃС‚РёРјРѕРј СЃРєРѕСѓРїРµ.",
    "Offer status cannot be changed for closed request": "КП нельзя изменить, если заявка уже закрыта или отклонена",
    "КП нельзя изменить, если заявка уже закрыта или отклонена": "КП нельзя изменить, если заявка уже закрыта или отклонена",
    "Insufficient permissions to update request amounts": "РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ РёР·РјРµРЅРµРЅРёСЏ СЃСѓРјРј Р·Р°СЏРІРєРё: С‚СЂРµР±СѓРµС‚СЃСЏ РїСЂР°РІРѕ РЅР° СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёРµ С†РµРЅ РІ РґРѕРїСѓСЃС‚РёРјРѕРј РєРѕРЅС‚СѓСЂРµ.",
    "Insufficient permissions to update request deadline": "РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ РёР·РјРµРЅРµРЅРёСЏ РґРµРґР»Р°Р№РЅР° Р·Р°СЏРІРєРё: С‚СЂРµР±СѓРµС‚СЃСЏ РїСЂР°РІРѕ СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ РґРµРґР»Р°Р№РЅР° РІ РґРѕРїСѓСЃС‚РёРјРѕРј РєРѕРЅС‚СѓСЂРµ.",
    "Insufficient permissions to upload request files": "РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ Р·Р°РіСЂСѓР·РєРё С„Р°Р№Р»РѕРІ РІ Р·Р°СЏРІРєСѓ: С‚СЂРµР±СѓРµС‚СЃСЏ РїСЂР°РІРѕ Р·Р°РіСЂСѓР·РєРё С„Р°Р№Р»РѕРІ Рё РґРѕСЃС‚СѓРї Рє Р·Р°СЏРІРєРµ.",
    "Insufficient permissions to delete request files": "РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ СѓРґР°Р»РµРЅРёСЏ С„Р°Р№Р»РѕРІ Р·Р°СЏРІРєРё: С‚СЂРµР±СѓРµС‚СЃСЏ РїСЂР°РІРѕ СѓРґР°Р»РµРЅРёСЏ С„Р°Р№Р»РѕРІ Рё РґРѕСЃС‚СѓРї Рє Р·Р°СЏРІРєРµ.",
    "Insufficient permissions to send request email notifications": "РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ РѕС‚РїСЂР°РІРєРё РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹С… СѓРІРµРґРѕРјР»РµРЅРёР№ РїРѕ Р·Р°СЏРІРєРµ.",
    "Operator can update status only for own requests": "РР·РјРµРЅРµРЅРёРµ СЃС‚Р°С‚СѓСЃР° РѕРїРµСЂР°С‚РѕСЂРѕРј РґРѕСЃС‚СѓРїРЅРѕ С‚РѕР»СЊРєРѕ РґР»СЏ СЃРѕР±СЃС‚РІРµРЅРЅС‹С… Р·Р°СЏРІРѕРє.",
    "Request is outside your management scope": "Р”РµР№СЃС‚РІРёРµ РЅРµРґРѕСЃС‚СѓРїРЅРѕ: Р·Р°СЏРІРєР° РІРЅРµ РІР°С€РµРіРѕ РєРѕРЅС‚СѓСЂР° СѓРїСЂР°РІР»РµРЅРёСЏ.",
    "Insufficient permissions to view chat": "РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ РїСЂРѕСЃРјРѕС‚СЂР° С‡Р°С‚Р°.",
    "Insufficient permissions to send chat message": "РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ РѕС‚РїСЂР°РІРєРё СЃРѕРѕР±С‰РµРЅРёСЏ РІ С‡Р°С‚.",
    "Insufficient permissions to view workspace": "РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ РїСЂРѕСЃРјРѕС‚СЂР° СЂР°Р±РѕС‡РµРіРѕ РїСЂРѕСЃС‚СЂР°РЅСЃС‚РІР°.",
    "Password is managed by the identity provider": "РџР°СЂРѕР»СЊ СѓРїСЂР°РІР»СЏРµС‚СЃСЏ РїСЂРѕРІР°Р№РґРµСЂРѕРј Р°СѓС‚РµРЅС‚РёС„РёРєР°С†РёРё.",
    "Keycloak authentication is disabled": "Р’С…РѕРґ РІСЂРµРјРµРЅРЅРѕ РЅРµРґРѕСЃС‚СѓРїРµРЅ.",
    "Keycloak email is already used by another account": "РџРѕС‡С‚Р° СѓР¶Рµ РёСЃРїРѕР»СЊР·СѓРµС‚СЃСЏ РґСЂСѓРіРёРј Р°РєРєР°СѓРЅС‚РѕРј.",
}
_CONTAINS_PUBLIC_DETAIL_TRANSLATIONS: tuple[tuple[str, str], ...] = (
    ("missing credentials", "РќРµРѕР±С…РѕРґРёРјРѕ РІРѕР№С‚Рё РІ СЃРёСЃС‚РµРјСѓ."),
    ("invalid token", "РЎРµСЃСЃРёСЏ РёСЃС‚РµРєР»Р°. Р’РѕР№РґРёС‚Рµ РІ СЃРёСЃС‚РµРјСѓ Р·Р°РЅРѕРІРѕ."),
    ("token expired", "РЎРµСЃСЃРёСЏ РёСЃС‚РµРєР»Р°. Р’РѕР№РґРёС‚Рµ РІ СЃРёСЃС‚РµРјСѓ Р·Р°РЅРѕРІРѕ."),
    ("unauthorized", "РЎРµСЃСЃРёСЏ РёСЃС‚РµРєР»Р°. Р’РѕР№РґРёС‚Рµ РІ СЃРёСЃС‚РµРјСѓ Р·Р°РЅРѕРІРѕ."),
    ("forbidden", "РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ РґРµР№СЃС‚РІРёСЏ."),
    ("insufficient permissions", "РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ РґРµР№СЃС‚РІРёСЏ."),
    ("not found", "Р”Р°РЅРЅС‹Рµ РЅРµ РЅР°Р№РґРµРЅС‹ РёР»Рё Р±С‹Р»Рё СѓРґР°Р»РµРЅС‹."),
    ("email is already used by another account", "РџРѕС‡С‚Р° СѓР¶Рµ РёСЃРїРѕР»СЊР·СѓРµС‚СЃСЏ РґСЂСѓРіРёРј Р°РєРєР°СѓРЅС‚РѕРј."),
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

    has_cyrillic = bool(re.search(r"[Рђ-РЇР°-СЏРЃС‘]", normalized))
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


