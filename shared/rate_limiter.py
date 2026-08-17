from __future__ import annotations

import asyncio
import time
from collections import deque
from collections.abc import Callable


class SlidingWindowRateLimiter:
    def __init__(
        self,
        *,
        attempts: int,
        window_seconds: float,
        max_buckets: int,
        cleanup_interval_seconds: float | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if attempts <= 0:
            raise ValueError("attempts must be greater than zero")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be greater than zero")
        if max_buckets <= 0:
            raise ValueError("max_buckets must be greater than zero")
        self._limit = attempts
        self._window = window_seconds
        self._max_buckets = max_buckets
        self._cleanup_interval = (
            cleanup_interval_seconds
            if cleanup_interval_seconds is not None
            else min(window_seconds, 30.0)
        )
        if self._cleanup_interval <= 0:
            raise ValueError("cleanup_interval_seconds must be greater than zero")
        self._clock = clock
        self._attempts: dict[str, deque[float]] = {}
        self._next_cleanup_at = 0.0
        self._lock = asyncio.Lock()

    @property
    def bucket_count(self) -> int:
        return len(self._attempts)

    def _remove_expired(self, cutoff: float) -> None:
        empty_keys: list[str] = []
        for key, attempts in self._attempts.items():
            while attempts and attempts[0] <= cutoff:
                attempts.popleft()
            if not attempts:
                empty_keys.append(key)
        for key in empty_keys:
            self._attempts.pop(key, None)

    def _evict_oldest_bucket(self) -> None:
        oldest_key = min(
            self._attempts,
            key=lambda key: (self._attempts[key][-1], key),
        )
        del self._attempts[oldest_key]

    async def allow(self, key: str) -> bool:
        async with self._lock:
            now = self._clock()
            cutoff = now - self._window
            if now >= self._next_cleanup_at or (
                key not in self._attempts and len(self._attempts) >= self._max_buckets
            ):
                self._remove_expired(cutoff)
                self._next_cleanup_at = now + self._cleanup_interval

            attempts = self._attempts.get(key)
            if attempts is None:
                if len(self._attempts) >= self._max_buckets:
                    self._evict_oldest_bucket()
                attempts = deque()
                self._attempts[key] = attempts
            else:
                while attempts and attempts[0] <= cutoff:
                    attempts.popleft()

            if len(attempts) >= self._limit:
                return False
            attempts.append(now)
            return True
