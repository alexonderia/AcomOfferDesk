from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

PROCESS_EVENT_TYPES = {
    "offer.created",
    "offer.files_changed",
    "offer.accepted",
    "offer.rejected",
    "offer.deleted",
    "message.created",
    "request.created",
    "request.files_changed",
    "request.responsible_changed",
    "request.deadline_changed",
    "request.status_changed",
    "user.status_changed",
    "system.warning",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _as_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _ensure_iso_datetime(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("occurred_at is required")
    parsed_raw = raw.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(parsed_raw)
    except ValueError as exc:
        raise ValueError("occurred_at must be ISO datetime") from exc
    return raw


@dataclass(frozen=True, slots=True)
class ProcessNotificationEvent:
    event_id: str
    event_type: str
    occurred_at: str
    actor_user_id: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    request_id: int | None = None
    offer_id: int | None = None
    chat_id: int | None = None
    message_id: int | None = None
    dedupe_key: str | None = None
    payload: dict[str, Any] | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at,
            "actor_user_id": self.actor_user_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "request_id": self.request_id,
            "offer_id": self.offer_id,
            "chat_id": self.chat_id,
            "message_id": self.message_id,
            "dedupe_key": self.dedupe_key,
            "payload": self.payload or {},
        }

    @classmethod
    def parse(cls, payload: dict[str, Any]) -> "ProcessNotificationEvent":
        event_id = str(payload.get("event_id") or "").strip()
        if not event_id:
            raise ValueError("event_id is required")
        try:
            UUID(event_id)
        except ValueError as exc:
            raise ValueError("event_id must be UUID") from exc

        event_type = str(payload.get("event_type") or "").strip()
        if not event_type:
            raise ValueError("event_type is required")
        occurred_at = _ensure_iso_datetime(payload.get("occurred_at"))

        raw_envelope_payload = payload.get("payload")
        envelope_payload: dict[str, Any]
        if raw_envelope_payload is None:
            envelope_payload = {}
        elif isinstance(raw_envelope_payload, dict):
            envelope_payload = dict(raw_envelope_payload)
        else:
            raise ValueError("payload must be an object")

        return cls(
            event_id=event_id,
            event_type=event_type,
            occurred_at=occurred_at,
            actor_user_id=_normalize_optional_str(payload.get("actor_user_id")),
            entity_type=_normalize_optional_str(payload.get("entity_type")),
            entity_id=_normalize_optional_str(payload.get("entity_id")),
            request_id=_as_optional_int(payload.get("request_id")),
            offer_id=_as_optional_int(payload.get("offer_id")),
            chat_id=_as_optional_int(payload.get("chat_id")),
            message_id=_as_optional_int(payload.get("message_id")),
            dedupe_key=_normalize_optional_str(payload.get("dedupe_key")),
            payload=envelope_payload,
        )


def build_process_notification_event(
    *,
    event_type: str,
    actor_user_id: str | None = None,
    entity_type: str | None = None,
    entity_id: int | str | None = None,
    request_id: int | None = None,
    offer_id: int | None = None,
    chat_id: int | None = None,
    message_id: int | None = None,
    dedupe_key: str | None = None,
    payload: dict[str, Any] | None = None,
) -> ProcessNotificationEvent:
    normalized_event_type = event_type.strip()
    if not normalized_event_type:
        raise ValueError("event_type is required")
    return ProcessNotificationEvent(
        event_id=str(uuid4()),
        event_type=normalized_event_type,
        occurred_at=utc_now_iso(),
        actor_user_id=_normalize_optional_str(actor_user_id),
        entity_type=_normalize_optional_str(entity_type),
        entity_id=_normalize_optional_str(entity_id),
        request_id=request_id,
        offer_id=offer_id,
        chat_id=chat_id,
        message_id=message_id,
        dedupe_key=_normalize_optional_str(dedupe_key),
        payload=dict(payload or {}),
    )
