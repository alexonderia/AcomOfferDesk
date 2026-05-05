from __future__ import annotations

from fastapi import APIRouter, Depends, File, Path as PathParam, UploadFile

from app.api.dependencies import get_current_user, get_uow
from app.core.uow import UnitOfWork
from app.domain.policies import CurrentUser
from app.schemas.links import Link, LinkSet
from app.schemas.normative_files import NormativeFileMutationResponse
from app.services.files import FileService
from app.services.normative_files import NormativeFileService

router = APIRouter()


@router.post("/normative-files/{normative_id}", response_model=NormativeFileMutationResponse)
async def upload_normative_file(
    normative_id: int = PathParam(..., ge=1),
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> NormativeFileMutationResponse:
    prepared = await FileService().prepare_upload(file)

    normative_file_service: FileService | None = None
    try:
        async with uow:
            normative_file_service = FileService(uow.files)
            service = NormativeFileService(uow.files, file_service=normative_file_service)
            result = await service.upload_normative_file(
                current_user=current_user,
                upload=prepared,
                normative_id=normative_id,
            )
    except Exception:
        if normative_file_service is not None:
            await normative_file_service.cleanup_tracked_objects()
        raise

    return NormativeFileMutationResponse(
        data={"normative_id": result.normative_id, "file_id": result.file_id},
        _links=LinkSet(
            self=Link(href=f"/api/v1/normative-files/{normative_id}", method="POST"),
        ),
    )
