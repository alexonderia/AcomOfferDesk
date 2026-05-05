from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.links import LinkSet


class NormativeFileMutationResponseData(BaseModel):
    normative_id: int
    file_id: int


class NormativeFileMutationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: NormativeFileMutationResponseData
    links: LinkSet = Field(alias="_links")
