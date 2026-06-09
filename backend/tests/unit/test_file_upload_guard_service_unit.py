from __future__ import annotations

import pytest

from app.core.config import settings
from app.domain.exceptions import ServiceUnavailable, UploadRejected
from app.infrastructure.file_guard_client import FileGuardVerdict
from app.services.file_upload_guard import FileUploadGuardService


class _FakeClient:
    def __init__(self, verdict: FileGuardVerdict | None = None, exc: Exception | None = None) -> None:
        self._verdict = verdict
        self._exc = exc

    async def scan_bytes(self, *, original_name: str, content_bytes: bytes, content_type: str | None):
        _ = (original_name, content_bytes, content_type)
        if self._exc is not None:
            raise self._exc
        assert self._verdict is not None
        return self._verdict


@pytest.mark.asyncio
async def test_scan_bytes_returns_guarded_upload_for_allowed_verdict(monkeypatch) -> None:
    monkeypatch.setattr(settings, "file_guard_enabled", True)
    service = FileUploadGuardService(
        client=_FakeClient(
            verdict=FileGuardVerdict(
                allowed=True,
                reason_code=None,
                message="ok",
                detected_mime="application/pdf",
                size_bytes=8,
                sha256="abc123",
            )
        )
    )

    result = await service.scan_bytes(
        original_name="spec.pdf",
        content_bytes=b"pdfbytes",
        content_type="application/pdf",
    )

    assert result.original_name == "spec.pdf"
    assert result.mime_type == "application/pdf"
    assert result.content_sha256 == "abc123"


@pytest.mark.asyncio
async def test_scan_bytes_raises_upload_rejected_for_blocked_verdict(monkeypatch) -> None:
    monkeypatch.setattr(settings, "file_guard_enabled", True)
    service = FileUploadGuardService(
        client=_FakeClient(
            verdict=FileGuardVerdict(
                allowed=False,
                reason_code="file_type_not_allowed",
                message="bad",
                detected_mime="application/x-msdownload",
                size_bytes=4,
                sha256="def456",
            )
        )
    )

    with pytest.raises(UploadRejected) as exc_info:
        await service.scan_bytes(
            original_name="spec.pdf",
            content_bytes=b"fake",
            content_type="application/pdf",
        )

    assert exc_info.value.reason_code == "file_type_not_allowed"
    assert exc_info.value.detail == "Тип файла не разрешен."
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_scan_bytes_maps_file_scan_unavailable_reason_to_safe_russian_text(monkeypatch) -> None:
    monkeypatch.setattr(settings, "file_guard_enabled", True)
    service = FileUploadGuardService(
        client=_FakeClient(
            verdict=FileGuardVerdict(
                allowed=False,
                reason_code="file_scan_unavailable",
                message="scan engine unavailable",
                detected_mime="application/pdf",
                size_bytes=4,
                sha256="def456",
            )
        )
    )

    with pytest.raises(UploadRejected) as exc_info:
        await service.scan_bytes(
            original_name="spec.pdf",
            content_bytes=b"fake",
            content_type="application/pdf",
        )

    assert exc_info.value.reason_code == "file_scan_unavailable"
    assert exc_info.value.detail == "Файл не удалось проверить. Попробуйте загрузить его позже."


@pytest.mark.asyncio
async def test_scan_bytes_fails_closed_when_guard_errors(monkeypatch) -> None:
    monkeypatch.setattr(settings, "file_guard_enabled", True)
    service = FileUploadGuardService(client=_FakeClient(exc=RuntimeError("boom")))

    with pytest.raises(ServiceUnavailable) as exc_info:
        await service.scan_bytes(
            original_name="spec.pdf",
            content_bytes=b"fake",
            content_type="application/pdf",
        )

    assert exc_info.value.reason_code == "file_scan_unavailable"
    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_scan_bytes_fails_closed_when_feature_is_disabled(monkeypatch) -> None:
    monkeypatch.setattr(settings, "file_guard_enabled", False)
    service = FileUploadGuardService(
        client=_FakeClient(
            verdict=FileGuardVerdict(
                allowed=True,
                reason_code=None,
                message="ok",
                detected_mime="application/pdf",
                size_bytes=4,
                sha256="abc",
            )
        )
    )

    with pytest.raises(ServiceUnavailable) as exc_info:
        await service.scan_bytes(
            original_name="spec.pdf",
            content_bytes=b"fake",
            content_type="application/pdf",
        )

    assert exc_info.value.reason_code == "file_scan_unavailable"
