from __future__ import annotations

from dataclasses import dataclass

from app.domain.exceptions import Conflict, NotFound
from app.domain.policies import CurrentUser, UserPolicy
from app.repositories.files import FileRepository, NormativeFileListRow
from app.services.files import FileService, PreparedUpload

ALLOWED_NORMATIVE_FILE_STATUSES = frozenset({"actual", "outdated"})


@dataclass(frozen=True)
class NormativeFileUpsertResult:
    normative_id: int
    file_id: int


class NormativeFileService:
    def __init__(self, files: FileRepository, *, file_service: FileService | None = None) -> None:
        self._files = files
        self._file_service = file_service or FileService(files)

    async def list_normative_files(
        self,
        *,
        current_user: CurrentUser,
        status: str | None = None,
    ) -> list[NormativeFileListRow]:
        UserPolicy.ensure_can_view_normative_files(current_user)
        if status is not None and status not in ALLOWED_NORMATIVE_FILE_STATUSES:
            raise Conflict("Недопустимый статус нормативного документа")
        return await self._files.list_normative_files(status=status)

    async def update_normative_file_status(
        self,
        *,
        current_user: CurrentUser,
        normative_id: int,
        status: str,
    ) -> NormativeFileListRow:
        UserPolicy.ensure_can_update_normative_file_status(current_user)
        if status not in ALLOWED_NORMATIVE_FILE_STATUSES:
            raise Conflict("Недопустимый статус нормативного документа")
        if not await self._files.supports_normative_status_column():
            raise Conflict("Смена статуса нормативного документа недоступна: в БД отсутствует колонка document_status")

        existing = await self._files.get_normative_file_row(normative_id=normative_id)
        if existing is None:
            raise NotFound("Normative file not found")

        updated = await self._files.update_normative_file_status(normative_id=normative_id, status=status)
        if not updated:
            raise NotFound("Normative file not found")

        refreshed = await self._files.get_normative_file_row(normative_id=normative_id)
        if refreshed is None:
            raise NotFound("Normative file not found")
        return refreshed

    async def upload_normative_file(
        self,
        *,
        current_user: CurrentUser,
        upload: PreparedUpload,
        normative_id: int | None = None,
    ) -> NormativeFileUpsertResult:
        UserPolicy.ensure_can_create_normative_files(current_user)

        if normative_id is None:
            normative_id = await self._files.get_next_normative_file_id()
        else:
            existing_file_id = await self._files.get_normative_file_id(normative_id=normative_id)
            if existing_file_id is not None:
                raise Conflict("Normative file can be uploaded only once")

        new_file = await self._file_service.create_normative_file(upload=upload)
        await self._files.create_normative_file_record(
            normative_id=normative_id,
            file_id=new_file.id,
            status="actual",
        )

        return NormativeFileUpsertResult(normative_id=normative_id, file_id=new_file.id)

    async def ensure_actual_normative_file_exists(self, *, normative_file_id: int) -> NormativeFileListRow:
        normative_file = await self._files.get_normative_file_row(normative_id=normative_file_id)
        if normative_file is None:
            raise Conflict("Для создания заявки необходимо выбрать актуальный нормативный документ")
        if normative_file.status != "actual":
            raise Conflict("Выбранный нормативный документ больше не актуален")
        return normative_file
