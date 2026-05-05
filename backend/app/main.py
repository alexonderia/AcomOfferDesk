from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
import fcntl

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1 import router as v1_router
from app.domain.exceptions import Conflict, Forbidden, NotFound, Unauthorized
from app.infrastructure.db import engine
from app.realtime.runtime import ChatRealtimeRuntime, set_chat_runtime
from app.services.files import FileService

logger = logging.getLogger(__name__)

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
    set_chat_runtime(realtime_runtime)
    await realtime_runtime.start()

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
    return JSONResponse(status_code=404, content={"detail": str(exc) or "Not found"})


@app.exception_handler(Forbidden)
async def forbidden_handler(request: Request, exc: Forbidden) -> JSONResponse:
    _ = request
    return JSONResponse(status_code=403, content={"detail": str(exc) or "Forbidden"})


@app.exception_handler(Unauthorized)
async def unauthorized_handler(request: Request, exc: Unauthorized) -> JSONResponse:
    _ = request
    return JSONResponse(status_code=401, content={"detail": str(exc) or "Unauthorized"})


@app.exception_handler(Conflict)
async def conflict_handler(request: Request, exc: Conflict) -> JSONResponse:
    _ = request
    return JSONResponse(status_code=409, content={"detail": str(exc) or "Conflict"})
