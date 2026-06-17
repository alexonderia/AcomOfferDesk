from __future__ import annotations

from typing import Any

_TRUE_FLAG_VALUES = frozenset({"1", "true", "yes", "on"})


def normalize_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def as_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def is_truthy_env_flag(value: Any) -> bool:
    normalized = normalize_optional_str(value)
    if normalized is None:
        return False
    return normalized.lower() in _TRUE_FLAG_VALUES
