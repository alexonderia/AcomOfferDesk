from __future__ import annotations

import uuid

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.request_id import REQUEST_ID_HEADER, RequestIdMiddleware, get_request_id
from app.infrastructure.iam_client import IamClient


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)

    @app.get("/request-id")
    async def request_id():
        return {"request_id": get_request_id()}

    return app


def test_preserves_valid_incoming_request_id() -> None:
    response = TestClient(_app()).get(
        "/request-id",
        headers={REQUEST_ID_HEADER: "gateway-123"},
    )

    assert response.json() == {"request_id": "gateway-123"}
    assert response.headers[REQUEST_ID_HEADER] == "gateway-123"


def test_replaces_invalid_request_id_with_uuid() -> None:
    response = TestClient(_app()).get(
        "/request-id",
        headers={REQUEST_ID_HEADER: "contains spaces"},
    )

    generated = response.headers[REQUEST_ID_HEADER]
    assert uuid.UUID(generated)
    assert response.json() == {"request_id": generated}


def test_iam_client_forwards_current_request_id() -> None:
    observed: dict[str, str] = {}

    class FakeHttpClient:
        async def request(self, method, path, *, json, headers):
            _ = method, path, json
            observed.update(headers)
            return httpx.Response(
                200,
                json={},
                request=httpx.Request(method, f"http://iam{path}"),
            )

    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)

    @app.get("/call-iam")
    async def call_iam():
        await IamClient(client=FakeHttpClient())._request("GET", "/internal/rbac")
        return {"status": "ok"}

    response = TestClient(app).get(
        "/call-iam",
        headers={REQUEST_ID_HEADER: "gateway-iam-456"},
    )

    assert response.status_code == 200
    assert observed[REQUEST_ID_HEADER] == "gateway-iam-456"
