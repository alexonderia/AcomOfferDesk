from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from iam_app.api import render_browser_auth_error, router
from iam_app.core.config import settings
from iam_app.db import SessionLocal
from iam_app.errors import IamError


logger = logging.getLogger(__name__)
_docs_enabled = settings.app_env != "production"

app = FastAPI(
    title="AcomOfferDesk IAM",
    version="1.0.0",
    docs_url="/docs" if _docs_enabled else None,
    redoc_url=None,
    openapi_url="/openapi.json" if _docs_enabled else None,
)
app.include_router(router)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if request.url.path.startswith("/iam/"):
        response.headers.setdefault("Cache-Control", "no-store")
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    async with SessionLocal() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.exception_handler(IamError)
async def iam_error_handler(request: Request, exc: IamError) -> JSONResponse:
    if request.url.path.startswith("/iam/"):
        return render_browser_auth_error(
            request=request,
            error=exc.public_detail,
            status_code=exc.status_code,
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.public_detail},
        headers={"Cache-Control": "no-store"},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "unhandled_iam_exception path=%s method=%s exception_type=%s",
        request.url.path,
        request.method,
        type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Сервис авторизации временно недоступен"},
        headers={"Cache-Control": "no-store"},
    )
