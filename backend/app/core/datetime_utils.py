from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Timezone-aware UTC (comparisons, tokens, API boundaries)."""
    return datetime.now(timezone.utc)


def utc_now_naive() -> datetime:
    """Naive UTC for PostgreSQL TIMESTAMP WITHOUT TIME ZONE (asyncpg)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def normalize_to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def to_db_timestamp(value: datetime) -> datetime:
    """Naive UTC for PostgreSQL TIMESTAMP WITHOUT TIME ZONE (asyncpg)."""
    return normalize_to_utc(value).replace(tzinfo=None)
