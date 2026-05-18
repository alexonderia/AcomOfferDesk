from __future__ import annotations

import pytest

from shared.process_notifications import ProcessNotificationEvent, build_process_notification_event


def test_process_notification_event_parse_valid_payload():
    payload = {
        "event_id": "8a62a16a-cf38-4ef0-995a-2ec2f4ab4d8a",
        "event_type": "offer.created",
        "occurred_at": "2026-05-18T12:00:00Z",
        "actor_user_id": "user-1",
        "entity_type": "offer",
        "entity_id": "123",
        "request_id": 42,
        "offer_id": 123,
        "dedupe_key": "offer.created:123",
        "payload": {"x": 1},
    }

    event = ProcessNotificationEvent.parse(payload)

    assert event.event_type == "offer.created"
    assert event.offer_id == 123
    assert event.payload == {"x": 1}


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"event_id": "bad", "event_type": "offer.created", "occurred_at": "2026-05-18T12:00:00Z"},
        {"event_id": "8a62a16a-cf38-4ef0-995a-2ec2f4ab4d8a", "event_type": "", "occurred_at": "2026-05-18T12:00:00Z"},
        {"event_id": "8a62a16a-cf38-4ef0-995a-2ec2f4ab4d8a", "event_type": "offer.created", "occurred_at": "bad"},
    ],
)
def test_process_notification_event_parse_rejects_invalid_payload(payload):
    with pytest.raises(ValueError):
        ProcessNotificationEvent.parse(payload)


def test_build_process_notification_event_populates_defaults():
    event = build_process_notification_event(
        event_type="message.created",
        payload={"chat_id": 5},
    )

    assert event.event_id
    assert event.occurred_at.endswith("Z")
    assert event.payload == {"chat_id": 5}
