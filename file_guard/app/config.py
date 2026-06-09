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


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value if value > 0 else default


@dataclass(frozen=True, slots=True)
class Settings:
    max_file_size_bytes: int = _env_int("FILE_GUARD_MAX_FILE_SIZE_BYTES", _env_int("MAX_UPLOAD_SIZE_BYTES", 5 * 1024 * 1024))
    allow_libmagic_fallback: bool = _env_bool("FILE_GUARD_ALLOW_LIBMAGIC_FALLBACK", True)
    antivirus_enabled: bool = _env_bool("FILE_GUARD_ANTIVIRUS_ENABLED", True)
    antivirus_timeout_seconds: float = _env_float("FILE_GUARD_ANTIVIRUS_TIMEOUT_SECONDS", 10.0)
    clamd_socket_path: str = os.getenv("FILE_GUARD_CLAMD_SOCKET_PATH", "/run/clamav/clamd.sock").strip() or "/run/clamav/clamd.sock"
    clamd_stream_chunk_bytes: int = _env_int("FILE_GUARD_CLAMD_STREAM_CHUNK_BYTES", 65536)
    office_max_entries: int = _env_int("FILE_GUARD_OFFICE_MAX_ENTRIES", 200)
    office_max_total_uncompressed_bytes: int = _env_int("FILE_GUARD_OFFICE_MAX_TOTAL_UNCOMPRESSED_BYTES", 40 * 1024 * 1024)
    office_max_entry_uncompressed_bytes: int = _env_int("FILE_GUARD_OFFICE_MAX_ENTRY_UNCOMPRESSED_BYTES", 12 * 1024 * 1024)
    office_max_compression_ratio: float = _env_float("FILE_GUARD_OFFICE_MAX_COMPRESSION_RATIO", 120.0)
    office_max_xml_scan_bytes: int = _env_int("FILE_GUARD_OFFICE_MAX_XML_SCAN_BYTES", 1024 * 1024)
    office_max_entry_name_length: int = _env_int("FILE_GUARD_OFFICE_MAX_ENTRY_NAME_LENGTH", 255)
    upload_read_chunk_bytes: int = _env_int("FILE_GUARD_UPLOAD_READ_CHUNK_BYTES", 1024 * 1024)
    image_max_width: int = _env_int("FILE_GUARD_IMAGE_MAX_WIDTH", 12000)
    image_max_height: int = _env_int("FILE_GUARD_IMAGE_MAX_HEIGHT", 12000)
    image_max_pixels: int = _env_int("FILE_GUARD_IMAGE_MAX_PIXELS", 40_000_000)


settings = Settings()
