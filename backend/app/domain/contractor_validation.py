from __future__ import annotations

import re

NOT_SPECIFIED_TEXT = "Не указано"

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_INN_RE = re.compile(r"^\d{10}$|^\d{12}$")


def validate_password_bcrypt_bytes(value: str) -> str:
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Пароль слишком длинный (максимум 72 байта)")
    return value


def validate_ru_phone(value: str) -> str:
    normalized = re.sub(r"\D", "", value)
    if len(normalized) != 11 or normalized[0] not in {"7", "8"}:
        raise ValueError("Некорректный формат телефона")
    return value


def validate_inn(value: str) -> str:
    if not _INN_RE.match(value):
        raise ValueError("Некорректный формат ИНН")
    return value


def validate_optional_email(
    value: str | None,
    *,
    allow_placeholder: bool = True,
) -> str | None:
    if value is None:
        return None
    if allow_placeholder and value == NOT_SPECIFIED_TEXT:
        return value
    if not _EMAIL_RE.match(value):
        raise ValueError("Некорректный формат email")
    return value
