from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import hmac
import json
import os
import subprocess
import sys
import time
import threading
import unicodedata

from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.domain.exceptions import Conflict, Forbidden
from app.domain.policies import CurrentUser, UserPolicy
from app.infrastructure.specification_parser import DOCX_MIME
from app.services.files import FileService, PreparedUpload

TOKEN_TTL = 60 * 60
CONFIRMATION_VERSION = 5
MAX_SOURCE_FILES = 5
_PARSER_SLOTS = threading.BoundedSemaphore(2)


@dataclass(frozen=True)
class SpecificationPreview:
    file: PreparedUpload
    confirmation: str
    item_count: int
    used_ocr: bool


@dataclass(frozen=True)
class VerifiedSpecification:
    public_source_indices: tuple[int, ...]
    extraction_indices: tuple[int, ...]


class RequestSpecificationService:
    def __init__(self, file_service: FileService | None = None):
        self._files = file_service or FileService()

    @staticmethod
    def _filename(request_id: str | None) -> str:
        number = (request_id or "").strip()
        if not number:
            raise Conflict("Укажите номер заявки перед подготовкой спецификации.")
        safe_number = "".join(
            "_" if character in '<>:"/\\|?*' or unicodedata.category(character).startswith("C") else character
            for character in unicodedata.normalize("NFKC", number)
        )[:200]
        return f"Заявка на закупку {safe_number}.docx"

    @staticmethod
    def ensure_sources_allowed(current_user: CurrentUser, sources: list[PreparedUpload]) -> None:
        UserPolicy.ensure_can_create_request(current_user)
        if current_user.role_id == settings.contractor_role_id:
            raise Forbidden("Контрагент не может загружать исходные договоры.")
        if not 1 <= len(sources) <= MAX_SOURCE_FILES:
            raise Conflict(f"Прикрепите от 1 до {MAX_SOURCE_FILES} исходных файлов.")
        if sum(source.size_bytes for source in sources) > 15 * 1024 * 1024:
            raise Conflict("Общий размер исходных файлов не должен превышать 15 МБ.")

    @staticmethod
    def _extraction_indices(sources: list[PreparedUpload], indices: list[int] | None) -> list[int]:
        selected = list(range(len(sources))) if indices is None else indices
        if (not selected or any(type(index) is not int or index < 0 or index >= len(sources) for index in selected)
                or len(set(selected)) != len(selected)):
            raise Conflict("Выберите файлы для формирования заявки среди прикреплённых исходников.")
        return sorted(selected)

    async def prepare(self, *, current_user: CurrentUser, request_id: str, sources: list[PreparedUpload],
                      extraction_indices: list[int] | None = None,
                      public_source_indices: list[int] | None = None) -> SpecificationPreview:
        self.ensure_sources_allowed(current_user, sources)
        filename = self._filename(request_id)
        selected = self._extraction_indices(sources, extraction_indices)
        public_sources = self._extraction_indices(sources, public_source_indices) if public_source_indices else []
        payload = [{"name": sources[index].original_name, "content": base64.b64encode(sources[index].content_bytes).decode("ascii")}
                   for index in selected]
        result = await run_in_threadpool(self._parse, payload)
        specification = await self._files.prepare_bytes(
            original_name=filename,
            content_bytes=base64.b64decode(result["content"], validate=True),
            mime_type=DOCX_MIME,
        )
        claims = {
            "v": CONFIRMATION_VERSION, "user": current_user.user_id, "expires": int(time.time()) + TOKEN_TTL,
            "sources": self._source_manifest(sources), "specification": specification.content_sha256,
            "request_id": request_id.strip(), "filename": specification.original_name,
            "extraction_indices": selected,
            "public_source_indices": public_sources,
        }
        encoded = base64.urlsafe_b64encode(json.dumps(claims, separators=(",", ":")).encode()).decode()
        return SpecificationPreview(specification, f"{encoded}.{self._signature(encoded)}", result["item_count"], result["used_ocr"])

    @staticmethod
    def _parse(payload: list[dict[str, str]]) -> dict:
        if not _PARSER_SLOTS.acquire(blocking=False):
            raise Conflict("Обработка документов занята. Повторите попытку немного позже.")
        try:
            environment = {**os.environ, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
            completed = subprocess.run(
                [sys.executable, "-m", "app.infrastructure.specification_parser"],
                input=json.dumps(payload).encode("utf-8"), capture_output=True, timeout=120, check=True, env=environment,
            )
            result = json.loads(completed.stdout)
        except (subprocess.SubprocessError, OSError, ValueError) as exc:
            raise Conflict("Не удалось подготовить спецификацию за отведённое время. Разделите документ или загрузите более чёткий файл.") from exc
        finally:
            _PARSER_SLOTS.release()
        if "error" in result:
            raise Conflict(result["error"])
        return result

    def verify(self, *, current_user: CurrentUser, request_id: str | None, sources: list[PreparedUpload], specification: PreparedUpload,
               confirmation: str | None) -> VerifiedSpecification:
        self.ensure_sources_allowed(current_user, sources)
        try:
            if not confirmation or len(confirmation) > 8192:
                raise ValueError
            encoded, signature = confirmation.split(".")
            if not hmac.compare_digest(signature, self._signature(encoded)):
                raise ValueError
            claims = json.loads(base64.urlsafe_b64decode(encoded))
            extraction_indices = self._extraction_indices(sources, claims["extraction_indices"])
            public_sources = claims["public_source_indices"]
            if not isinstance(public_sources, list):
                raise ValueError
            if public_sources:
                self._extraction_indices(sources, public_sources)
            if (claims["v"] != CONFIRMATION_VERSION or claims["user"] != current_user.user_id or claims["expires"] < time.time()
                    or claims["sources"] != self._source_manifest(sources)
                    or claims["specification"] != specification.content_sha256
                    or claims["request_id"] != (request_id or "").strip()
                    or claims["filename"] != specification.original_name
                    or specification.original_name != self._filename(request_id) or specification.mime_type != DOCX_MIME):
                raise ValueError
        except (ValueError, KeyError, TypeError) as exc:
            raise Conflict("Файлы изменились или время подтверждения истекло. Подготовьте спецификацию повторно.") from exc
        return VerifiedSpecification(tuple(public_sources), tuple(extraction_indices))

    @staticmethod
    def _source_manifest(sources: list[PreparedUpload]) -> list[list[str]]:
        return [[source.original_name, source.content_sha256] for source in sources]

    @staticmethod
    def _signature(encoded: str) -> str:
        key = hmac.digest(settings.jwt_secret.encode(), b"acom:request-specification:v1", "sha256")
        return hmac.new(key, encoded.encode(), hashlib.sha256).hexdigest()
