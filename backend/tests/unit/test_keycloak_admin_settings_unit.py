from __future__ import annotations

from app.core.config import Settings


def test_keycloak_admin_credentials_fallback_from_bootstrap_when_empty(monkeypatch) -> None:
    monkeypatch.setenv("KEYCLOAK_ADMIN_USERNAME", "")
    monkeypatch.setenv("KEYCLOAK_ADMIN_PASSWORD", "")
    monkeypatch.setenv("KC_BOOTSTRAP_ADMIN_USERNAME", "kc_bootstrap_admin")
    monkeypatch.setenv("KC_BOOTSTRAP_ADMIN_PASSWORD", "bootstrap-pass-for-ci-only")

    settings = Settings()

    assert settings.keycloak_admin_username == "kc_bootstrap_admin"
    assert settings.keycloak_admin_password == "bootstrap-pass-for-ci-only"


def test_keycloak_admin_credentials_explicit_override_bootstrap(monkeypatch) -> None:
    monkeypatch.setenv("KEYCLOAK_ADMIN_USERNAME", "explicit_admin")
    monkeypatch.setenv("KEYCLOAK_ADMIN_PASSWORD", "explicit-pass")
    monkeypatch.setenv("KC_BOOTSTRAP_ADMIN_USERNAME", "kc_bootstrap_admin")
    monkeypatch.setenv("KC_BOOTSTRAP_ADMIN_PASSWORD", "bootstrap-pass")

    settings = Settings()

    assert settings.keycloak_admin_username == "explicit_admin"
    assert settings.keycloak_admin_password == "explicit-pass"
