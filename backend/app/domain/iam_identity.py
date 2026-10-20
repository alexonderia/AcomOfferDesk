from __future__ import annotations

import hmac
import uuid

from app.core.config import settings


def stable_iam_account_id(login: str) -> uuid.UUID:
    """Build a retry-stable opaque account UUID without storing an outbox row.

    The HMAC keeps identifiers unpredictable while ensuring a retry after a
    partial cross-database failure addresses the same IAM account.
    """

    digest = hmac.digest(
        key=settings.iam_internal_service_token.encode("utf-8"),
        msg=login.strip().encode("utf-8"),
        digest="sha256",
    )
    raw = bytearray(digest[:16])
    raw[6] = (raw[6] & 0x0F) | 0x40
    raw[8] = (raw[8] & 0x3F) | 0x80
    return uuid.UUID(bytes=bytes(raw))
