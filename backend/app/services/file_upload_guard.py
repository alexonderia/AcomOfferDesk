from __future__ import annotations

import hashlib
from dataclasses import dataclass
import logging

import httpx

from app.core.config import settings
from app.domain.exceptions import ServiceUnavailable, UploadRejected
from app.infrastructure.file_guard_client import FileGuardClient, FileGuardVerdict

logger = logging.getLogger(__name__)

_PUBLIC_ERROR_BY_REASON: dict[str, str] = {
    "file_type_not_allowed": "Тип файла не разрешен.",
    "file_too_large": "Файл слишком большой.",
    "empty_file": "Файл пустой.",
    "unsafe_file_name": "Недопустимое имя файла.",
    "mime_mismatch": "Содержимое файла не соответствует расширению файла.",
    "invalid_pdf": "PDF-файл поврежден или не читается.",
    "encrypted_pdf_not_allowed": "Зашифрованные PDF-файлы не поддерживаются.",
    "invalid_office_document": "Office-файл поврежден или имеет неверную структуру.",
    "invalid_image": "Изображение повреждено или имеет неверный формат.",
    "malware_detected": "Файл не прошел проверку безопасности.",
    "file_scan_unavailable": "Файл не удалось проверить. Попробуйте загрузить его позже.",
}
_DEFAULT_BLOCKED_MESSAGE = "Файл не прошел проверку безопасности."
_FILE_SCAN_UNAVAILABLE_MESSAGE = "Сервис проверки файлов временно недоступен."


@dataclass(frozen=True, slots=True)
class GuardedUpload:
    original_name: str
    content_bytes: bytes
    mime_type: str
    content_sha256: str


class FileUploadGuardService:
    def __init__(self, *, client: FileGuardClient | None = None) -> None:
        self._client = client or FileGuardClient(
            base_url=settings.file_guard_url,
            timeout_seconds=settings.file_guard_timeout_seconds,
        )

    async def scan_bytes(
        self,
        *,
        original_name: str,
        content_bytes: bytes,
        content_type: str | None,
    ) -> GuardedUpload:
        if not settings.file_guard_enabled:
            logger.warning(
                "Upload scan rejected because file guard is disabled: filename=%s size_bytes=%s",
                original_name,
                len(content_bytes),
            )
            raise ServiceUnavailable(
                reason_code="file_scan_unavailable",
                detail=_FILE_SCAN_UNAVAILABLE_MESSAGE,
            )

        if len(content_bytes) > settings.max_upload_size_bytes:
            logger.warning(
                "Upload scan rejected before remote call because size exceeds backend limit: filename=%s size_bytes=%s max_size_bytes=%s",
                original_name,
                len(content_bytes),
                settings.max_upload_size_bytes,
            )
            raise UploadRejected(
                reason_code="file_too_large",
                detail=_PUBLIC_ERROR_BY_REASON["file_too_large"],
            )

        logger.info(
            "Submitting file for remote scan: filename=%s size_bytes=%s claimed_mime=%s",
            original_name,
            len(content_bytes),
            (content_type or "application/octet-stream").strip() or "application/octet-stream",
        )
        try:
            verdict = await self._client.scan_bytes(
                original_name=original_name,
                content_bytes=content_bytes,
                content_type=content_type,
            )
        except (httpx.HTTPError, ValueError, TypeError, RuntimeError) as exc:
            logger.exception(
                "Remote file scan failed: filename=%s size_bytes=%s",
                original_name,
                len(content_bytes),
            )
            raise ServiceUnavailable(
                reason_code="file_scan_unavailable",
                detail=_FILE_SCAN_UNAVAILABLE_MESSAGE,
            ) from exc

        self._raise_if_blocked(verdict)

        resolved_sha256 = verdict.sha256.strip() or hashlib.sha256(content_bytes).hexdigest()
        resolved_mime = verdict.detected_mime.strip() or (content_type or "application/octet-stream")
        logger.info(
            "File scan passed: filename=%s detected_mime=%s size_bytes=%s sha256_prefix=%s",
            original_name,
            resolved_mime,
            verdict.size_bytes or len(content_bytes),
            _hash_prefix(resolved_sha256),
        )
        return GuardedUpload(
            original_name=original_name,
            content_bytes=content_bytes,
            mime_type=resolved_mime,
            content_sha256=resolved_sha256,
        )

    @staticmethod
    def _raise_if_blocked(verdict: FileGuardVerdict) -> None:
        if verdict.allowed:
            return
        reason_code = (verdict.reason_code or "file_type_not_allowed").strip() or "file_type_not_allowed"
        detail = _PUBLIC_ERROR_BY_REASON.get(reason_code, _DEFAULT_BLOCKED_MESSAGE)
        logger.warning(
            "File scan blocked upload: reason_code=%s detail=%s detected_mime=%s size_bytes=%s sha256_prefix=%s",
            reason_code,
            detail,
            verdict.detected_mime,
            verdict.size_bytes,
            _hash_prefix(verdict.sha256),
        )
        raise UploadRejected(reason_code=reason_code, detail=detail)


def _hash_prefix(value: str) -> str:
    return value[:12]
