from __future__ import annotations

from dataclasses import dataclass

from app.domain.exceptions import Conflict
from app.domain.policies import CurrentUser, UserPolicy
from app.repositories.files import FileRepository
from app.services.files import FileService, PreparedUpload


@dataclass(frozen=True)
class NormativeFileUpsertResult:
    normative_id: int
    file_id: int


class NormativeFileService:
    def __init__(self, files: FileRepository, *, file_service: FileService | None = None) -> None:
        self._files = files
        self._file_service = file_service or FileService(files)

    async def upload_normative_file(
        self,
        *,
        current_user: CurrentUser,
        upload: PreparedUpload,
        normative_id: int = 1,
    ) -> NormativeFileUpsertResult:
        UserPolicy.ensure_can_manage_normative_files(current_user)

        existing_file_id = await self._files.get_normative_file_id(normative_id=normative_id)
        if existing_file_id is not None:
            raise Conflict("Normative file can be uploaded only once")

        new_file = await self._file_service.create_normative_file(upload=upload)
        await self._files.upsert_normative_file(normative_id=normative_id, file_id=new_file.id)

        return NormativeFileUpsertResult(normative_id=normative_id, file_id=new_file.id)
