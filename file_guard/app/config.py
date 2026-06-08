from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


@dataclass(frozen=True, slots=True)
class Settings:
    max_file_size_bytes: int = _env_int("FILE_GUARD_MAX_FILE_SIZE_BYTES", _env_int("MAX_UPLOAD_SIZE_BYTES", 5 * 1024 * 1024))
    allow_libmagic_fallback: bool = _env_bool("FILE_GUARD_ALLOW_LIBMAGIC_FALLBACK", True)


settings = Settings()
