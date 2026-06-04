from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from shared.broker import RK_EMAIL_DELIVERY_FAILED, RK_EMAIL_DELIVERY_SUCCEEDED

EMAIL_DELIVERY_RESULT_EVENTS = {
    RK_EMAIL_DELIVERY_SUCCEEDED,
    RK_EMAIL_DELIVERY_FAILED,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def generate_correlation_id() -> str:
    return str(uuid4())


@dataclass(frozen=True, slots=True)
class EmailDeliveryResultEvent:
    event_type: str
    correlation_id: str
    recipient_user_id: str | None
    request_id: str | None
    offer_id: int | None
    to_email: str
    suppress_delivery_notification: bool
    operation_id: str | None
    operation_kind: str | None
    operation_expected_total: int | None
    safe_error_code: str | None
    safe_error_message: str | None
    occurred_at: str
