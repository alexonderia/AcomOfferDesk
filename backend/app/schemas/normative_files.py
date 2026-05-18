from __future__ import annotations

from pydantic import BaseModel


class NormativeFileMutationResponseData(BaseModel):
    normative_id: int
    file_id: int


class NormativeFileMutationResponse(BaseModel):
    data: NormativeFileMutationResponseData
