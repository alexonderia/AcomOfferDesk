from __future__ import annotations

from fastapi.testclient import TestClient

from iam_app import main
from iam_app.core.config import settings


def test_live_does_not_require_database(monkeypatch) -> None:
    def forbidden_session():
        raise AssertionError("liveness must not open a database session")

    monkeypatch.setattr(main, "SessionLocal", forbidden_session)
    response = TestClient(main.app).get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_reports_ok_when_database_and_signing_are_available() -> None:
    response = TestClient(main.app).get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_is_not_ok_when_database_is_unavailable(monkeypatch) -> None:
    class UnavailableSession:
        async def __aenter__(self):
            raise OSError("database unavailable")

        async def __aexit__(self, *_args):
            return None

    monkeypatch.setattr(main, "SessionLocal", UnavailableSession)
    response = TestClient(main.app).get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}


def test_ready_is_not_ok_when_active_signing_key_is_invalid(monkeypatch) -> None:
    monkeypatch.setattr(settings, "signing_private_key", "invalid")
    response = TestClient(main.app).get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}


def test_compatibility_health_keeps_readiness_semantics() -> None:
    response = TestClient(main.app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
