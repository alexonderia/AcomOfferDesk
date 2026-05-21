from __future__ import annotations

import json
import smtplib
from email.message import EmailMessage

import pytest

from notifications_worker.app import consumers as worker_consumers
from notifications_worker.app import email_sender as worker_email_sender
from notifications_worker.app.email_sender import EmailSendResult
from shared.broker import RK_EMAIL


class _FakeMessageProcess:
    def __init__(self, owner: "_FakeIncomingMessage", *, requeue: bool) -> None:
        self._owner = owner
        self._requeue = requeue

    async def __aenter__(self):
        self._owner.process_requeue_args.append(self._requeue)
        self._owner.process_enter_count += 1
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)
        self._owner.process_exit_count += 1


class _FakeIncomingMessage:
    def __init__(self, *, body: bytes, routing_key: str) -> None:
        self.body = body
        self.routing_key = routing_key
        self.process_requeue_args: list[bool] = []
        self.process_enter_count = 0
        self.process_exit_count = 0

    def process(self, requeue: bool = False) -> _FakeMessageProcess:
        return _FakeMessageProcess(self, requeue=requeue)


@pytest.fixture(autouse=True)
def _reset_worker_state(monkeypatch):
    worker_email_sender._recent_payloads_until.clear()
    worker_email_sender._recipient_spam_block_until.clear()
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_SECURITY", "ssl")
    monkeypatch.setenv("EMAIL_ADDRESS", "noreply@example.com")
    monkeypatch.setenv("EMAIL_APP_PASSWORD", "password")
    monkeypatch.setenv("EMAIL_FROM_NAME", "AcomOfferDesk")


@pytest.mark.asyncio
async def test_consumer_handles_valid_email_payload_and_uses_no_requeue(monkeypatch):
    sent_payloads: list[dict] = []
    published_events: list[object] = []

    async def _fake_send_email(payload: dict) -> EmailSendResult:
        sent_payloads.append(payload)
        return EmailSendResult(success=True)

    async def _fake_publish(event) -> None:
        published_events.append(event)

    monkeypatch.setattr(worker_consumers, "send_email", _fake_send_email)
    monkeypatch.setattr(worker_consumers, "publish_email_delivery_result", _fake_publish)
    message = _FakeIncomingMessage(
        body=json.dumps({"to_email": "a@example.com", "subject": "Hi", "text_content": "Body"}).encode("utf-8"),
        routing_key=RK_EMAIL,
    )

    await worker_consumers.handle_message(message)

    assert sent_payloads == [{"to_email": "a@example.com", "subject": "Hi", "text_content": "Body"}]
    assert len(published_events) == 1
    assert published_events[0].event_type == "email.delivery.succeeded"
    assert message.process_requeue_args == [False]
    assert message.process_enter_count == 1
    assert message.process_exit_count == 1


@pytest.mark.asyncio
async def test_consumer_ignores_invalid_json_payload(monkeypatch):
    async def _must_not_send_email(payload: dict) -> None:
        raise AssertionError(f"Unexpected send_email call: {payload}")

    monkeypatch.setattr(worker_consumers, "send_email", _must_not_send_email)
    message = _FakeIncomingMessage(body=b"{invalid-json", routing_key=RK_EMAIL)

    await worker_consumers.handle_message(message)

    assert message.process_requeue_args == [False]


@pytest.mark.asyncio
async def test_consumer_ignores_non_dict_payload(monkeypatch):
    async def _must_not_send_email(payload: dict) -> None:
        raise AssertionError(f"Unexpected send_email call: {payload}")

    monkeypatch.setattr(worker_consumers, "send_email", _must_not_send_email)
    message = _FakeIncomingMessage(body=json.dumps(["not", "an", "object"]).encode("utf-8"), routing_key=RK_EMAIL)

    await worker_consumers.handle_message(message)

    assert message.process_requeue_args == [False]


@pytest.mark.asyncio
async def test_consumer_generates_fallback_correlation_id(monkeypatch):
    published_events: list[object] = []

    async def _fake_send_email(payload: dict) -> EmailSendResult:
        _ = payload
        return EmailSendResult(success=False, safe_error_code="SMTP_DELIVERY_ERROR", safe_error_message="safe")

    async def _fake_publish(event) -> None:
        published_events.append(event)

    monkeypatch.setattr(worker_consumers, "send_email", _fake_send_email)
    monkeypatch.setattr(worker_consumers, "publish_email_delivery_result", _fake_publish)
    message = _FakeIncomingMessage(
        body=json.dumps({"to_email": "a@example.com", "subject": "Hi", "text_content": "Body"}).encode("utf-8"),
        routing_key=RK_EMAIL,
    )

    await worker_consumers.handle_message(message)

    assert len(published_events) == 1
    assert published_events[0].event_type == "email.delivery.failed"
    assert published_events[0].correlation_id


class _FakeSMTP:
    def __init__(self, attempts: list[EmailMessage], error_to_raise: BaseException | None = None) -> None:
        self._attempts = attempts
        self._error_to_raise = error_to_raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)

    def ehlo(self) -> None:
        return None

    def starttls(self, context=None) -> None:
        _ = context

    def login(self, username: str, password: str) -> None:
        _ = (username, password)

    def send_message(self, message: EmailMessage, from_addr: str, to_addrs: list[str]) -> None:
        _ = (from_addr, to_addrs)
        self._attempts.append(message)
        if self._error_to_raise is not None:
            raise self._error_to_raise


@pytest.mark.asyncio
async def test_email_sender_skips_payload_without_mandatory_fields(monkeypatch):
    attempts: list[EmailMessage] = []
    monkeypatch.setattr(
        worker_email_sender.smtplib,
        "SMTP_SSL",
        lambda *args, **kwargs: _FakeSMTP(attempts),
    )

    await worker_email_sender.send_email({"to_email": "", "subject": "s", "text_content": "t"})
    await worker_email_sender.send_email({"to_email": "a@example.com", "subject": "", "text_content": "t"})
    await worker_email_sender.send_email({"to_email": "a@example.com", "subject": "s", "text_content": ""})

    assert attempts == []


@pytest.mark.asyncio
async def test_email_sender_sends_valid_payload(monkeypatch):
    attempts: list[EmailMessage] = []
    monkeypatch.setattr(
        worker_email_sender.smtplib,
        "SMTP_SSL",
        lambda *args, **kwargs: _FakeSMTP(attempts),
    )

    await worker_email_sender.send_email(
        {
            "to_email": "a@example.com",
            "subject": "Новая заявка",
            "text_content": "Текст письма",
            "html_content": "<p>Текст письма</p>",
        }
    )

    assert len(attempts) == 1
    assert attempts[0]["To"] == "a@example.com"
    assert attempts[0]["Subject"] == "Новая заявка"


@pytest.mark.asyncio
async def test_email_sender_transient_error_allows_retry(monkeypatch):
    attempts: list[EmailMessage] = []
    error = smtplib.SMTPServerDisconnected("Connection lost")
    monkeypatch.setattr(
        worker_email_sender.smtplib,
        "SMTP_SSL",
        lambda *args, **kwargs: _FakeSMTP(attempts, error_to_raise=error),
    )

    payload = {"to_email": "a@example.com", "subject": "Subject", "text_content": "Body"}
    await worker_email_sender.send_email(payload)
    await worker_email_sender.send_email(payload)

    assert len(attempts) == 2


@pytest.mark.asyncio
async def test_email_sender_spam_rejection_activates_recipient_cooldown(monkeypatch):
    attempts: list[EmailMessage] = []
    error = smtplib.SMTPDataError(554, b"5.7.1 spam suspicion")
    monkeypatch.setattr(
        worker_email_sender.smtplib,
        "SMTP_SSL",
        lambda *args, **kwargs: _FakeSMTP(attempts, error_to_raise=error),
    )

    payload = {"to_email": "spam@example.com", "subject": "Subject", "text_content": "Body"}
    await worker_email_sender.send_email(payload)
    await worker_email_sender.send_email(payload)

    assert len(attempts) == 1
