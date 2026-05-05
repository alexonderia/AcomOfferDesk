from pydantic import BaseModel, Field


class TgLinkRequest(BaseModel):
    tg_id: int = Field(..., ge=1)


class TgLinkData(BaseModel):
    url: str


class TgLinkResponse(BaseModel):
    data: TgLinkData

