from __future__ import annotations

import re

NOTIFICATION_TYPES = {
    "offer.created",
    "offer.files_changed",
    "offer.accepted",
    "offer.rejected",
    "offer.deleted",
    "message.created",
    "email.sent",
    "email.failed",
    "request.created",
    "request.files_changed",
    "request.responsible_changed",
    "request.deadline_changed",
    "request.status_changed",
    "user.status_changed",
    "plan.assigned",
    "plan.updated",
    "system.warning",
}

NOTIFICATION_SEVERITIES = {"info", "success", "warning", "error"}

_MAX_ERROR_MESSAGE_LENGTH = 240
_SENSITIVE_VALUE_PATTERN = re.compile(
    r"(?i)\b(password|passwd|token|secret|api[_-]?key|authorization)\b\s*[:=]\s*[^\s,;]+"
)


def sanitize_notification_error_message(raw_message: str | None) -> str:
    if raw_message is None:
        return "Не удалось отправить письмо. Проверьте настройки и попробуйте снова."

    first_line = raw_message.strip().splitlines()[0] if raw_message.strip() else ""
    if not first_line:
        return "Не удалось отправить письмо. Проверьте настройки и попробуйте снова."

    if "traceback" in first_line.lower():
        return "Не удалось отправить письмо. Подробности доступны в логах сервера."

    cleaned = _SENSITIVE_VALUE_PATTERN.sub(r"\1=[redacted]", first_line)
    if len(cleaned) > _MAX_ERROR_MESSAGE_LENGTH:
        cleaned = f"{cleaned[:_MAX_ERROR_MESSAGE_LENGTH - 3].rstrip()}..."
    return cleaned
