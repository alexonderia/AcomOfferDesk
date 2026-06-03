"""Integration/API-contract tests for auth enforcement paths."""

from __future__ import annotations

import asyncio
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
from app.core.email_token import EmailVerificationTokenCodec
from app.domain.auth_context import CurrentUser, build_current_user_from_keycloak
from app.domain.exceptions import Unauthorized
from app.domain.permissions import PermissionCodes
from app.services import email_verification as email_verification_service


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
        self.users = _UsersRepo()


class _EmailVerificationUow(_NoopUow):
    def __init__(self, profiles=None) -> None:
        self.profiles = profiles if profiles is not None else object()


class _EmailVerificationProfilesRepo:
    def __init__(self, profiles: dict[str, str]) -> None:
        self._profiles = {
            user_id: SimpleNamespace(id=user_id, mail=email)
            for user_id, email in profiles.items()
        }

    async def get_by_id(self, user_id: str):
        return self._profiles.get(user_id)

    async def exists_by_mail(self, *, email: str, exclude_user_id: str | None = None) -> bool:
        normalized = email.strip().lower()
        return any(
            profile.mail.strip().lower() == normalized and user_id != exclude_user_id
            for user_id, profile in self._profiles.items()
        )

    async def update_mail_after_verification(self, *, user_id: str, email: str) -> bool:
        profile = self._profiles.get(user_id)
        if profile is None:
            return False
        candidate = email.strip()
        if profile.mail and profile.mail.strip().lower() == candidate.lower():
            return True
        profile.mail = candidate
        return True

    def mail_for(self, user_id: str) -> str | None:
        profile = self._profiles.get(user_id)
        return profile.mail if profile is not None else None


class _FilesRepo:
    async def get_by_id(self, file_id: int):
        return SimpleNamespace(
            id=file_id,
            id_storage_object="obj-1",
            original_name="file.pdf",
            mime_type="application/pdf",
        )

    async def is_normative_file(self, *, file_id: int) -> bool:
        _ = file_id
        return False


class _RequestsRepo:
    async def is_file_linked_to_visible_open_request(self, *, contractor_user_id: str, file_id: int) -> bool:
        _ = (contractor_user_id, file_id)
        return False

    async def get_request_owner_id_by_request_file_id(self, *, file_id: int) -> str | None:
        _ = file_id
        return "owner-1"


class _OffersRepo:
    async def is_file_linked_to_contractor(self, *, contractor_user_id: str, file_id: int) -> bool:
        _ = (contractor_user_id, file_id)
        return False

    async def is_message_file_linked_to_contractor(self, *, contractor_user_id: str, file_id: int) -> bool:
        _ = (contractor_user_id, file_id)
        return False

    async def get_request_owner_id_by_offer_file_id(self, *, file_id: int) -> str | None:
        _ = file_id
        return None

    async def get_request_owner_id_by_message_file_id(self, *, file_id: int) -> str | None:
        _ = file_id
        return None


class _UsersRepo:
    async def get_by_id(self, user_id: str):
        users = {
            "owner-1": SimpleNamespace(id="owner-1", id_role=settings.economist_role_id, id_parent="lead-1"),
            "lead-1": SimpleNamespace(id="lead-1", id_role=settings.lead_economist_role_id, id_parent=None),
        }
        return users.get(user_id)

    async def list_active_user_parent_pairs(self):
        return [("owner-1", "lead-1")]


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
        user_id="lead-1",
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


def test_non_hierarchy_role_with_atomic_file_and_request_read_cannot_download_scoped_file(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    set_current_user(
        make_current_user(
            user_id="admin-1",
            role_id=settings.admin_role_id,
            status="active",
            permissions={PermissionCodes.FILES_DOWNLOAD, PermissionCodes.REQUESTS_READ},
        )
    )
    set_uow(_FileDownloadUow())

    response = test_client.get("/api/v1/files/1/download")

    assert response.status_code == 403


def test_department_atomic_permission_without_delegation_role_is_ignored(
    test_client,
    set_current_user,
    set_uow,
):
    user = build_current_user_from_keycloak(
        user_id="lead-1",
        role_id=settings.lead_economist_role_id,
        status="active",
        api_roles=frozenset(
            {
                PermissionCodes.FILES_DOWNLOAD,
                PermissionCodes.DEPARTMENT_FILES_READ,
            }
        ),
    )
    set_current_user(user)
    set_uow(_FileDownloadUow())

    response = test_client.get("/api/v1/files/1/download")

    assert PermissionCodes.DEPARTMENT_FILES_READ not in user.permissions
    assert response.status_code == 403


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

    monkeypatch.setattr(
        auth_api.EmailVerificationService,
        "request_profile_verification",
        _fake_request_profile_verification,
    )

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

    monkeypatch.setattr(
        auth_api.EmailVerificationService,
        "request_profile_verification",
        _fake_request_profile_verification,
    )

    response = test_client.post(
        "/api/v1/auth/request-email-verification",
        json={"email": "inactive@example.com"},
    )

    assert response.status_code == 403


def test_request_email_verification_blocks_review_non_contractor_even_with_profile_permission(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    review_economist = make_current_user(
        role_id=settings.economist_role_id,
        status="review",
        permissions={PermissionCodes.PROFILE_MANAGE_OWN},
    )
    set_current_user(review_economist)
    set_uow(_EmailVerificationUow())

    async def _fake_request_profile_verification(self, *, user_id: str, email: str):
        _ = (self, user_id, email)
        return "sent"

    monkeypatch.setattr(
        auth_api.EmailVerificationService,
        "request_profile_verification",
        _fake_request_profile_verification,
    )

    response = test_client.post(
        "/api/v1/auth/request-email-verification",
        json={"email": "review-economist@example.com"},
    )

    assert response.status_code == 403


def test_request_email_verification_uses_fake_transport_and_deduplicates_repeat_request(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    profiles = _EmailVerificationProfilesRepo({"contractor-1": "old@example.com"})
    set_uow(_EmailVerificationUow(profiles))
    set_current_user(
        make_current_user(
            user_id="contractor-1",
            role_id=settings.contractor_role_id,
            status="review",
            permissions={PermissionCodes.PROFILE_MANAGE_OWN},
        )
    )
    outbox = []
    auth_api.EmailVerificationService._request_locks.clear()
    monkeypatch.setattr(settings, "web_base_url", "https://acom.example")

    async def _fake_send_email(
        self,
        to_email,
        subject,
        text_content,
        html_content=None,
        attachments=None,
        reply_token=None,
        recipient_context=None,
    ):
        _ = (self, html_content, attachments, reply_token)
        outbox.append(
            {
                "to_email": to_email,
                "subject": subject,
                "text": text_content,
                "recipient_context": recipient_context,
            }
        )

    monkeypatch.setattr(
        email_verification_service.SMTPEmailService,
        "send_email",
        _fake_send_email,
    )

    first_response = test_client.post(
        "/api/v1/auth/request-email-verification",
        json={"email": "new@example.com"},
    )
    second_response = test_client.post(
        "/api/v1/auth/request-email-verification",
        json={"email": "new@example.com"},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert [item["to_email"] for item in outbox] == ["new@example.com"]
    assert outbox[0]["recipient_context"] == {"user_login": "contractor-1", "tg_id": None}
    assert "https://acom.example/verify-email?token=" in outbox[0]["text"]


def test_request_email_verification_rejects_email_used_by_another_profile(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
):
    profiles = _EmailVerificationProfilesRepo(
        {
            "contractor-1": "old@example.com",
            "contractor-2": "taken@example.com",
        }
    )
    set_uow(_EmailVerificationUow(profiles))
    set_current_user(
        make_current_user(
            user_id="contractor-1",
            role_id=settings.contractor_role_id,
            status="review",
            permissions={PermissionCodes.PROFILE_MANAGE_OWN},
        )
    )
    outbox = []
    monkeypatch.setattr(settings, "web_base_url", "https://acom.example")

    async def _fake_send_email(self, *args, **kwargs):
        _ = (self, args, kwargs)
        outbox.append(args)

    monkeypatch.setattr(
        email_verification_service.SMTPEmailService,
        "send_email",
        _fake_send_email,
    )

    response = test_client.post(
        "/api/v1/auth/request-email-verification",
        json={"email": "taken@example.com"},
    )

    assert response.status_code == 409
    assert outbox == []


def test_verify_email_accepts_valid_token_and_repeated_verification(
    test_client,
    set_uow,
):
    profiles = _EmailVerificationProfilesRepo({"contractor-1": "old@example.com"})
    set_uow(_EmailVerificationUow(profiles))
    token = asyncio.run(
        EmailVerificationTokenCodec(
            secret=settings.email_verification_secret,
            ttl_seconds=settings.email_verification_ttl_seconds,
        ).create_profile_token(user_id="contractor-1", email="verified@example.com")
    )

    first_response = test_client.get("/api/v1/auth/verify-email", params={"token": token})
    second_response = test_client.get("/api/v1/auth/verify-email", params={"token": token})

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert profiles.mail_for("contractor-1") == "verified@example.com"


def test_verify_email_rejects_invalid_token(test_client, set_uow):
    set_uow(_EmailVerificationUow(_EmailVerificationProfilesRepo({"contractor-1": "old@example.com"})))

    response = test_client.get(
        "/api/v1/auth/verify-email",
        params={"token": "broken-token-value-with-enough-length"},
    )

    assert response.status_code == 401


def test_verify_email_rejects_expired_token(test_client, set_uow):
    set_uow(_EmailVerificationUow(_EmailVerificationProfilesRepo({"contractor-1": "old@example.com"})))
    token = asyncio.run(
        EmailVerificationTokenCodec(
            secret=settings.email_verification_secret,
            ttl_seconds=-1,
        ).create_profile_token(user_id="contractor-1", email="verified@example.com")
    )

    response = test_client.get("/api/v1/auth/verify-email", params={"token": token})

    assert response.status_code == 401


def test_verify_email_rejects_tg_registration_token_for_profile_flow(test_client, set_uow):
    set_uow(_EmailVerificationUow(_EmailVerificationProfilesRepo({"contractor-1": "old@example.com"})))
    token = asyncio.run(
        EmailVerificationTokenCodec(
            secret=settings.email_verification_secret,
            ttl_seconds=settings.email_verification_ttl_seconds,
        ).create_tg_registration_token(tg_id=123, email="tg@example.com")
    )

    response = test_client.get("/api/v1/auth/verify-email", params={"token": token})

    assert response.status_code == 403


def test_verify_email_rejects_token_email_already_used_by_another_user(test_client, set_uow):
    profiles = _EmailVerificationProfilesRepo(
        {
            "contractor-1": "old@example.com",
            "contractor-2": "taken@example.com",
        }
    )
    set_uow(_EmailVerificationUow(profiles))
    token = asyncio.run(
        EmailVerificationTokenCodec(
            secret=settings.email_verification_secret,
            ttl_seconds=settings.email_verification_ttl_seconds,
        ).create_profile_token(user_id="contractor-1", email="taken@example.com")
    )

    response = test_client.get("/api/v1/auth/verify-email", params={"token": token})

    assert response.status_code == 409
    assert profiles.mail_for("contractor-1") == "old@example.com"
