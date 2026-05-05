from __future__ import annotations

import mimetypes
import re
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from uuid import uuid4


@dataclass(slots=True, frozen=True)
class ParsedEmailAttachment:
    original_name: str
    safe_file_name: str
    content_type: str
    content_bytes: bytes


class EmailAttachmentParser:
    def __init__(self, *, max_attachment_size_bytes: int = 25 * 1024 * 1024) -> None:
        self._max_attachment_size_bytes = max_attachment_size_bytes

    async def parse_attachments(self, message: EmailMessage) -> list[ParsedEmailAttachment]:
        parsed: list[ParsedEmailAttachment] = []

        for part in message.walk():
            if part.get_content_disposition() != "attachment":
                continue

            content_bytes = part.get_payload(decode=True) or b""
            if not content_bytes or len(content_bytes) > self._max_attachment_size_bytes:
                continue

            original_name = part.get_filename() or "attachment.bin"
            safe_file_name = self._build_safe_name(original_name)
            content_type = part.get_content_type() or "application/octet-stream"

            parsed.append(
                ParsedEmailAttachment(
                    original_name=original_name,
                    safe_file_name=safe_file_name,
                    content_type=content_type,
                    content_bytes=content_bytes,
                )
            )

        return parsed

    @staticmethod
    def _build_safe_name(original_name: str) -> str:
        base_name = Path(original_name).name.strip() or "attachment"
        stem = Path(base_name).stem or "attachment"
        suffix = Path(base_name).suffix

        safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._-") or "attachment"
        safe_suffix = suffix if suffix else mimetypes.guess_extension("application/octet-stream") or ".bin"
        return f"{safe_stem}_{uuid4().hex}{safe_suffix}"
