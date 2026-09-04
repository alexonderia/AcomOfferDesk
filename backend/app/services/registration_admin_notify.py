"""Internal review notifications for newly registered local users."""

from __future__ import annotations

from typing import Awaitable, Callable

from app.infrastructure.notification_publisher import publish_process_notification_event
from shared.process_notifications import build_process_notification_event


def schedule_registration_review_required_notification(
    *,
    after_commit_hook_registrar: Callable[[Callable[[], Awaitable[None]]], None] | None,
    user_id: str,
    actor_user_id: str,
    role_id: int,
    source: str,
) -> bool:
    if after_commit_hook_registrar is None:
        return False
    event = build_process_notification_event(
        event_type="user.review_required",
        actor_user_id=actor_user_id,
        entity_type="user",
        entity_id=user_id,
        dedupe_key=f"user.review_required:{user_id}:{source}",
        payload={
            "target_user_id": user_id,
            "target_role": role_id,
            "source": source,
        },
    )
    after_commit_hook_registrar(lambda: publish_process_notification_event(event))
    return True
