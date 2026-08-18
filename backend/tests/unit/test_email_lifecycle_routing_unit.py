from __future__ import annotations

import pytest

from app.infrastructure.email.smtp_email_service import SMTPEmailService
from app.services import iam_password_actions
from shared.broker import RK_EMAIL


@pytest.mark.asyncio
async def test_ordinary_verification_mail_goes_to_rabbitmq(monkeypatch) -> None:
    published = []

    async def _publish(routing_key, payload):
        published.append((routing_key, payload))

    monkeypatch.setattr("app.infrastructure.email.smtp_email_service.publish_notification", _publish)
    service = SMTPEmailService(
        smtp_host="unused",
        smtp_port=465,
        username="sender@example.com",
        password="secret",
        from_address="sender@example.com",
        from_name="Acom",
    )
    await service.send_email(
        "user@example.com",
        "Verify",
        "token-in-body",
        "<p>token-in-body</p>",
    )
    assert published[0][0] == RK_EMAIL
    assert published[0][1]["to_email"] == "user@example.com"


@pytest.mark.asyncio
async def test_password_setup_and_reset_use_sensitive_direct_smtp(monkeypatch) -> None:
    observed = []

    class FakeSensitive:
        def __init__(self, **_kwargs) -> None:
            pass

        async def send_email(self, **kwargs) -> None:
            observed.append(kwargs)

    monkeypatch.setattr(iam_password_actions, "SensitiveEmailService", FakeSensitive)
    await iam_password_actions.send_iam_password_action_email(
        to_email="user@example.com",
        raw_token="raw-setup-token",
        purpose="password_setup",
    )
    await iam_password_actions.send_iam_password_action_email(
        to_email="user@example.com",
        raw_token="raw-reset-token",
        purpose="password_reset",
    )
    assert len(observed) == 2
    assert "raw-setup-token" in observed[0]["text_content"]
    assert "raw-reset-token" in observed[1]["text_content"]


def test_iam_app_does_not_send_smtp_itself() -> None:
    from pathlib import Path

    iam_root = Path(__file__).resolve().parents[3] / "iam" / "iam_app"
    hits = []
    for path in iam_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "smtplib" in text or "SMTPEmailService" in text or "SensitiveEmailService" in text:
            hits.append(str(path))
    assert hits == []
