from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import parseaddr
from urllib.parse import parse_qs, unquote, urlparse

from app.domain.exceptions import Unauthorized


@dataclass(frozen=True)
class ReplyTokenClaims:
    request_id: int
    user_id: str
    exp: int


class ReplyTokenCodec:
    PURPOSE = "request_reply"
    _TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")
    _REPLY_TO_ALIAS_PATTERN = re.compile(r"(?:\+|%2B)rt-([A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)", re.IGNORECASE)

    def __init__(self, *, secret: str) -> None:
        self._secret = secret.encode("utf-8")

    async def create_token(self, *, request_id: int, user_id: str, ttl_seconds: int) -> str:
        exp = int((datetime.now(timezone.utc) + timedelta(seconds=max(1, ttl_seconds))).timestamp())
        payload = {
            "purpose": self.PURPOSE,
            "request_id": request_id,
            "user_id": user_id,
            "exp": exp,
        }
        return self._encode(payload)

    async def parse_token(self, token: str) -> ReplyTokenClaims:
        payload = self._decode(token)
        if str(payload.get("purpose", "")).strip() not in {"", self.PURPOSE}:
            raise Unauthorized("Invalid reply token payload")

        try:
            request_id = int(payload.get("request_id"))
        except (TypeError, ValueError) as exc:
            raise Unauthorized("Invalid reply token payload") from exc

        user_id = str(payload.get("user_id", "")).strip()
        if not user_id:
            raise Unauthorized("Invalid reply token payload")

        exp = self._extract_exp(payload)
        return ReplyTokenClaims(request_id=request_id, user_id=user_id, exp=exp)

    async def extract_token_from_email(self, message: EmailMessage) -> str | None:
        candidates: list[str] = []

        for header_name in ("Reply-To", "Subject", "In-Reply-To", "References", "To", "Cc"):
            raw_value = str(message.get(header_name, "")).strip()
            if raw_value:
                candidates.extend(self._extract_from_text(raw_value))

        for body_part in self._extract_message_text_parts(message):
            candidates.extend(self._extract_from_text(body_part))

        for candidate in candidates:
            try:
                await self.parse_token(candidate)
            except Unauthorized:
                continue
            return candidate
        return None

    def _extract_message_text_parts(self, message: EmailMessage) -> list[str]:
        chunks: list[str] = []
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_disposition() == "attachment":
                    continue
                content_type = part.get_content_type()
                if content_type not in {"text/plain", "text/html"}:
                    continue
                payload = part.get_payload(decode=True)
                if not payload:
                    continue
                charset = part.get_content_charset() or "utf-8"
                chunks.append(payload.decode(charset, errors="replace"))
            return chunks

        payload = message.get_payload(decode=True)
        if payload:
            charset = message.get_content_charset() or "utf-8"
            chunks.append(payload.decode(charset, errors="replace"))
        return chunks

    def _extract_exp(self, payload: dict[str, object]) -> int:
        try:
            exp = int(payload.get("exp", 0))
        except (TypeError, ValueError) as exc:
            raise Unauthorized("Invalid reply token payload") from exc
        if exp <= int(datetime.now(timezone.utc).timestamp()):
            raise Unauthorized("Reply token expired")
        return exp

    def _encode(self, payload: dict[str, object]) -> str:
        payload_part = self._b64_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signature_part = self._sign(payload_part)
        return f"{payload_part}.{signature_part}"

    def _decode(self, token: str) -> dict[str, object]:
        try:
            payload_part, signature_part = token.split(".", maxsplit=1)
        except ValueError as exc:
            raise Unauthorized("Invalid reply token") from exc

        expected_signature = self._sign(payload_part)
        if not hmac.compare_digest(signature_part, expected_signature):
            raise Unauthorized("Invalid reply token signature")

        try:
            return json.loads(self._b64_decode(payload_part).decode("utf-8"))
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise Unauthorized("Malformed reply token") from exc

    def _sign(self, value: str) -> str:
        digest = hmac.new(self._secret, value.encode("utf-8"), hashlib.sha256).digest()
        return self._b64_encode(digest)

    def _extract_from_text(self, text: str) -> list[str]:
        extracted: list[str] = []

        for raw_token in self._TOKEN_PATTERN.findall(text):
            extracted.append(raw_token)

        for alias_token in self._REPLY_TO_ALIAS_PATTERN.findall(text):
            extracted.append(alias_token)

        parts = re.split(r"[\s,<>()]", text)
        for part in parts:
            candidate = part.strip().strip("\"'")
            if not candidate:
                continue

            address = parseaddr(candidate)[1].strip()
            if address:
                extracted.extend(self._extract_from_reply_alias_address(address))

            if "?" not in candidate and "mailto:" not in candidate:
                continue

            try:
                parsed = urlparse(candidate)
            except ValueError:
                continue

            if parsed.scheme and parsed.query:
                query_items = parse_qs(parsed.query)
                for key in ("reply_token", "token", "rt"):
                    for token in query_items.get(key, []):
                        decoded = unquote(token).strip()
                        if decoded:
                            extracted.append(decoded)

        unique_tokens = []
        seen: set[str] = set()
        for token in extracted:
            if token in seen:
                continue
            seen.add(token)
            unique_tokens.append(token)
        return unique_tokens

    def _extract_from_reply_alias_address(self, address: str) -> list[str]:
        local_part, _, _ = address.partition("@")
        if not local_part:
            return []

        normalized_local = unquote(local_part)
        matches = self._REPLY_TO_ALIAS_PATTERN.findall(normalized_local)
        return [token.strip() for token in matches if token.strip()]

    @staticmethod
    def _b64_encode(raw: bytes) -> str:
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("utf-8")

    @staticmethod
    def _b64_decode(value: str) -> bytes:
        padding = "=" * ((4 - len(value) % 4) % 4)
        return base64.urlsafe_b64decode(f"{value}{padding}".encode("utf-8"))
