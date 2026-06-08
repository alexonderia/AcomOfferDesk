from __future__ import annotations

import hashlib
import io
import logging
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path

from .config import settings

logger = logging.getLogger(__name__)

try:
    import magic as magic_lib
except Exception:  # pragma: no cover - optional dependency
    magic_lib = None

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - optional dependency
    PdfReader = None

try:
    from PIL import Image, UnidentifiedImageError
except Exception:  # pragma: no cover - optional dependency
    Image = None
    UnidentifiedImageError = Exception

_ALLOWED_EXTENSIONS = frozenset({".pdf", ".docx", ".xlsx", ".jpg", ".jpeg", ".png"})
_DANGEROUS_EXTENSIONS = frozenset(
    {
        ".exe",
        ".dll",
        ".msi",
        ".bat",
        ".cmd",
        ".ps1",
        ".sh",
        ".js",
        ".html",
        ".htm",
        ".php",
        ".py",
        ".jar",
        ".war",
        ".apk",
        ".scr",
        ".com",
        ".svg",
        ".docm",
        ".xlsm",
        ".pptm",
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
    }
)
_EXPECTED_MIME_BY_EXTENSION = {
    ".pdf": {"application/pdf"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    ".xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".png": {"image/png"},
}


@dataclass(frozen=True, slots=True)
class ScanVerdict:
    allowed: bool
    reason_code: str | None
    message: str
    detected_mime: str
    size_bytes: int
    sha256: str


class FileScanner:
    def scan_bytes(
        self,
        *,
        original_name: str,
        content_bytes: bytes,
    ) -> ScanVerdict:
        size_bytes = len(content_bytes)
        sha256 = hashlib.sha256(content_bytes).hexdigest()
        logger.info(
            "Received file for scan: filename=%s size_bytes=%s sha256_prefix=%s",
            original_name,
            size_bytes,
            _hash_prefix(sha256),
        )

        try:
            safe_name = self._normalize_filename(original_name)
        except ValueError as exc:
            return self._blocked(
                original_name=original_name,
                normalized_name=None,
                extension=None,
                reason_code="unsafe_file_name",
                message=str(exc),
                detected_mime=self._detect_mime(content_bytes=content_bytes),
                size_bytes=size_bytes,
                sha256=sha256,
            )

        extension = Path(safe_name).suffix.lower()
        logger.info(
            "Normalized file name for scan: original_name=%s normalized_name=%s extension=%s",
            original_name,
            safe_name,
            extension,
        )
        detected_mime = self._detect_mime(content_bytes=content_bytes)
        logger.info(
            "Detected file MIME type: filename=%s extension=%s detected_mime=%s",
            safe_name,
            extension,
            detected_mime,
        )

        if extension in _DANGEROUS_EXTENSIONS or extension not in _ALLOWED_EXTENSIONS:
            return self._blocked(
                original_name=original_name,
                normalized_name=safe_name,
                extension=extension,
                reason_code="file_type_not_allowed",
                message="File extension is not allowed",
                detected_mime=detected_mime,
                size_bytes=size_bytes,
                sha256=sha256,
            )
        if size_bytes == 0:
            return self._blocked(
                original_name=original_name,
                normalized_name=safe_name,
                extension=extension,
                reason_code="empty_file",
                message="File is empty",
                detected_mime=detected_mime,
                size_bytes=size_bytes,
                sha256=sha256,
            )
        if size_bytes > settings.max_file_size_bytes:
            return self._blocked(
                original_name=original_name,
                normalized_name=safe_name,
                extension=extension,
                reason_code="file_too_large",
                message="File exceeds maximum size",
                detected_mime=detected_mime,
                size_bytes=size_bytes,
                sha256=sha256,
            )

        expected_mimes = _EXPECTED_MIME_BY_EXTENSION[extension]
        logger.info(
            "Running file checks: filename=%s extension=%s expected_mimes=%s",
            safe_name,
            extension,
            ",".join(sorted(expected_mimes)),
        )
        if detected_mime not in expected_mimes:
            if self._looks_like_extension(extension=extension, content_bytes=content_bytes):
                logger.info(
                    "Detected MIME does not match extension, but signature matches; running deep validation: filename=%s extension=%s detected_mime=%s",
                    safe_name,
                    extension,
                    detected_mime,
                )
                failure = self._validate_content(extension=extension, content_bytes=content_bytes)
                if failure is not None:
                    return self._blocked(
                        original_name=original_name,
                        normalized_name=safe_name,
                        extension=extension,
                        reason_code=failure[0],
                        message=failure[1],
                        detected_mime=detected_mime,
                        size_bytes=size_bytes,
                        sha256=sha256,
                    )
            return self._blocked(
                original_name=original_name,
                normalized_name=safe_name,
                extension=extension,
                reason_code="mime_mismatch",
                message="File extension does not match detected MIME type",
                detected_mime=detected_mime,
                size_bytes=size_bytes,
                sha256=sha256,
            )

        failure = self._validate_content(extension=extension, content_bytes=content_bytes)
        if failure is not None:
            return self._blocked(
                original_name=original_name,
                normalized_name=safe_name,
                extension=extension,
                reason_code=failure[0],
                message=failure[1],
                detected_mime=detected_mime,
                size_bytes=size_bytes,
                sha256=sha256,
            )

        logger.info(
            "File scan completed successfully: filename=%s extension=%s detected_mime=%s size_bytes=%s sha256_prefix=%s",
            safe_name,
            extension,
            detected_mime,
            size_bytes,
            _hash_prefix(sha256),
        )
        return ScanVerdict(
            allowed=True,
            reason_code=None,
            message="File is allowed",
            detected_mime=detected_mime,
            size_bytes=size_bytes,
            sha256=sha256,
        )

    def _blocked(
        self,
        *,
        original_name: str,
        normalized_name: str | None,
        extension: str | None,
        reason_code: str,
        message: str,
        detected_mime: str,
        size_bytes: int,
        sha256: str,
    ) -> ScanVerdict:
        logger.warning(
            "File scan blocked: original_name=%s normalized_name=%s extension=%s reason_code=%s detected_mime=%s size_bytes=%s sha256_prefix=%s",
            original_name,
            normalized_name or "",
            extension or "",
            reason_code,
            detected_mime,
            size_bytes,
            _hash_prefix(sha256),
        )
        return ScanVerdict(
            allowed=False,
            reason_code=reason_code,
            message=message,
            detected_mime=detected_mime,
            size_bytes=size_bytes,
            sha256=sha256,
        )

    @staticmethod
    def _normalize_filename(original_name: str) -> str:
        normalized = unicodedata.normalize("NFKC", (original_name or "").strip())
        if not normalized:
            raise ValueError("File name is required")
        if len(normalized) > 255:
            raise ValueError("File name is too long")
        if any(ord(ch) < 32 for ch in normalized):
            raise ValueError("File name contains control characters")
        if Path(normalized).name != normalized or "/" in normalized or "\\" in normalized:
            raise ValueError("Unsafe file name")
        return normalized

    def _detect_mime(self, *, content_bytes: bytes) -> str:
        if magic_lib is not None:
            try:
                detected = str(magic_lib.from_buffer(content_bytes, mime=True) or "").strip()
                if detected:
                    return self._normalize_magic_mime(detected, content_bytes=content_bytes)
            except Exception:
                if not settings.allow_libmagic_fallback:
                    raise
                logger.warning("libmagic MIME detection failed; falling back to signature-based detection")
        return self._detect_mime_fallback(content_bytes)

    def _normalize_magic_mime(self, detected: str, *, content_bytes: bytes) -> str:
        if detected == "application/zip":
            return self._detect_mime_fallback(content_bytes)
        if detected == "image/jpg":
            return "image/jpeg"
        return detected

    def _detect_mime_fallback(self, content_bytes: bytes) -> str:
        if content_bytes.startswith(b"%PDF-"):
            return "application/pdf"
        if content_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if content_bytes.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        office_mime = self._detect_office_mime(content_bytes)
        if office_mime is not None:
            return office_mime
        return "application/octet-stream"

    def _detect_office_mime(self, content_bytes: bytes) -> str | None:
        if not content_bytes.startswith(b"PK\x03\x04"):
            return None
        try:
            with zipfile.ZipFile(io.BytesIO(content_bytes)) as archive:
                names = set(archive.namelist())
        except zipfile.BadZipFile:
            return None
        if "word/document.xml" in names:
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if "xl/workbook.xml" in names:
            return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return None

    def _validate_content(self, *, extension: str, content_bytes: bytes) -> tuple[str, str] | None:
        logger.info("Validating file content by extension: extension=%s", extension)
        if extension == ".pdf":
            return self._validate_pdf(content_bytes)
        if extension in {".docx", ".xlsx"}:
            return self._validate_office(extension=extension, content_bytes=content_bytes)
        if extension in {".jpg", ".jpeg", ".png"}:
            return self._validate_image(extension=extension, content_bytes=content_bytes)
        return None

    @staticmethod
    def _looks_like_extension(*, extension: str, content_bytes: bytes) -> bool:
        if extension == ".pdf":
            return content_bytes.startswith(b"%PDF-")
        if extension in {".docx", ".xlsx"}:
            return content_bytes.startswith(b"PK\x03\x04")
        if extension == ".png":
            return content_bytes.startswith(b"\x89PNG\r\n\x1a\n")
        if extension in {".jpg", ".jpeg"}:
            return content_bytes.startswith(b"\xff\xd8\xff")
        return False

    def _validate_pdf(self, content_bytes: bytes) -> tuple[str, str] | None:
        if not content_bytes.startswith(b"%PDF-"):
            return ("invalid_pdf", "PDF is corrupted or unreadable")

        if PdfReader is not None:
            try:
                reader = PdfReader(io.BytesIO(content_bytes), strict=False)
                if getattr(reader, "is_encrypted", False):
                    return ("encrypted_pdf_not_allowed", "Encrypted PDF files are not allowed")
                if len(reader.pages) < 1:
                    return ("invalid_pdf", "PDF is corrupted or unreadable")
                return None
            except Exception:
                logger.info("pypdf could not parse PDF; falling back to signature checks")

        if b"%%EOF" not in content_bytes[-2048:]:
            return ("invalid_pdf", "PDF is corrupted or unreadable")
        if b"/Encrypt" in content_bytes[:65536]:
            return ("encrypted_pdf_not_allowed", "Encrypted PDF files are not allowed")
        return None

    @staticmethod
    def _validate_office(*, extension: str, content_bytes: bytes) -> tuple[str, str] | None:
        required_entry = "word/document.xml" if extension == ".docx" else "xl/workbook.xml"
        if not content_bytes.startswith(b"PK\x03\x04"):
            return ("invalid_office_document", "Office document is corrupted or invalid")
        try:
            with zipfile.ZipFile(io.BytesIO(content_bytes)) as archive:
                names = set(archive.namelist())
                if "[Content_Types].xml" not in names or required_entry not in names:
                    return ("invalid_office_document", "Office document is corrupted or invalid")
                for name in names:
                    if name.startswith("/") or ".." in Path(name).parts:
                        return ("invalid_office_document", "Office document is corrupted or invalid")
        except zipfile.BadZipFile:
            return ("invalid_office_document", "Office document is corrupted or invalid")
        return None

    def _validate_image(self, *, extension: str, content_bytes: bytes) -> tuple[str, str] | None:
        if Image is not None:
            try:
                with Image.open(io.BytesIO(content_bytes)) as image:
                    image.verify()
                    format_name = (image.format or "").upper()
                if extension == ".png" and format_name != "PNG":
                    return ("invalid_image", "Image is corrupted or invalid")
                if extension in {".jpg", ".jpeg"} and format_name != "JPEG":
                    return ("invalid_image", "Image is corrupted or invalid")
                return None
            except (UnidentifiedImageError, OSError, ValueError):
                return ("invalid_image", "Image is corrupted or invalid")
        if extension == ".png":
            return self._validate_png(content_bytes)
        return self._validate_jpeg(content_bytes)

    @staticmethod
    def _validate_png(content_bytes: bytes) -> tuple[str, str] | None:
        if not content_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            return ("invalid_image", "Image is corrupted or invalid")
        if b"IEND" not in content_bytes[-32:]:
            return ("invalid_image", "Image is corrupted or invalid")
        return None

    @staticmethod
    def _validate_jpeg(content_bytes: bytes) -> tuple[str, str] | None:
        if not content_bytes.startswith(b"\xff\xd8\xff"):
            return ("invalid_image", "Image is corrupted or invalid")
        if not content_bytes.endswith(b"\xff\xd9"):
            return ("invalid_image", "Image is corrupted or invalid")
        return None


def _hash_prefix(value: str) -> str:
    return value[:12]
