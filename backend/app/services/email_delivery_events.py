from __future__ import annotations

import logging
from typing import Any

from app.core.uow import UnitOfWork
from app.domain.notifications import sanitize_notification_error_message
from app.models.orm_models import UserNotification
from app.services.notifications import NotificationService
from shared.broker import RK_EMAIL_DELIVERY_FAILED, RK_EMAIL_DELIVERY_SUCCEEDED

logger = logging.getLogger(__name__)

BATCH_OPERATION_KIND_REQUEST_ADDITIONAL = "request.additional_email"
BATCH_OPERATION_KIND_CONTRACTOR_INVITE = "contractor.invite"
_BATCH_OPERATION_KINDS = {
    BATCH_OPERATION_KIND_REQUEST_ADDITIONAL,
    BATCH_OPERATION_KIND_CONTRACTOR_INVITE,
}
_TRACKING_NOTIFICATION_TYPE = "system.warning"
_TRACKING_FLAG_TRUE = "true"
_TRACKING_FLAG_FALSE = "false"
_TOAST_CHANNEL_SYSTEM = "system"
_GENERIC_QUEUE_FAILURE_MESSAGE = "Не удалось поставить письмо в очередь на отправку."
_GENERIC_DELIVERY_FAILURE_MESSAGE = "Не удалось отправить письмо. Попробуйте позже."


def _as_optional_int(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_optional_str(value) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _normalize_operation_kind(value) -> str | None:
    normalized = _normalize_optional_str(value)
    if normalized is None or normalized not in _BATCH_OPERATION_KINDS:
        return None
    return normalized


def _build_tracker_seed_payload(
    *,
    operation_id: str,
    operation_kind: str,
    expected_total: int,
    request_id: str | None,
    offer_id: int | None,
) -> dict[str, Any]:
    return {
        "tracking_only": _TRACKING_FLAG_TRUE,
        "operation_id": operation_id,
        "operation_kind": operation_kind,
        "operation_expected_total": expected_total,
        "request_id": request_id,
        "offer_id": offer_id,
        "immediate_failure_count": 0,
        "delivery_success_count": 0,
        "delivery_failure_count": 0,
        "processed_correlation_ids": [],
        "first_error_message": None,
    }


def _operation_context(
    *,
    operation_kind: str,
    request_id: str | None,
    offer_id: int | None,
) -> tuple[str | None, int | None, str | None]:
    if operation_kind == BATCH_OPERATION_KIND_CONTRACTOR_INVITE:
        return None, None, "/contractors"
    if request_id is not None:
        request_entity_id = _as_optional_int(request_id)
        return "request", request_entity_id, f"/requests/{request_id}"
    if offer_id is not None:
        return "offer", offer_id, f"/offers/{offer_id}/workspace"
    return None, None, None


def _is_tracking_only_notification(notification: UserNotification) -> bool:
    payload = notification.payload if isinstance(notification.payload, dict) else {}
    return str(payload.get("tracking_only") or "").strip().lower() == _TRACKING_FLAG_TRUE


def _tracker_progress_score(notification: UserNotification) -> int:
    payload = notification.payload if isinstance(notification.payload, dict) else {}
    return (
        max(0, _as_optional_int(payload.get("immediate_failure_count")) or 0)
        + max(0, _as_optional_int(payload.get("delivery_success_count")) or 0)
        + max(0, _as_optional_int(payload.get("delivery_failure_count")) or 0)
    )


async def _cleanup_duplicate_tracking_notifications(
    *,
    notifications_repo,
    user_id: str,
    operation_id: str,
    keep_id: int,
) -> None:
    candidates = await notifications_repo.list_by_user_and_payload_key(
        user_id=user_id,
        key_name="operation_id",
        key_value=operation_id,
    )
    orphan_ids = [
        candidate.id
        for candidate in candidates
        if candidate.id != keep_id and _is_tracking_only_notification(candidate)
    ]
    if orphan_ids:
        await notifications_repo.delete_by_ids(orphan_ids)


def _processed_correlation_ids(payload: dict[str, Any]) -> list[str]:
    raw_ids = payload.get("processed_correlation_ids")
    if not isinstance(raw_ids, list):
        return []
    normalized: list[str] = []
    for raw_id in raw_ids:
        correlation_id = _normalize_optional_str(raw_id)
        if correlation_id is not None and correlation_id not in normalized:
            normalized.append(correlation_id)
    return normalized


def _summary_notification_content(
    *,
    operation_kind: str,
    expected_total: int,
    success_count: int,
    failure_count: int,
    first_error_message: str | None,
) -> tuple[str, str, str]:
    if operation_kind == BATCH_OPERATION_KIND_CONTRACTOR_INVITE:
        base_success_title = "Приглашения контрагентам отправлены"
        base_partial_title = "Приглашения контрагентам отправлены частично"
        base_failure_title = "Приглашения контрагентам не отправлены"
    else:
        base_success_title = "Дополнительная рассылка завершена"
        base_partial_title = "Дополнительная рассылка завершена частично"
        base_failure_title = "Дополнительная рассылка не выполнена"

    if failure_count == 0:
        return (
            "email.sent",
            "success",
            f"{base_success_title}. Успешно отправлено {success_count} из {expected_total} писем.",
        )

    if success_count == 0:
        body = f"{base_failure_title}. Не удалось отправить ни одного письма из {expected_total}."
        if first_error_message:
            body = f"{body} Причина: {first_error_message}"
        return ("email.failed", "error", body)

    return (
        "system.warning",
        "warning",
        f"{base_partial_title}. Успешно отправлено {success_count} из {expected_total}, ошибок: {failure_count}.",
    )


async def _get_or_create_operation_tracker(
    *,
    notifications_repo,
    recipient_user_id: str,
    operation_id: str,
    operation_kind: str,
    expected_total: int,
    request_id: str | None,
    offer_id: int | None,
) -> UserNotification:
    candidates = await notifications_repo.list_by_user_and_payload_key(
        user_id=recipient_user_id,
        key_name="operation_id",
        key_value=operation_id,
    )
    if candidates:
        tracking_candidates = [candidate for candidate in candidates if _is_tracking_only_notification(candidate)]
        if tracking_candidates:
            tracker = max(tracking_candidates, key=lambda candidate: (_tracker_progress_score(candidate), candidate.id))
            await _cleanup_duplicate_tracking_notifications(
                notifications_repo=notifications_repo,
                user_id=recipient_user_id,
                operation_id=operation_id,
                keep_id=tracker.id,
            )
            return tracker
        return candidates[0]

    entity_type, entity_id, link_url = _operation_context(
        operation_kind=operation_kind,
        request_id=request_id,
        offer_id=offer_id,
    )
    tracker = UserNotification(
        user_id=recipient_user_id,
        type=_TRACKING_NOTIFICATION_TYPE,
        severity="info",
        title="Tracking email operation",
        body="Tracking email operation",
        entity_type=entity_type,
        entity_id=entity_id,
        link_url=link_url,
        payload=_build_tracker_seed_payload(
            operation_id=operation_id,
            operation_kind=operation_kind,
            expected_total=expected_total,
            request_id=request_id,
            offer_id=offer_id,
        ),
    )
    await notifications_repo.create(tracker)
    await _cleanup_duplicate_tracking_notifications(
        notifications_repo=notifications_repo,
        user_id=recipient_user_id,
        operation_id=operation_id,
        keep_id=tracker.id,
    )
    return tracker


async def _finalize_tracker_if_ready(
    *,
    notifications_repo,
    service: NotificationService,
    tracker: UserNotification,
) -> bool:
    payload = dict(tracker.payload or {})
    expected_total = max(0, _as_optional_int(payload.get("operation_expected_total")) or 0)
    immediate_failure_count = max(0, _as_optional_int(payload.get("immediate_failure_count")) or 0)
    delivery_success_count = max(0, _as_optional_int(payload.get("delivery_success_count")) or 0)
    delivery_failure_count = max(0, _as_optional_int(payload.get("delivery_failure_count")) or 0)
    completed_total = immediate_failure_count + delivery_success_count + delivery_failure_count
    if expected_total <= 0 or completed_total < expected_total:
        return False
    if str(payload.get("tracking_only") or "") != _TRACKING_FLAG_TRUE:
        return False

    operation_kind = _normalize_operation_kind(payload.get("operation_kind")) or BATCH_OPERATION_KIND_REQUEST_ADDITIONAL
    first_error_message = _normalize_optional_str(payload.get("first_error_message"))
    notification_type, severity, body = _summary_notification_content(
        operation_kind=operation_kind,
        expected_total=expected_total,
        success_count=delivery_success_count,
        failure_count=immediate_failure_count + delivery_failure_count,
        first_error_message=first_error_message,
    )
    if operation_kind == BATCH_OPERATION_KIND_CONTRACTOR_INVITE:
        title = "Результат отправки приглашений"
    else:
        title = "Результат дополнительной рассылки"

    payload["tracking_only"] = _TRACKING_FLAG_FALSE
    payload["toast_channel"] = _TOAST_CHANNEL_SYSTEM
    payload["completed_total"] = completed_total
    payload["final_success_count"] = delivery_success_count
    payload["final_failure_count"] = immediate_failure_count + delivery_failure_count

    tracker.type = notification_type
    tracker.severity = severity
    tracker.title = title
    tracker.body = body
    tracker.payload = payload
    tracker.read_at = None
    await notifications_repo.save(tracker)
    operation_id_value = _normalize_optional_str(payload.get("operation_id"))
    if operation_id_value:
        await _cleanup_duplicate_tracking_notifications(
            notifications_repo=notifications_repo,
            user_id=tracker.user_id,
            operation_id=operation_id_value,
            keep_id=tracker.id,
        )
    await service.emit_created_event(tracker)
    return True


async def record_email_batch_operation_state(
    *,
    recipient_user_id: str,
    operation_id: str,
    operation_kind: str,
    expected_total: int,
    request_id: str | None = None,
    offer_id: int | None = None,
    immediate_failure_count: int = 0,
    first_error_message: str | None = None,
) -> None:
    normalized_recipient = _normalize_optional_str(recipient_user_id)
    normalized_operation_id = _normalize_optional_str(operation_id)
    normalized_operation_kind = _normalize_operation_kind(operation_kind)
    if normalized_recipient is None or normalized_operation_id is None or normalized_operation_kind is None:
        return
    if expected_total <= 0:
        return

    async with UnitOfWork() as uow:
        notifications_repo = uow.notifications
        if notifications_repo is None:
            logger.warning("Notifications repository is unavailable in UnitOfWork")
            return
        service = NotificationService(notifications_repo)
        tracker = await _get_or_create_operation_tracker(
            notifications_repo=notifications_repo,
            recipient_user_id=normalized_recipient,
            operation_id=normalized_operation_id,
            operation_kind=normalized_operation_kind,
            expected_total=expected_total,
            request_id=request_id,
            offer_id=offer_id,
        )
        payload = dict(tracker.payload or {})
        if str(payload.get("tracking_only") or "") != _TRACKING_FLAG_TRUE:
            return
        payload["operation_expected_total"] = max(expected_total, _as_optional_int(payload.get("operation_expected_total")) or 0)
        payload["request_id"] = request_id if request_id is not None else payload.get("request_id")
        payload["offer_id"] = offer_id if offer_id is not None else payload.get("offer_id")
        payload["immediate_failure_count"] = max(0, _as_optional_int(payload.get("immediate_failure_count")) or 0) + max(0, immediate_failure_count)
        if first_error_message:
            payload["first_error_message"] = payload.get("first_error_message") or sanitize_notification_error_message(first_error_message)
        tracker.payload = payload
        await notifications_repo.save(tracker)
        await _finalize_tracker_if_ready(
            notifications_repo=notifications_repo,
            service=service,
            tracker=tracker,
        )


class EmailDeliveryEventHandler:
    async def handle(self, *, routing_key: str, payload: dict) -> None:
        correlation_id = str(payload.get("correlation_id") or "").strip()
        if not correlation_id:
            logger.warning("Skip email delivery event without correlation_id")
            return

        recipient_user_id = str(payload.get("recipient_user_id") or "").strip()
        if not recipient_user_id:
            logger.warning("Skip email delivery event without recipient_user_id")
            return

        request_id = _normalize_optional_str(payload.get("request_id"))
        offer_id = _as_optional_int(payload.get("offer_id"))
        to_email = str(payload.get("to_email") or "").strip()
        safe_error_code = str(payload.get("safe_error_code") or "").strip() or None
        safe_error_message = str(payload.get("safe_error_message") or "").strip() or None
        suppress_delivery_notification = bool(payload.get("suppress_delivery_notification"))
        operation_id = _normalize_optional_str(payload.get("operation_id"))
        operation_kind = _normalize_operation_kind(payload.get("operation_kind"))
        operation_expected_total = _as_optional_int(payload.get("operation_expected_total"))

        if suppress_delivery_notification:
            logger.info(
                "Skip email delivery center notification due to suppress flag: correlation_id=%s recipient_user_id=%s",
                correlation_id,
                recipient_user_id,
            )
            return

        async with UnitOfWork() as uow:
            notifications_repo = uow.notifications
            if notifications_repo is None:
                logger.warning("Notifications repository is unavailable in UnitOfWork")
                return
            service = NotificationService(notifications_repo)

            if operation_id and operation_kind and operation_expected_total:
                await self._handle_aggregated_operation_event(
                    notifications_repo=notifications_repo,
                    service=service,
                    routing_key=routing_key,
                    correlation_id=correlation_id,
                    recipient_user_id=recipient_user_id,
                    request_id=request_id,
                    offer_id=offer_id,
                    operation_id=operation_id,
                    operation_kind=operation_kind,
                    operation_expected_total=operation_expected_total,
                    safe_error_message=safe_error_message,
                )
                return

            if routing_key == RK_EMAIL_DELIVERY_SUCCEEDED:
                notification_type = "email.sent"
            elif routing_key == RK_EMAIL_DELIVERY_FAILED:
                notification_type = "email.failed"
            else:
                logger.warning("Unsupported email delivery routing key: %s", routing_key)
                return
            if await notifications_repo.exists_by_type_user_and_correlation_id(
                user_id=recipient_user_id,
                notification_type=notification_type,
                correlation_id=correlation_id,
            ):
                logger.info(
                    "Skip duplicate email delivery notification: type=%s user_id=%s correlation_id=%s",
                    routing_key,
                    recipient_user_id,
                    correlation_id,
                )
                return

            payload_data = {
                "correlation_id": correlation_id,
                "request_id": request_id,
                "offer_id": offer_id,
                "to_email": to_email,
                "toast_channel": _TOAST_CHANNEL_SYSTEM,
            }
            if safe_error_code:
                payload_data["safe_error_code"] = safe_error_code

            entity_type = "request" if request_id is not None else "offer" if offer_id is not None else None
            entity_id = _as_optional_int(request_id) if request_id is not None else offer_id
            link_url = f"/requests/{request_id}" if request_id is not None else f"/offers/{offer_id}/workspace" if offer_id is not None else None

            if routing_key == RK_EMAIL_DELIVERY_SUCCEEDED:
                await service.notify_email_sent(
                    recipient_user_id=recipient_user_id,
                    title="Письмо отправлено",
                    body=f"Письмо успешно отправлено на адрес {to_email}.",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    link_url=link_url,
                    payload=payload_data,
                )
                return

            if routing_key == RK_EMAIL_DELIVERY_FAILED:
                await service.notify_email_failed(
                    recipient_user_id=recipient_user_id,
                    error_message=safe_error_message or _GENERIC_DELIVERY_FAILURE_MESSAGE,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    link_url=link_url,
                    payload=payload_data,
                )

    async def _handle_aggregated_operation_event(
        self,
        *,
        notifications_repo,
        service: NotificationService,
        routing_key: str,
        correlation_id: str,
        recipient_user_id: str,
        request_id: str | None,
        offer_id: int | None,
        operation_id: str,
        operation_kind: str,
        operation_expected_total: int,
        safe_error_message: str | None,
    ) -> None:
        tracker = await _get_or_create_operation_tracker(
            notifications_repo=notifications_repo,
            recipient_user_id=recipient_user_id,
            operation_id=operation_id,
            operation_kind=operation_kind,
            expected_total=operation_expected_total,
            request_id=request_id,
            offer_id=offer_id,
        )
        payload = dict(tracker.payload or {})
        if str(payload.get("tracking_only") or "") != _TRACKING_FLAG_TRUE:
            logger.info(
                "Skip late aggregated email delivery event for finalized notification: operation_id=%s recipient_user_id=%s correlation_id=%s",
                operation_id,
                recipient_user_id,
                correlation_id,
            )
            return
        processed_ids = _processed_correlation_ids(payload)
        if correlation_id in processed_ids:
            logger.info(
                "Skip duplicate aggregated email delivery event: operation_id=%s recipient_user_id=%s correlation_id=%s",
                operation_id,
                recipient_user_id,
                correlation_id,
            )
            return

        processed_ids.append(correlation_id)
        payload["processed_correlation_ids"] = processed_ids
        payload["operation_expected_total"] = max(operation_expected_total, _as_optional_int(payload.get("operation_expected_total")) or 0)
        payload["request_id"] = request_id if request_id is not None else payload.get("request_id")
        payload["offer_id"] = offer_id if offer_id is not None else payload.get("offer_id")

        if routing_key == RK_EMAIL_DELIVERY_SUCCEEDED:
            payload["delivery_success_count"] = max(0, _as_optional_int(payload.get("delivery_success_count")) or 0) + 1
        elif routing_key == RK_EMAIL_DELIVERY_FAILED:
            payload["delivery_failure_count"] = max(0, _as_optional_int(payload.get("delivery_failure_count")) or 0) + 1
            if safe_error_message:
                payload["first_error_message"] = payload.get("first_error_message") or sanitize_notification_error_message(safe_error_message)
        else:
            logger.warning("Unsupported email delivery routing key: %s", routing_key)
            return

        tracker.payload = payload
        await notifications_repo.save(tracker)
        await _finalize_tracker_if_ready(
            notifications_repo=notifications_repo,
            service=service,
            tracker=tracker,
        )
