"""Shared integration test harness.

Builds a minimal FastAPI app with dependency overrides so API contract tests
can run without live infrastructure services.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user, get_uow
from app.api.v1 import router as v1_router
from app.domain.auth_context import CurrentUser
from app.domain.exceptions import Conflict, Forbidden, NotFound, Unauthorized


class DummyUow:
    def __init__(self) -> None:
        self.requests = None
        self.files = None
        self.users = None
        self.offers = None
        self.user_status_periods = None
        self.chats = None
        self.messages = None
        self.profiles = None
        self.company_contacts = None
        self.feedback = None
        self.tg_users = None
        self.user_auth_accounts = None
        self.user_contact_channels = None
        self.notifications = None
        self.economy_plans = None

    async def __aenter__(self) -> "DummyUow":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)


@pytest.fixture
def make_current_user():
    def _make_current_user(
        *,
        user_id: str = "user-1",
        role_id: int = 6,
        status: str = "active",
        permissions: set[str] | frozenset[str] | None = None,
    ) -> CurrentUser:
        normalized_permissions = frozenset(permissions or set())
        return CurrentUser(
            user_id=user_id,
            role_id=role_id,
            status=status,
            permissions=normalized_permissions,
            keycloak_roles=normalized_permissions,
            app_roles=frozenset(),
            delegation_roles=frozenset(),
        )

    return _make_current_user


@pytest.fixture
def api_app() -> FastAPI:
    app = FastAPI()
    app.include_router(v1_router)

    @app.exception_handler(NotFound)
    async def not_found_handler(request, exc):
        _ = request
        return JSONResponse(status_code=404, content={"detail": str(exc) or "Not found"})

    @app.exception_handler(Forbidden)
    async def forbidden_handler(request, exc):
        _ = request
        return JSONResponse(status_code=403, content={"detail": str(exc) or "Forbidden"})

    @app.exception_handler(Unauthorized)
    async def unauthorized_handler(request, exc):
        _ = request
        return JSONResponse(status_code=401, content={"detail": str(exc) or "Unauthorized"})

    @app.exception_handler(Conflict)
    async def conflict_handler(request, exc):
        _ = request
        return JSONResponse(status_code=409, content={"detail": str(exc) or "Conflict"})

    async def _default_current_user() -> CurrentUser:
        raise RuntimeError("Test should override current user dependency")

    async def _default_uow() -> DummyUow:
        return DummyUow()

    app.dependency_overrides[get_current_user] = _default_current_user
    app.dependency_overrides[get_uow] = _default_uow
    return app


@pytest.fixture
def test_client(api_app: FastAPI) -> AsyncIterator[TestClient]:
    with TestClient(api_app) as client:
        yield client


@pytest.fixture
def set_current_user(api_app: FastAPI):
    def _set_current_user(user: CurrentUser) -> None:
        async def _override() -> CurrentUser:
            return user

        api_app.dependency_overrides[get_current_user] = _override

    return _set_current_user


@pytest.fixture
def set_uow(api_app: FastAPI):
    def _set_uow(uow_obj: DummyUow) -> None:
        async def _override() -> DummyUow:
            return uow_obj

        api_app.dependency_overrides[get_uow] = _override

    return _set_uow
