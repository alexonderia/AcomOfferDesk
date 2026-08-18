from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from iam_app.core.config import settings
from iam_app.main import app


def test_internal_api_requires_service_authentication() -> None:
    with TestClient(app) as client:
        response = client.get("/internal/rbac")
        assert response.status_code == 403
        assert response.json() == {"detail": "Доступ запрещён"}


def test_internal_rbac_seed_is_idempotent() -> None:
    headers = {"X-Acom-Service-Token": settings.internal_service_token}
    payload = {
        "roles": [
            {"name": "economist", "permissions": ["requests.view", "offers.view"]},
            {"name": "admin", "permissions": ["requests.view", "users.update"]},
        ]
    }
    with TestClient(app) as client:
        first = client.put("/internal/rbac", headers=headers, json=payload)
        second = client.put("/internal/rbac", headers=headers, json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()


def test_internal_reconciliation_is_authenticated_and_read_only() -> None:
    headers = {"X-Acom-Service-Token": settings.internal_service_token}
    with TestClient(app) as client:
        forbidden = client.post(
            "/internal/reconciliation/accounts",
            json={"account_ids": []},
        )
        response = client.post(
            "/internal/reconciliation/accounts",
            headers=headers,
            json={"account_ids": []},
        )

    assert forbidden.status_code == 403
    assert response.status_code == 200
    assert response.json() == {
        "orphan_iam_account_ids": [],
        "missing_iam_account_ids": [],
    }


def test_registration_credential_routes_are_service_only_and_secret_free(caplog) -> None:
    headers = {"X-Acom-Service-Token": settings.internal_service_token}
    account_id = uuid.uuid4()
    password = "registration secret 123"
    path = f"/internal/accounts/{account_id}/registration-credentials"
    payload = {
        "login": "api.registration",
        "role": "economist",
        "auth_status": "pending",
        "password": password,
    }
    with TestClient(app) as client:
        client.put(
            "/internal/rbac",
            headers=headers,
            json={"roles": [{"name": "economist", "permissions": ["requests.view"]}]},
        )
        forbidden_put = client.put(path, json=payload)
        created = client.put(path, headers=headers, json=payload)
        repeated = client.put(path, headers=headers, json=payload)
        conflict = client.put(
            path,
            headers=headers,
            json={**payload, "password": "different registration password"},
        )
        forbidden_state = client.get(f"/internal/accounts/{account_id}/credential-state")
        state = client.get(
            f"/internal/accounts/{account_id}/credential-state",
            headers=headers,
        )
        public_write = client.put(
            f"/iam/accounts/{account_id}/registration-credentials",
            json=payload,
        )

    assert forbidden_put.status_code == 403
    assert forbidden_state.status_code == 403
    assert created.status_code == 200
    assert created.json() == {
        "id": str(account_id),
        "login": "api.registration",
        "role": "economist",
        "auth_status": "pending",
        "password_set": True,
        "required_actions": [],
        "created": True,
    }
    assert repeated.status_code == 200
    assert repeated.json() == {**created.json(), "created": False}
    assert state.status_code == 200
    assert state.json() == {
        "id": str(account_id),
        "login": "api.registration",
        "role": "economist",
        "auth_status": "pending",
        "password_set": True,
        "required_actions": [],
    }
    assert conflict.status_code == 409
    assert conflict.json() == {"detail": "Конфликт данных"}
    assert public_write.status_code == 404
    response_text = created.text + repeated.text + state.text + conflict.text
    assert password not in response_text
    assert "password_hash" not in response_text
    assert password not in caplog.text


def test_password_confirmation_mismatch_does_not_consume_token() -> None:
    headers = {"X-Acom-Service-Token": settings.internal_service_token}
    account_id = uuid.uuid4()
    password = "confirmed password 123"
    with TestClient(app) as client:
        client.put(
            "/internal/rbac",
            headers=headers,
            json={"roles": [{"name": "economist", "permissions": ["requests.view"]}]},
        )
        client.put(
            f"/internal/accounts/{account_id}",
            headers=headers,
            json={
                "login": "confirmation.user",
                "role": "economist",
                "auth_status": "pending",
            },
        )
        passwordless_state = client.get(
            f"/internal/accounts/{account_id}/credential-state",
            headers=headers,
        )
        token_response = client.post(
            f"/internal/accounts/{account_id}/action-tokens",
            headers=headers,
            json={"purpose": "password_setup"},
        )
        token = token_response.json()["token"]
        page = client.get("/iam/password/setup", params={"token": token})
        mismatch = client.post(
            "/iam/password/setup",
            data={
                "token": token,
                "new_password": password,
                "password_confirmation": "different password 123",
            },
        )
        consumed = client.post(
            "/iam/password/setup",
            data={
                "token": token,
                "new_password": password,
                "password_confirmation": password,
            },
        )
        state = client.get(
            f"/internal/accounts/{account_id}/credential-state",
            headers=headers,
        )

    assert token_response.status_code == 200
    assert passwordless_state.status_code == 200
    assert passwordless_state.json()["password_set"] is False
    assert page.status_code == 200
    assert 'name="password_confirmation"' in page.text
    assert page.headers["cache-control"] == "no-store"
    assert page.headers["x-frame-options"] == "DENY"
    assert mismatch.status_code == 400
    assert "Пароли не совпадают" in mismatch.text
    assert password not in mismatch.text
    assert consumed.status_code == 200
    assert "Пароль сохранён" in consumed.text
    assert 'href="/login"' in consumed.text
    assert "Войти" in consumed.text
    assert state.json()["auth_status"] == "pending"
    assert state.json()["password_set"] is True


def test_local_development_provisioning_requires_service_auth_and_creates_active_account(
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "app_env", "development")
    headers = {"X-Acom-Service-Token": settings.internal_service_token}
    with TestClient(app) as client:
        client.put(
            "/internal/rbac",
            headers=headers,
            json={"roles": [{"name": "admin", "permissions": ["users.read"]}]},
        )
        forbidden = client.post(
            "/internal/local-dev/accounts/2efc6d60-a4a6-4e11-8ac4-a3e4d21d679e/provision",
            json={"login": "superadmin", "role": "admin", "auth_status": "active"},
        )
        created = client.post(
            "/internal/local-dev/accounts/2efc6d60-a4a6-4e11-8ac4-a3e4d21d679e/provision",
            headers=headers,
            json={"login": "superadmin", "role": "admin", "auth_status": "active"},
        )

    assert forbidden.status_code == 403
    assert created.status_code == 200
    assert created.json()["auth_status"] == "active"
    assert created.json()["created"] is True


def test_authorize_rejects_unlisted_redirect_and_sets_security_headers() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/iam/authorize",
            params={
                "response_type": "code",
                "state": "s" * 24,
                "code_challenge": "c" * 43,
                "code_challenge_method": "S256",
                "redirect_uri": "https://attacker.invalid/callback",
            },
        )
    assert response.status_code == 400
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-frame-options"] == "DENY"


def test_login_page_never_reflects_password() -> None:
    with TestClient(app) as client:
        authorize = client.get(
            "/iam/authorize",
            params={
                "response_type": "code",
                "state": "s" * 24,
                "code_challenge": "c" * 43,
                "code_challenge_method": "S256",
                "redirect_uri": settings.allowed_redirect_uris[0],
            },
        )
        response = client.post(
            "/iam/login",
            data={"login": "missing.user", "password": "never-reflect-this-secret"},
        )
    assert authorize.status_code == 200
    assert response.status_code == 401
    assert "never-reflect-this-secret" not in response.text
    assert "Неверный логин или пароль" in response.text


def test_login_page_has_password_recovery_link() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/iam/authorize",
            params={
                "response_type": "code",
                "state": "s" * 24,
                "code_challenge": "c" * 43,
                "code_challenge_method": "S256",
                "redirect_uri": settings.allowed_redirect_uris[0],
            },
        )

    assert response.status_code == 200
    assert 'href="/login?reset=1"' in response.text
    assert "Восстановить доступ" in response.text
    assert 'class="aod-app-footer"' in response.text
    assert 'aria-label="Перейти в Битрикс"' in response.text
    assert 'aria-label="Открыть MAX"' in response.text
    assert "img-src data:" in response.headers["content-security-policy"]
    assert "script-src 'nonce-" in response.headers["content-security-policy"]
    assert 'data-password-toggle' in response.text
    assert 'aria-label="Показать пароль"' in response.text
    assert "Безопасный вход" not in response.text


def test_browser_logout_clears_its_own_session_cookie() -> None:
    with TestClient(app) as client:
        client.cookies.set(settings.browser_session_cookie_name, "browser-session", path="/iam")
        response = client.post("/iam/logout")

    assert response.status_code == 204
    assert settings.browser_session_cookie_name in response.headers["set-cookie"]
    assert "Max-Age=0" in response.headers["set-cookie"]


def test_direct_login_restarts_the_browser_authorization_flow() -> None:
    with TestClient(app) as client:
        response = client.get("/iam/login", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/api/v1/auth/login"


def test_expired_login_form_returns_html_recovery_page() -> None:
    with TestClient(app) as client:
        response = client.post("/iam/login", data={"login": "superadmin", "password": "superadmin"})

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("text/html")
    assert "Сессия входа истекла" in response.text
    assert 'href="/api/v1/auth/login"' in response.text


def test_successful_login_creates_browser_session_for_passwordless_retry(monkeypatch) -> None:
    monkeypatch.setattr(settings, "app_env", "development")
    headers = {"X-Acom-Service-Token": settings.internal_service_token}
    first_state = "s" * 24
    second_state = "t" * 24
    challenge = "c" * 43
    with TestClient(app) as client:
        client.put(
            "/internal/rbac",
            headers=headers,
            json={"roles": [{"name": "admin", "permissions": ["users.read"]}]},
        )
        client.post(
            "/internal/local-dev/accounts/2efc6d60-a4a6-4e11-8ac4-a3e4d21d679e/provision",
            headers=headers,
            json={"login": "superadmin", "role": "admin", "auth_status": "active"},
        )
        client.get(
            "/iam/authorize",
            params={
                "response_type": "code",
                "state": first_state,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "redirect_uri": settings.allowed_redirect_uris[0],
            },
        )
        login = client.post(
            "/iam/login",
            data={"login": "superadmin", "password": "superadmin"},
            follow_redirects=False,
        )
        retry = client.get(
            "/iam/authorize",
            params={
                "response_type": "code",
                "state": second_state,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "redirect_uri": settings.allowed_redirect_uris[0],
            },
            follow_redirects=False,
        )

    assert login.status_code == 303
    assert settings.browser_session_cookie_name in login.headers["set-cookie"]
    assert retry.status_code == 303
    assert f"state={second_state}" in retry.headers["location"]
    assert "code=" in retry.headers["location"]
