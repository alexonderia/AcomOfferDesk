from pydantic import BaseModel, ConfigDict


class Link(BaseModel):
    href: str
    method: str


class LinkSet(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    self: Link
