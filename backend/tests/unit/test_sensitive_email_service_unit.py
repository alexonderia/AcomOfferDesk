from __future__ import annotations

import logging

import pytest

from app.infrastructure.email.sensitive_email_service import (
    SensitiveEmailDeliveryError,
    SensitiveEmailService,
)
from app.services import iam_password_actions


@pytest.mark.asyncio
async def test_sensitive_email_is_sent_directly_over_smtp_ssl(monkeypatch) -> None:
    observed: dict[str, object] = {}

    class FakeSmtp:
        def __init__(self, host, port, *, timeout, context) -> None:
            observed.update(host=host, port=port, timeout=timeout, context=context)

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def login(self, username, password) -> None:
            observed.update(username=username, password=password)

        def send_message(self, message, *, from_addr, to_addrs) -> None:
            observed.update(message=message, from_addr=from_addr, to_addrs=to_addrs)

    monkeypatch.setattr("smtplib.SMTP_SSL", FakeSmtp)
    service = SensitiveEmailService(
        smtp_host="smtp.example",
        smtp_port=465,
        smtp_security="ssl",
        username="sender@example.com",
        password="smtp-secret",
        from_address="sender@example.com",
        from_name="AcomOfferDesk",
    )

    await service.send_email(
        to_email="recipient@example.com",
        subject="Password action",
        text_content="Open the action link",
        html_content="<p>Open the action link</p>",
    )

    assert observed["host"] == "smtp.example"
    assert observed["username"] == "sender@example.com"
    assert observed["to_addrs"] == ["recipient@example.com"]
    assert observed["message"]["To"] == "recipient@example.com"


@pytest.mark.asyncio
async def test_sensitive_email_sanitizes_smtp_exceptions(monkeypatch) -> None:
    raw_token = "raw-action-token-in-message"

    class FailingSmtp:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def login(self, *_args) -> None:
            pass

        def send_message(self, message, **_kwargs) -> None:
            raise RuntimeError(message.as_string())

    monkeypatch.setattr("smtplib.SMTP_SSL", FailingSmtp)
    service = SensitiveEmailService(
        smtp_host="smtp.example",
        smtp_port=465,
        smtp_security="ssl",
        username="sender@example.com",
        password="smtp-secret",
        from_address="sender@example.com",
        from_name="AcomOfferDesk",
    )

    with pytest.raises(SensitiveEmailDeliveryError) as captured:
        await service.send_email(
            to_email="recipient@example.com",
            subject="Password action",
            text_content=raw_token,
            html_content=f"<p>{raw_token}</p>",
        )

    assert raw_token not in str(captured.value)
    assert captured.value.__cause__ is None


@pytest.mark.asyncio
async def test_safe_password_reset_delivery_never_logs_raw_token(
    monkeypatch,
    caplog,
) -> None:
    raw_token = "raw-reset-token-that-must-not-be-logged"

    async def fail_delivery(**_kwargs) -> None:
        raise RuntimeError(f"synthetic failure containing {raw_token}")

    monkeypatch.setattr(iam_password_actions, "send_iam_password_action_email", fail_delivery)
    with caplog.at_level(logging.ERROR):
        await iam_password_actions.send_iam_password_action_email_safely(
            to_email="recipient@example.com",
            raw_token=raw_token,
            purpose="password_reset",
        )

    assert "iam_password_action_delivery_failed" in caplog.text
    assert raw_token not in caplog.text
