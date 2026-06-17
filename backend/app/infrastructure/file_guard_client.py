from __future__ import annotations

from dataclasses import dataclass
import logging

import httpx

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class FileGuardVerdict:
    allowed: bool
    reason_code: str | None
    message: str
    detected_mime: str
    size_bytes: int
    sha256: str


class FileGuardClient:
    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._http_client = http_client

    async def scan_bytes(
        self,
        *,
        original_name: str,
        content_bytes: bytes,
        content_type: str | None,
    ) -> FileGuardVerdict:
        logger.info(
            "Calling file guard service: base_url=%s filename=%s size_bytes=%s claimed_mime=%s",
            self._base_url,
            original_name,
            len(content_bytes),
            (content_type or "application/octet-stream").strip() or "application/octet-stream",
        )
        files = {
            "file": (
                original_name,
                content_bytes,
                (content_type or "application/octet-stream").strip() or "application/octet-stream",
            )
        }
        if self._http_client is not None:
            response = await self._http_client.post("/scan", files=files)
        else:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout_seconds,
                trust_env=False,
            ) as client:
                response = await client.post("/scan", files=files)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            logger.warning(
                "File guard service returned non-success status: status_code=%s filename=%s",
                response.status_code,
                original_name,
            )
            raise
        payload = response.json()
        verdict = FileGuardVerdict(
            allowed=bool(payload.get("allowed")),
            reason_code=payload.get("reason_code"),
            message=str(payload.get("message") or ""),
            detected_mime=str(payload.get("detected_mime") or "application/octet-stream"),
            size_bytes=int(payload.get("size_bytes") or 0),
            sha256=str(payload.get("sha256") or ""),
        )
        logger.info(
            "Received file guard verdict: allowed=%s reason_code=%s detected_mime=%s size_bytes=%s sha256_prefix=%s",
            verdict.allowed,
            verdict.reason_code,
            verdict.detected_mime,
            verdict.size_bytes,
            _hash_prefix(verdict.sha256),
        )
        return verdict


def _hash_prefix(value: str) -> str:
    return value[:12]
