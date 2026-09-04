from __future__ import annotations

import logging
import uuid

from fastapi.testclient import TestClient

from iam_app.core.request_id import REQUEST_ID_HEADER
from iam_app.main import app


def test_iam_preserves_request_id_in_response() -> None:
    response = TestClient(app).get(
        "/health/live",
        headers={REQUEST_ID_HEADER: "backend-123"},
    )

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] == "backend-123"


def test_iam_generates_request_id_when_incoming_value_is_invalid() -> None:
    response = TestClient(app).get(
        "/health/live",
        headers={REQUEST_ID_HEADER: "invalid request id"},
    )

    assert uuid.UUID(response.headers[REQUEST_ID_HEADER])


def test_invalid_internal_auth_log_contains_request_id_but_not_secret(caplog) -> None:
    caplog.set_level(logging.WARNING)
    response = TestClient(app).get(
        "/internal/rbac",
        headers={
            REQUEST_ID_HEADER: "backend-security-456",
            "X-Acom-Service-Token": "bad-secret-value",
        },
    )

    assert response.status_code == 403
    assert "internal_service_auth.failed" in caplog.text
    assert "backend-security-456" in caplog.text
    assert "bad-secret-value" not in caplog.text
