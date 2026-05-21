from __future__ import annotations

import pytest

from app.services import email_delivery_events as module


class _FakeNotificationsRepo:
    def __init__(self, *, dedupe_exists: bool = False) -> None:
        self.dedupe_exists = dedupe_exists
        self.created = []

    async def exists_by_type_user_and_correlation_id(self, *, user_id: str, notification_type: str, correlation_id: str) -> bool:
        _ = (user_id, notification_type, correlation_id)
        return self.dedupe_exists

    async def create(self, notification):
        self.created.append(notification)
        return notification


class _FakeUow:
    def __init__(self, repo: _FakeNotificationsRepo) -> None:
        self.notifications = repo

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        _ = (exc_type, exc, tb)


@pytest.mark.asyncio
async def test_email_delivery_succeeded_creates_email_sent(monkeypatch):
    repo = _FakeNotificationsRepo()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo))
    handler = module.EmailDeliveryEventHandler()

    await handler.handle(
        routing_key="email.delivery.succeeded",
        payload={
            "correlation_id": "corr-1",
            "recipient_user_id": "user-1",
            "request_id": 42,
            "to_email": "contractor@example.com",
        },
    )

    assert len(repo.created) == 1
    assert repo.created[0].type == "email.sent"
    assert repo.created[0].payload["correlation_id"] == "corr-1"


@pytest.mark.asyncio
async def test_email_delivery_failed_creates_email_failed(monkeypatch):
    repo = _FakeNotificationsRepo()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo))
    handler = module.EmailDeliveryEventHandler()

    await handler.handle(
        routing_key="email.delivery.failed",
        payload={
            "correlation_id": "corr-2",
            "recipient_user_id": "user-2",
            "request_id": 44,
            "to_email": "contractor@example.com",
            "safe_error_code": "SMTP_AUTH_FAILED",
            "safe_error_message": "Не удалось отправить письмо. Проверьте настройки почты.",
        },
    )

    assert len(repo.created) == 1
    assert repo.created[0].type == "email.failed"
    assert "traceback" not in repo.created[0].body.lower()


@pytest.mark.asyncio
async def test_email_delivery_dedupe_skips_duplicate(monkeypatch):
    repo = _FakeNotificationsRepo(dedupe_exists=True)
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo))
    handler = module.EmailDeliveryEventHandler()

    await handler.handle(
        routing_key="email.delivery.succeeded",
        payload={
            "correlation_id": "corr-3",
            "recipient_user_id": "user-3",
            "to_email": "contractor@example.com",
        },
    )

    assert repo.created == []

