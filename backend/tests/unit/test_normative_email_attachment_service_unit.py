from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.domain.exceptions import Conflict, NotFound
from app.services.normative_email_attachment import NormativeEmailAttachmentService


class _FakeFilesRepo:
    def __init__(self, *, status: str = "actual", has_file: bool = True) -> None:
        self._status = status
        self._has_file = has_file

    async def get_normative_file_row(self, *, normative_id: int):
        _ = normative_id
        return SimpleNamespace(
            id=normative_id,
            file_id=100,
            original_name="Презентация.pptx",
            status=self._status,
            created_at="2026-06-01T00:00:00Z",
        )

    async def get_normative_file(self, *, normative_id: int):
        _ = normative_id
        if not self._has_file:
            return None
        return SimpleNamespace(
            original_name="Презентация.pptx",
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )

    async def list_normative_files(self, *, status: str | None = None):
        _ = status
        return [
            SimpleNamespace(
                id=7,
                file_id=100,
                original_name="Презентация.pptx",
                status="actual",
                created_at="2026-06-01T00:00:00Z",
            ),
            SimpleNamespace(
                id=8,
                file_id=101,
                original_name="partner-card.pdf",
                status="actual",
                created_at="2026-06-01T00:00:00Z",
            ),
        ]


class _FakeFileService:
    def __init__(self, *, raise_not_found: bool = False) -> None:
        self._raise_not_found = raise_not_found

    async def read_bytes(self, *, db_file):
        _ = db_file
        if self._raise_not_found:
            raise NotFound("File content not found")
        return b"pptx-bytes"


@pytest.mark.asyncio
async def test_load_required_attachment_reads_actual_normative_file() -> None:
    service = NormativeEmailAttachmentService(
        _FakeFilesRepo(),
        file_service=_FakeFileService(),
    )

    attachment = await service.load_required_attachment(normative_file_id=5)

    assert attachment.filename == "Презентация.pptx"
    assert attachment.mime_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    assert attachment.content_bytes == b"pptx-bytes"


@pytest.mark.asyncio
async def test_load_required_attachment_rejects_non_actual_normative_file() -> None:
    service = NormativeEmailAttachmentService(
        _FakeFilesRepo(status="outdated"),
        file_service=_FakeFileService(),
    )

    with pytest.raises(Conflict):
        await service.load_required_attachment(normative_file_id=5)


@pytest.mark.asyncio
async def test_load_required_attachment_rejects_missing_normative_file_content() -> None:
    service = NormativeEmailAttachmentService(
        _FakeFilesRepo(has_file=False),
        file_service=_FakeFileService(),
    )

    with pytest.raises(Conflict):
        await service.load_required_attachment(normative_file_id=5)


@pytest.mark.asyncio
async def test_resolve_presentation_normative_file_id_prefers_presentation_name() -> None:
    service = NormativeEmailAttachmentService(
        _FakeFilesRepo(),
        file_service=_FakeFileService(),
    )

    normative_id = await service.resolve_presentation_normative_file_id()

    assert normative_id == 7


@pytest.mark.asyncio
async def test_load_required_attachment_rejects_missing_storage_object() -> None:
    service = NormativeEmailAttachmentService(
        _FakeFilesRepo(),
        file_service=_FakeFileService(raise_not_found=True),
    )

    with pytest.raises(Conflict):
        await service.load_required_attachment(normative_file_id=5)
