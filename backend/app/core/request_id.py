from __future__ import annotations

import contextvars
import re
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


REQUEST_ID_HEADER = "X-Request-ID"
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id",
    default=None,
)


def normalize_request_id(value: str | None) -> str:
    candidate = (value or "").strip()
    if _VALID_REQUEST_ID.fullmatch(candidate):
        return candidate
    return str(uuid.uuid4())


def get_request_id() -> str | None:
    return _request_id.get()


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = normalize_request_id(request.headers.get(REQUEST_ID_HEADER))
        token = _request_id.set(request_id)
        request.state.request_id = request_id
        try:
            response = await call_next(request)
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            _request_id.reset(token)
