"""Integration/API-contract tests for auth enforcement paths."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api import dependencies as api_dependencies
from app.api.dependencies import get_current_user, get_uow
from app.api.v1 import auth as auth_api
from app.api.v1 import requests as requests_api
from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.exceptions import Unauthorized
from app.domain.permissions import PermissionCodes


class _NoopUow:
    async def __aenter__(self) -> "_NoopUow":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)


class _FileDownloadUow(_NoopUow):
    def __init__(self) -> None:
        self.files = _FilesRepo()
        self.requests = _RequestsRepo()
        self.offers = _OffersRepo()


class _EmailVerificationUow(_NoopUow):
    def __init__(self) -> None:
        self.profiles = object()


class _FilesRepo:
    async def get_by_id(self, file_id: int):
        return SimpleNamespace(
            id=file_id,
            id_storage_object="obj-1",
            original_name="file.pdf",
            mime_type="application/pdf",
        )


class _RequestsRepo:
    async def is_file_linked_to_visible_open_request(self, *, contractor_user_id: str, file_id: int) -> bool:
        _ = (contractor_user_id, file_id)
        return False


class _OffersRepo:
    async def is_file_linked_to_contractor(self, *, contractor_user_id: str, file_id: int) -> bool:
        _ = (contractor_user_id, file_id)
        return False

    async def is_message_file_linked_to_contractor(self, *, contractor_user_id: str, file_id: int) -> bool:
        _ = (contractor_user_id, file_id)
        return False


def _build_guard_app() -> FastAPI:
    app = FastAPI()

    @app.exception_handler(Unauthorized)
    async def unauthorized_handler(request, exc):
        _ = request
        return JSONResponse(status_code=401, content={"detail": str(exc) or "Unauthorized"})

    async def _uow_override():
        return _NoopUow()

    app.dependency_overrides[get_uow] = _uow_override

    @app.get("/guarded")
    async def _guarded(current_user: CurrentUser = Depends(get_current_user)) -> dict[str, str]:
        return {"user_id": current_user.user_id}

    return app


def test_endpoint_without_authorization_returns_401():
    app = _build_guard_app()
    with TestClient(app) as client:
        response = client.get("/guarded")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing credentials"


def test_endpoint_with_invalid_bearer_token_returns_401(monkeypatch):
    app = _build_guard_app()

    async def _raise_unauthorized(token: str, *, uow):
        _ = (token, uow)
        raise Unauthorized("Invalid token")

    monkeypatch.setattr(api_dependencies, "_get_current_user_from_keycloak_token", _raise_unauthorized)

    with TestClient(app) as client:
        response = client.get("/guarded", headers={"Authorization": "Bearer broken-token"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_active_user_with_required_permission_gets_success_on_protected_endpoint(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    user = make_current_user(
        role_id=settings.lead_economist_role_id,
        status="active",
        permissions={PermissionCodes.FILES_DOWNLOAD, PermissionCodes.REQUESTS_READ},
    )
    set_current_user(user)
    set_uow(_FileDownloadUow())

    async def _fake_read_bytes(self, *, db_file):
        _ = (self, db_file)
        return b"fake-pdf"

    monkeypatch.setattr(requests_api.FileService, "read_bytes", _fake_read_bytes)

    response = test_client.get("/api/v1/files/1/download")

    assert response.status_code == 200
    assert response.content == b"fake-pdf"


@pytest.mark.parametrize("status", ["review", "inactive", "blacklist"])
def test_review_inactive_blacklist_are_blocked_for_protected_endpoint(
    test_client,
    set_current_user,
    make_current_user,
    status,
):
    user = make_current_user(
        role_id=settings.contractor_role_id,
        status=status,
        permissions={PermissionCodes.FILES_DOWNLOAD, PermissionCodes.REQUESTS_READ},
    )
    set_current_user(user)

    response = test_client.get("/api/v1/files/1/download")

    assert response.status_code == 403


def test_request_email_verification_allows_review_contractor_only_for_limited_action(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    review_contractor = make_current_user(
        role_id=settings.contractor_role_id,
        status="review",
        permissions={PermissionCodes.PROFILE_MANAGE_OWN},
    )
    set_current_user(review_contractor)
    set_uow(_EmailVerificationUow())

    async def _fake_request_profile_verification(self, *, user_id: str, email: str):
        _ = (self, user_id, email)
        return "sent"

    monkeypatch.setattr(auth_api.EmailVerificationService, "request_profile_verification", _fake_request_profile_verification)

    response = test_client.post(
        "/api/v1/auth/request-email-verification",
        json={"email": "contractor@example.com"},
    )

    assert response.status_code == 200


def test_request_email_verification_blocks_inactive_user(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    inactive_user = make_current_user(
        role_id=settings.contractor_role_id,
        status="inactive",
        permissions={PermissionCodes.PROFILE_MANAGE_OWN},
    )
    set_current_user(inactive_user)
    set_uow(_EmailVerificationUow())

    async def _fake_request_profile_verification(self, *, user_id: str, email: str):
        _ = (self, user_id, email)
        return "sent"

    monkeypatch.setattr(auth_api.EmailVerificationService, "request_profile_verification", _fake_request_profile_verification)

    response = test_client.post(
        "/api/v1/auth/request-email-verification",
        json={"email": "inactive@example.com"},
    )

    assert response.status_code == 403
