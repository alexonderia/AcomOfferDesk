from __future__ import annotations

from pydantic import BaseModel


class ScanResponse(BaseModel):
    allowed: bool
    reason_code: str | None
    message: str
    detected_mime: str
    size_bytes: int
    sha256: str
