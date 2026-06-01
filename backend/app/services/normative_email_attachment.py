from __future__ import annotations

from app.domain.exceptions import Conflict, NotFound
from app.infrastructure.email.email_attachment import EmailAttachment
from app.repositories.files import FileRepository
from app.services.files import FileService
from app.services.normative_files import NormativeFileService


class NormativeEmailAttachmentService:
    def __init__(
        self,
        files: FileRepository,
        *,
        file_service: FileService | None = None,
    ) -> None:
        self._files = files
        self._file_service = file_service or FileService(files)
        self._normative_file_service = NormativeFileService(files)

    async def load_required_attachment(self, *, normative_file_id: int) -> EmailAttachment:
        normative_file = await self._normative_file_service.ensure_actual_normative_file_exists(
            normative_file_id=normative_file_id,
        )
        db_file = await self._files.get_normative_file(normative_id=normative_file_id)
        if db_file is None:
            raise Conflict("Выбранный нормативный документ не найден")

        try:
            content_bytes = await self._file_service.read_bytes(db_file=db_file)
        except NotFound as exc:
            raise Conflict("Файл выбранного нормативного документа недоступен для отправки") from exc

        return EmailAttachment(
            filename=normative_file.original_name,
            content_bytes=content_bytes,
            mime_type=db_file.mime_type,
        )
