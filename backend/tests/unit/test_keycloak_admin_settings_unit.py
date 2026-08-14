from app.core.config import Settings


def test_legacy_keycloak_flag_cannot_enable_runtime(monkeypatch) -> None:
    monkeypatch.setenv("KEYCLOAK_ENABLED", "true")
    monkeypatch.setenv("KEYCLOAK_BOOTSTRAP_BINDING_ENABLED", "true")
    monkeypatch.setenv("KEYCLOAK_DEV_AUTO_LINK_BY_USERNAME_ENABLED", "true")
    monkeypatch.setenv("KEYCLOAK_PROD_AUTO_LINK_BY_VERIFIED_EMAIL_ENABLED", "true")

    settings = Settings()

    assert settings.keycloak_enabled is False
    assert settings.keycloak_bootstrap_binding_enabled is False
    assert settings.keycloak_dev_auto_link_by_username_enabled is False
    assert settings.keycloak_prod_auto_link_by_verified_email_enabled is False


def test_keycloak_credentials_are_not_required_or_bootstrap_derived(monkeypatch) -> None:
    monkeypatch.setenv("KEYCLOAK_ADMIN_USERNAME", "")
    monkeypatch.setenv("KEYCLOAK_ADMIN_PASSWORD", "")
    monkeypatch.setenv("KC_BOOTSTRAP_ADMIN_USERNAME", "legacy-admin")
    monkeypatch.setenv("KC_BOOTSTRAP_ADMIN_PASSWORD", "legacy-password")

    settings = Settings()

    assert settings.keycloak_admin_username is None
    assert settings.keycloak_admin_password is None
