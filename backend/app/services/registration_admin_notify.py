"""Owner notifications when a new local user is created (registration paths)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Awaitable, Callable

import httpx

from app.core.config import settings
from app.infrastructure.notification_publisher import publish_process_notification_event
from app.domain.permissions import get_permissions_for_role
from app.services.keycloak_app_roles import role_mapping_by_local_role_id
from shared.process_notifications import build_process_notification_event

logger = logging.getLogger(__name__)

_SOURCE_LABELS = {
    "admin_register": "создание сотрудника (админка)",
    "contractor_tg": "регистрация контрагента (Telegram)",
    "oidc_invite": "регистрация по invite (Keycloak OIDC)",
    "manual_contractor": "ручной контрагент (админка)",
}


@dataclass(frozen=True, slots=True)
class RegistrationNotifyContext:
    source: str
    user_id: str
    role_id: int
    role_name: str | None
    status: str
    full_name: str | None = None
    email: str | None = None
    registered_by: str | None = None
    company_name: str | None = None
    keycloak_subject: str | None = None


def build_permission_audit(role_id: int) -> dict[str, object]:
    """Matrix from backend/app/domain/permissions.py (upstream test branch)."""
    permissions = sorted(get_permissions_for_role(role_id))
    keycloak_app_role = role_mapping_by_local_role_id().get(role_id)
    sample = permissions[:10]
    extra = len(permissions) - len(sample)
    sample_suffix = f" (+ещё {extra})" if extra > 0 else ""
    return {
        "permissions_count": len(permissions),
        "keycloak_app_role": keycloak_app_role or "—",
        "permissions_sample": ", ".join(sample) + sample_suffix if sample else "—",
        "matrix_ok": keycloak_app_role is not None and len(permissions) > 0,
    }


def format_registration_message(ctx: RegistrationNotifyContext) -> str:
    audit = build_permission_audit(ctx.role_id)
    source_label = _SOURCE_LABELS.get(ctx.source, ctx.source)
    role_line = f"{ctx.role_name or '—'} (id={ctx.role_id})"

    if ctx.source == "manual_contractor":
        subject_label = "Контрагент (компания)"
        display_name = (ctx.company_name or "").strip() or ctx.user_id
    elif ctx.source == "contractor_tg":
        subject_label = "Представитель"
        display_name = (ctx.full_name or "").strip() or ctx.user_id
    else:
        subject_label = "Пользователь"
        display_name = (ctx.full_name or "").strip() or ctx.user_id

    lines = [
        "Регистрация AcomOfferDesk",
        f"Источник: {source_label}",
        f"{subject_label}: {display_name}",
        f"Логин: {ctx.user_id} | статус: {ctx.status}",
        f"Роль: {role_line} → Keycloak {audit['keycloak_app_role']}",
        f"Прав по матрице permissions.py: {audit['permissions_count']} "
        f"({audit['permissions_sample']})",
    ]
    if ctx.email:
        lines.append(f"Email: {ctx.email}")
    if ctx.company_name and ctx.source != "manual_contractor":
        lines.append(f"Компания: {ctx.company_name}")
    if ctx.registered_by:
        lines.append(f"Создал: {ctx.registered_by}")
    if ctx.keycloak_subject:
        lines.append(f"Keycloak subject: {ctx.keycloak_subject[:12]}…")
    if not audit["matrix_ok"]:
        lines.append("⚠️ Проверьте: роль без Keycloak app.* или пустая матрица прав")
    return "\n".join(lines)


async def notify_new_user_registration(ctx: RegistrationNotifyContext) -> None:
    """POST human-readable registration alert (best-effort; never raises to caller)."""
    if not settings.registration_notify_enabled:
        return
    url = (settings.registration_notify_url or "").strip()
    if not url:
        logger.debug("registration_notify: URL unset, skip user=%s", ctx.user_id)
        return

    message = format_registration_message(ctx)
    audit = build_permission_audit(ctx.role_id)
    payload: dict[str, object] = {
        "event": "user_registration",
        "service": settings.registration_notify_service,
        "user_id": ctx.user_id,
        "role_id": ctx.role_id,
        "role_name": ctx.role_name,
        "status": ctx.status,
        "source": ctx.source,
        "message": message,
        "environment": "prod",
        "permissions_count": audit["permissions_count"],
        "keycloak_app_role": audit["keycloak_app_role"],
        "matrix_ok": audit["matrix_ok"],
    }
    if ctx.full_name:
        payload["full_name"] = ctx.full_name.strip()
    if ctx.email:
        payload["email"] = ctx.email
    if ctx.company_name:
        payload["company_name"] = ctx.company_name
    headers = {"Content-Type": "application/json"}
    token = (settings.registration_notify_token or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    timeout = max(1.0, float(settings.registration_notify_timeout_seconds))
    try:
        async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
            response = await client.post(url, json=payload, headers=headers)
        if response.status_code >= 300:
            logger.warning(
                "registration_notify: HTTP %s for user=%s url=%s",
                response.status_code,
                ctx.user_id,
                url,
            )
    except Exception:
        logger.exception("registration_notify: failed for user=%s", ctx.user_id)


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
    after_commit_hook_registrar(
        lambda: publish_process_notification_event(event)
    )
    return True
