from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class EmailAttachment:
    filename: str
    content_bytes: bytes
    mime_type: str

    @property
    def size_bytes(self) -> int:
        return len(self.content_bytes)
