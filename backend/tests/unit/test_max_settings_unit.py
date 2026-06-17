from __future__ import annotations

import pytest

from app.core.config import Settings


def test_max_bot_disabled_by_default_when_env_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MAX_BOT_ENABLED", raising=False)
    monkeypatch.delenv("MAX_BOT_TOKEN", raising=False)
    monkeypatch.delenv("MAX_LINK_SECRET", raising=False)

    settings = Settings(_env_file=None)

    assert settings.max_bot_enabled is False


def test_max_bot_secrets_optional_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_BOT_ENABLED", "false")
    monkeypatch.delenv("MAX_BOT_TOKEN", raising=False)
    monkeypatch.delenv("MAX_LINK_SECRET", raising=False)

    settings = Settings(_env_file=None)

    assert settings.max_bot_enabled is False
    assert settings.max_bot_token is None
    assert settings.max_link_secret is None


def test_max_bot_token_required_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_BOT_ENABLED", "true")
    monkeypatch.setenv("MAX_BOT_TOKEN", "")
    monkeypatch.setenv("MAX_LINK_SECRET", "secret")

    with pytest.raises(ValueError, match="MAX_BOT_TOKEN is required when MAX_BOT_ENABLED=true"):
        Settings(_env_file=None)


def test_max_link_secret_required_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_BOT_ENABLED", "true")
    monkeypatch.setenv("MAX_BOT_TOKEN", "token")
    monkeypatch.setenv("MAX_LINK_SECRET", "")

    with pytest.raises(ValueError, match="MAX_LINK_SECRET is required when MAX_BOT_ENABLED=true"):
        Settings(_env_file=None)
