from __future__ import annotations

from datetime import datetime
from html import escape

EMAIL_SUBJECT_PREFIX = "AcomOfferDesk — "

NOTIFICATION_BUTTON_LABEL = "Перейти в систему"
REGISTRATION_BUTTON_LABEL = "Перейти к регистрации"
AUTHORIZATION_BUTTON_LABEL = "Перейти к авторизации"

REGISTRATION_COMPLETED_BODY = "Регистрация пройдена. Данные отправлены на проверку."

ACCESS_OPENED_BODY = "Доступ к системе открыт."
ACCESS_CLOSED_BODY = "Доступ к системе ограничен."

MAX_ACCOUNT_LINKED_BODY = "MAX успешно привязан к вашему аккаунту AcomOfferDesk."

EXPIRED_REGISTRATION_LINK_BODY = "Срок действия ссылки истек. Пожалуйста, запросите новую через /start."

OFFER_STATUS_TITLES = {
    "accepted": "Коммерческое предложение принято",
    "rejected": "Коммерческое предложение отклонено",
    "deleted": "Коммерческое предложение удалено",
}


def email_subject(suffix: str) -> str:
    normalized = suffix.strip()
    if normalized.startswith(EMAIL_SUBJECT_PREFIX):
        return normalized
    return f"{EMAIL_SUBJECT_PREFIX}{normalized}"


def format_status_transition(*, previous: str | None, new: str | None) -> str:
    return f"{(previous or '-').strip()} → {(new or '-').strip()}"


REQUEST_CREATED_BODY_NO_ID = "Поступила новая заявка."


def request_created_body(*, request_id: str | None) -> str:
    if request_id is None:
        return REQUEST_CREATED_BODY_NO_ID
    return f"Поступила новая заявка №{request_id}."


def request_created_title() -> str:
    return "Новая заявка"


def new_request_outbound_body(
    *,
    request_id: str,
    description: str | None,
    deadline_at: datetime,
) -> str:
    description_text = description.strip() if description else "без описания"
    deadline_text = deadline_at.strftime("%d.%m.%Y, %H:%M")
    return (
        f"{request_created_body(request_id=request_id)}\n\n"
        f"{description_text}\n"
        f"Срок: {deadline_text}"
    )


def request_status_changed_title() -> str:
    return "Статус заявки изменён"


_REQUEST_STATUS_LABELS: dict[str, str] = {
    "open": "Открыта",
    "review": "На рассмотрении",
    "closed": "Закрыта",
    "cancelled": "Отменена",
}


def format_request_status_label(status: str | None) -> str:
    """Return a human-readable Russian label for a request status code."""
    normalized = (status or "").strip().lower()
    if not normalized or normalized == "-":
        return "-"
    return _REQUEST_STATUS_LABELS.get(normalized, normalized)


def request_status_changed_body(
    *,
    request_id: str | None,
    previous_status: str | None,
    new_status: str | None,
) -> str:
    prev_label = format_request_status_label(previous_status)
    new_label = format_request_status_label(new_status)
    transition = format_status_transition(previous=prev_label, new=new_label)
    if request_id is None:
        return f"{request_status_changed_title()}: {transition}."
    return f"Заявка №{request_id}: {transition}."


def request_deadline_changed_title() -> str:
    return "Изменён срок заявки"


REQUEST_DEADLINE_CHANGED_BODY_NO_ID = "Изменён срок заявки."


def request_deadline_changed_body(*, request_id: str | None) -> str:
    if request_id is None:
        return REQUEST_DEADLINE_CHANGED_BODY_NO_ID
    return f"По заявке №{request_id} изменён срок."


def request_files_changed_title() -> str:
    return "Изменены файлы заявки"


def request_files_changed_body(*, request_id: str) -> str:
    return f"По заявке №{request_id} обновлены вложения."


def offer_created_title() -> str:
    return "Новое коммерческое предложение"


def offer_created_body(*, request_id: str | None) -> str:
    if request_id is None:
        return "Создано новое КП."
    return f"По заявке №{request_id} создано новое КП."


def offer_updated_title() -> str:
    return "КП обновлено"


OFFER_UPDATED_BODY_NO_REQUEST = "Обновлено коммерческое предложение."


def offer_updated_body(*, request_id: str | None) -> str:
    if request_id is None:
        return OFFER_UPDATED_BODY_NO_REQUEST
    return f"По заявке №{request_id} обновлено коммерческое предложение."


def offer_status_changed_title(*, new_status: str) -> str:
    return OFFER_STATUS_TITLES.get(new_status, "Статус коммерческого предложения изменён")


def offer_status_changed_body(*, request_id: str | None) -> str:
    if request_id is None:
        return "Изменён статус коммерческого предложения."
    return f"По заявке №{request_id} изменён статус КП."


def message_created_title() -> str:
    return "Новое сообщение"


def message_created_body(*, request_id: str) -> str:
    return f"В чате по заявке №{request_id} появилось новое сообщение."


def message_unread_email_subject(*, request_id: str) -> str:
    return email_subject(f"непрочитанное сообщение по заявке №{request_id}")


def message_unread_email_body(*, request_id: str) -> str:
    return (
        f"В чате по заявке №{request_id} осталось непрочитанное сообщение.\n"
        "Откройте систему, чтобы прочитать его."
    )


def message_unread_email_body_html(*, request_id: str) -> str:
    return (
        f"В чате по заявке <strong>№{request_id}</strong> осталось непрочитанное сообщение.<br/>"
        "Откройте систему, чтобы прочитать его."
    )


def plain_to_html_paragraph(text: str) -> str:
    return escape(text).replace("\n", "<br/>")
