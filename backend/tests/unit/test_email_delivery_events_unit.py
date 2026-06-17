from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.models.orm_models import UserNotification
from app.services import email_delivery_events as module


class _FakeNotificationsRepo:
    def __init__(self, *, dedupe_exists: bool = False) -> None:
        self.dedupe_exists = dedupe_exists
        self.created = []
        self.by_operation_id: dict[str, UserNotification] = {}

    def _payload_key_value(self, notification: UserNotification, key_name: str) -> str:
        payload = notification.payload or {}
        return str(payload.get(key_name) or "").strip()

    async def exists_by_type_user_and_correlation_id(self, *, user_id: str, notification_type: str, correlation_id: str) -> bool:
        _ = (user_id, notification_type, correlation_id)
        return self.dedupe_exists

    async def create(self, notification):
        notification.id = len(self.created) + 1
        notification.created_at = datetime.now(timezone.utc)
        self.created.append(notification)
        payload = notification.payload or {}
        operation_id = str(payload.get("operation_id") or "").strip()
        if operation_id:
            self.by_operation_id[operation_id] = notification
        return notification

    async def get_by_user_and_payload_key(
        self,
        *,
        user_id: str,
        key_name: str,
        key_value: str,
        notification_type: str | None = None,
    ):
        notifications = await self.list_by_user_and_payload_key(
            user_id=user_id,
            key_name=key_name,
            key_value=key_value,
            notification_type=notification_type,
        )
        if not notifications:
            return None
        return notifications[0]

    async def list_by_user_and_payload_key(
        self,
        *,
        user_id: str,
        key_name: str,
        key_value: str,
        notification_type: str | None = None,
    ):
        _ = (user_id, notification_type)
        matches = [
            notification
            for notification in self.created
            if self._payload_key_value(notification, key_name) == key_value
        ]
        return sorted(matches, key=lambda notification: notification.id, reverse=True)

    async def delete_by_ids(self, notification_ids):
        deleted = 0
        for notification in list(self.created):
            if notification.id in notification_ids:
                operation_id = self._payload_key_value(notification, "operation_id")
                if operation_id and self.by_operation_id.get(operation_id) is notification:
                    self.by_operation_id.pop(operation_id, None)
                self.created.remove(notification)
                deleted += 1
        return deleted

    async def save(self, notification):
        payload = notification.payload or {}
        operation_id = str(payload.get("operation_id") or "").strip()
        if operation_id:
            self.by_operation_id[operation_id] = notification
        return notification


class _FakeUow:
    def __init__(self, repo: _FakeNotificationsRepo) -> None:
        self.notifications = repo

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        _ = (exc_type, exc, tb)


class _FakeRealtimeRuntime:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    async def send_to_user(self, *, user_id: str, event) -> bool:
        self.calls.append((user_id, event))
        return True


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


@pytest.mark.asyncio
async def test_aggregated_delivery_events_finalize_single_summary_notification(monkeypatch):
    repo = _FakeNotificationsRepo()
    runtime = _FakeRealtimeRuntime()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo))
    monkeypatch.setattr("app.realtime.runtime.get_unified_realtime_runtime", lambda: runtime)
    handler = module.EmailDeliveryEventHandler()

    await module.record_email_batch_operation_state(
        recipient_user_id="initiator-1",
        operation_id="op-1",
        operation_kind=module.BATCH_OPERATION_KIND_REQUEST_ADDITIONAL,
        expected_total=2,
        request_id="77",
    )

    await handler.handle(
        routing_key="email.delivery.succeeded",
        payload={
            "correlation_id": "corr-10",
            "recipient_user_id": "initiator-1",
            "request_id": "77",
            "to_email": "ok@example.com",
            "operation_id": "op-1",
            "operation_kind": module.BATCH_OPERATION_KIND_REQUEST_ADDITIONAL,
            "operation_expected_total": 2,
        },
    )

    tracker = repo.by_operation_id["op-1"]
    assert tracker.payload["tracking_only"] == "true"
    assert runtime.calls == []

    await handler.handle(
        routing_key="email.delivery.failed",
        payload={
            "correlation_id": "corr-11",
            "recipient_user_id": "initiator-1",
            "request_id": "77",
            "to_email": "fail@example.com",
            "safe_error_message": "SMTP timeout",
            "operation_id": "op-1",
            "operation_kind": module.BATCH_OPERATION_KIND_REQUEST_ADDITIONAL,
            "operation_expected_total": 2,
        },
    )

    tracker = repo.by_operation_id["op-1"]
    assert len(repo.created) == 1
    assert tracker.type == "system.warning"
    assert tracker.payload["tracking_only"] == "false"
    assert tracker.payload["toast_channel"] == "system"
    assert tracker.payload["final_success_count"] == 1
    assert tracker.payload["final_failure_count"] == 1
    assert "1 из 2" in tracker.body
    assert len(runtime.calls) == 2
    assert all(call[0] == "initiator-1" for call in runtime.calls)
    assert [call[1].type for call in runtime.calls] == ["notification.created", "system.toast"]


@pytest.mark.asyncio
async def test_record_batch_state_finalizes_when_all_queue_attempts_fail(monkeypatch):
    repo = _FakeNotificationsRepo()
    runtime = _FakeRealtimeRuntime()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo))
    monkeypatch.setattr("app.realtime.runtime.get_unified_realtime_runtime", lambda: runtime)

    await module.record_email_batch_operation_state(
        recipient_user_id="initiator-2",
        operation_id="op-2",
        operation_kind=module.BATCH_OPERATION_KIND_CONTRACTOR_INVITE,
        expected_total=2,
        immediate_failure_count=2,
        first_error_message="Не удалось поставить письмо в очередь на отправку",
    )

    tracker = repo.by_operation_id["op-2"]
    assert len(repo.created) == 1
    assert tracker.type == "email.failed"
    assert tracker.payload["tracking_only"] == "false"
    assert tracker.payload["toast_channel"] == "system"
    assert tracker.payload["final_success_count"] == 0
    assert tracker.payload["final_failure_count"] == 2
    assert "ни одного письма" in tracker.body
    assert len(runtime.calls) == 2
    assert [call[1].type for call in runtime.calls] == ["notification.created", "system.toast"]


@pytest.mark.asyncio
async def test_finalize_removes_orphan_tracking_duplicate(monkeypatch):
    repo = _FakeNotificationsRepo()
    runtime = _FakeRealtimeRuntime()
    monkeypatch.setattr(module, "UnitOfWork", lambda: _FakeUow(repo))
    monkeypatch.setattr("app.realtime.runtime.get_unified_realtime_runtime", lambda: runtime)
    handler = module.EmailDeliveryEventHandler()

    orphan = UserNotification(
        user_id="initiator-3",
        type="system.warning",
        severity="info",
        title="Tracking email operation",
        body="Tracking email operation",
        entity_type="request",
        entity_id=88,
        link_url="/requests/88",
        payload=module._build_tracker_seed_payload(
            operation_id="op-3",
            operation_kind=module.BATCH_OPERATION_KIND_REQUEST_ADDITIONAL,
            expected_total=1,
            request_id="88",
            offer_id=None,
        ),
    )
    await repo.create(orphan)
    duplicate = UserNotification(
        user_id="initiator-3",
        type="system.warning",
        severity="info",
        title="Tracking email operation",
        body="Tracking email operation",
        entity_type="request",
        entity_id=88,
        link_url="/requests/88",
        payload=module._build_tracker_seed_payload(
            operation_id="op-3",
            operation_kind=module.BATCH_OPERATION_KIND_REQUEST_ADDITIONAL,
            expected_total=1,
            request_id="88",
            offer_id=None,
        ),
    )
    await repo.create(duplicate)

    await handler.handle(
        routing_key="email.delivery.succeeded",
        payload={
            "correlation_id": "corr-20",
            "recipient_user_id": "initiator-3",
            "request_id": "88",
            "to_email": "ok@example.com",
            "operation_id": "op-3",
            "operation_kind": module.BATCH_OPERATION_KIND_REQUEST_ADDITIONAL,
            "operation_expected_total": 1,
        },
    )

    assert len(repo.created) == 1
    tracker = repo.created[0]
    assert tracker.id == duplicate.id
    assert tracker.title == "Результат дополнительной рассылки"
    assert tracker.payload["tracking_only"] == "false"
    assert tracker.payload["final_success_count"] == 1
