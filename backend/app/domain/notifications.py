from __future__ import annotations

import re

NOTIFICATION_TYPES = {
    "offer.created",
    "offer.updated",
    "offer.status_changed",
    "message.created",
    "email.sent",
    "email.failed",
    "request.created",
    "request.files_changed",
    "request.responsible_changed",
    "request.deadline_changed",
    "request.status_changed",
    "user.status_changed",
    "user.review_required",
    "plan.assigned",
    "plan.updated",
    "system.warning",
}

NOTIFICATION_SEVERITIES = {"info", "success", "warning", "error"}

_MAX_ERROR_MESSAGE_LENGTH = 240
_SENSITIVE_VALUE_PATTERN = re.compile(
    r"(?i)\b(password|passwd|token|secret|api[_-]?key|authorization)\b\s*[:=]\s*[^\s,;]+"
)
_TECHNICAL_DETAILS_PATTERN = re.compile(
    r"(?i)(traceback|stack trace|sql|rabbitmq|smtp|internal server error|validationerror)"
)
_SAFE_ERROR_TRANSLATIONS = {
    "network error": "Нет соединения с сервером. Проверьте подключение к интернету.",
    "failed to fetch": "Нет соединения с сервером. Проверьте подключение к интернету.",
    "connection refused": "Почтовый сервер временно недоступен. Попробуйте позже.",
    "timeout": "Почтовый сервер не ответил вовремя. Попробуйте позже.",
    "mailbox unavailable": "Почтовый адрес получателя временно недоступен.",
}


def sanitize_notification_error_message(raw_message: str | None) -> str:
    if raw_message is None:
        return "Не удалось отправить письмо. Проверьте настройки и попробуйте снова."

    first_line = raw_message.strip().splitlines()[0] if raw_message.strip() else ""
    if not first_line:
        return "Не удалось отправить письмо. Проверьте настройки и попробуйте снова."

    lowered = first_line.lower()
    for key, translated in _SAFE_ERROR_TRANSLATIONS.items():
        if key in lowered:
            return translated

    if _TECHNICAL_DETAILS_PATTERN.search(first_line):
        return "Не удалось отправить письмо. Попробуйте позже."

    cleaned = _SENSITIVE_VALUE_PATTERN.sub(r"\1=[redacted]", first_line)
    if _TECHNICAL_DETAILS_PATTERN.search(cleaned):
        return "Не удалось отправить письмо. Попробуйте позже."
    if len(cleaned) > _MAX_ERROR_MESSAGE_LENGTH:
        cleaned = f"{cleaned[:_MAX_ERROR_MESSAGE_LENGTH - 3].rstrip()}..."
    return cleaned
