from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class EmailAttachment:
    filename: str
    content_bytes: bytes
    mime_type: str