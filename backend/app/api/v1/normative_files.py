from __future__ import annotations

from fastapi import APIRouter, Depends, File, Path as PathParam, Query, UploadFile

from app.api.dependencies import get_current_user, get_uow
from app.core.uow import UnitOfWork
from app.domain.policies import CurrentUser
from app.schemas.normative_files import (
    NormativeFileItemSchema,
    NormativeFileListData,
    NormativeFileListResponse,
    NormativeFileMutationResponse,
    NormativeFileStatusUpdatePayload,
    NormativeFileStatusUpdateResponse,
)
from app.services.files import FileService
from app.services.normative_files import NormativeFileService

router = APIRouter()


def _normative_file_schema(item) -> NormativeFileItemSchema:
    return NormativeFileItemSchema(
        id=item.id,
        file_id=item.file_id,
        original_name=item.original_name,
        status=item.status,
        created_at=item.created_at,
        download_url=f"/api/v1/files/{item.file_id}/download",
    )


@router.get("/normative-files", response_model=NormativeFileListResponse)
@router.get("/normative-files/", response_model=NormativeFileListResponse, include_in_schema=False)
async def list_normative_files(
    status: str | None = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> NormativeFileListResponse:
    async with uow:
        service = NormativeFileService(uow.files)
        items = await service.list_normative_files(current_user=current_user, status=status)

    return NormativeFileListResponse(
        data=NormativeFileListData(
            items=[_normative_file_schema(item) for item in items],
        ),
    )


@router.patch("/normative-files/{normative_id}/status", response_model=NormativeFileStatusUpdateResponse)
async def update_normative_file_status(
    payload: NormativeFileStatusUpdatePayload,
    normative_id: int = PathParam(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> NormativeFileStatusUpdateResponse:
    async with uow:
        service = NormativeFileService(uow.files)
        item = await service.update_normative_file_status(
            current_user=current_user,
            normative_id=normative_id,
            status=payload.status,
        )

    return NormativeFileStatusUpdateResponse(data=_normative_file_schema(item))


@router.post("/normative-files", response_model=NormativeFileMutationResponse)
@router.post("/normative-files/", response_model=NormativeFileMutationResponse, include_in_schema=False)
async def create_normative_file(
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
            )
    except Exception:
        if normative_file_service is not None:
            await normative_file_service.cleanup_tracked_objects()
        raise

    return NormativeFileMutationResponse(
        data={"normative_id": result.normative_id, "file_id": result.file_id},
    )


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
    )
