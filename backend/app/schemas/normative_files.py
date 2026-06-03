from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

NormativeFileStatus = Literal["actual", "outdated"]


class NormativeFileItemSchema(BaseModel):
    id: int
    file_id: int
    original_name: str
    status: NormativeFileStatus
    created_at: str
    download_url: str


class NormativeFileListData(BaseModel):
    items: list[NormativeFileItemSchema]


class NormativeFileListResponse(BaseModel):
    data: NormativeFileListData


class NormativeFileStatusUpdatePayload(BaseModel):
    status: NormativeFileStatus


class NormativeFileMutationResponseData(BaseModel):
    normative_id: int
    file_id: int


class NormativeFileMutationResponse(BaseModel):
    data: NormativeFileMutationResponseData


class NormativeFileStatusUpdateResponse(BaseModel):
    data: NormativeFileItemSchema
