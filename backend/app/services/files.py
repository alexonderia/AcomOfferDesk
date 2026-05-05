from __future__ import annotations

import hashlib
import io
import mimetypes
import zipfile
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.domain.exceptions import Conflict, NotFound
from app.infrastructure.minio_client import MinioStorage, S3Error
from app.models.orm_models import File, StorageObject
from app.repositories.files import FileRepository

_ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".txt",
    ".md",
    ".doc",
    ".docx",
    ".docs",
    ".xls",
    ".xlsx",
    ".exl",
    ".csv",
    ".ods",
}
_DANGEROUS_EXTENSIONS = {".exe", ".sh", ".bat", ".cmd", ".ps1", ".js", ".msi", ".dll", ".so", ".jar"}


@dataclass(frozen=True, slots=True)
class PreparedUpload:
    original_name: str
    content_bytes: bytes
    mime_type: str
    content_sha256: str

    @property
    def size_bytes(self) -> int:
        return len(self.content_bytes)


class FileService:
    def __init__(
        self,
        files: FileRepository | None = None,
        *,
        storage: MinioStorage | None = None,
    ) -> None:
        self._files = files
        self._storage = storage or MinioStorage()
        self._tracked_objects: list[tuple[str, str]] = []

    async def ensure_bucket_exists(self) -> None:
        await self._storage.ensure_bucket_exists(bucket=settings.s3_bucket)

    async def prepare_upload(self, upload: UploadFile) -> PreparedUpload:
        return await self.prepare_bytes(
            original_name=upload.filename or "",
            content_bytes=await upload.read(),
            mime_type=upload.content_type,
        )

    async def prepare_bytes(
        self,
        *,
        original_name: str,
        content_bytes: bytes,
        mime_type: str | None = None,
    ) -> PreparedUpload:
        safe_name = self._sanitize_filename(original_name)
        extension = Path(safe_name).suffix.lower()

        if extension in _DANGEROUS_EXTENSIONS:
            raise Conflict("Forbidden file type")
        if extension not in _ALLOWED_EXTENSIONS:
            raise Conflict("Unsupported file extension")
        if not content_bytes:
            raise Conflict("File cannot be empty")
        if len(content_bytes) > settings.max_upload_size_bytes:
            raise Conflict("File too large")
        if not self._magic_signature_matches(extension=extension, content=content_bytes):
            raise Conflict("File content does not match extension")

        detected_mime_type = (mime_type or mimetypes.guess_type(safe_name)[0] or "application/octet-stream").strip()
        return PreparedUpload(
            original_name=safe_name,
            content_bytes=content_bytes,
            mime_type=detected_mime_type or "application/octet-stream",
            content_sha256=hashlib.sha256(content_bytes).hexdigest(),
        )

    async def create_request_file(self, *, request_id: int, upload: PreparedUpload) -> File:
        _ = request_id
        return await self._store(upload=upload)

    async def create_offer_file(self, *, offer_id: int, upload: PreparedUpload) -> File:
        _ = offer_id
        return await self._store(upload=upload)

    async def create_chat_temp_file(self, *, offer_id: int, upload: PreparedUpload) -> File:
        _ = offer_id
        return await self._store(upload=upload)

    async def create_chat_message_file(self, *, offer_id: int, upload: PreparedUpload) -> File:
        _ = offer_id
        return await self._store(upload=upload)

    async def create_normative_file(self, *, upload: PreparedUpload) -> File:
        return await self._store(upload=upload)

    async def build_download_url(self, *, db_file: File) -> str:
        storage_object = self._require_storage_object(db_file)
        try:
            await self._storage.stat_object(bucket=storage_object.storage_bucket, key=storage_object.storage_key)
        except S3Error as exc:
            if self._is_missing_object_error(exc):
                raise NotFound("File content not found") from exc
            raise
        return await self._storage.generate_presigned_get_url(
            bucket=storage_object.storage_bucket,
            key=storage_object.storage_key,
            ttl_seconds=settings.s3_presigned_get_ttl_seconds,
        )

    async def read_bytes(self, *, db_file: File) -> bytes:
        storage_object = self._require_storage_object(db_file)
        try:
            return await self._storage.get_object_bytes(
                bucket=storage_object.storage_bucket,
                key=storage_object.storage_key,
            )
        except S3Error as exc:
            if self._is_missing_object_error(exc):
                raise NotFound("File content not found") from exc
            raise

    async def delete_file(self, *, file_id: int) -> None:
        if self._files is None:
            raise RuntimeError("File repository is not configured")

        db_file = await self._files.get_by_id(file_id)
        if db_file is None:
            raise NotFound("File not found")

        storage_object = self._require_storage_object(db_file)
        deleted = await self._files.delete_by_id(file_id=file_id)
        if not deleted:
            raise NotFound("File not found")

        remaining_refs = await self._files.count_files_by_storage_object_id(storage_object_id=storage_object.id)
        if remaining_refs > 0:
            return

        try:
            await self._storage.remove_object(
                bucket=storage_object.storage_bucket,
                key=storage_object.storage_key,
            )
        except S3Error as exc:
            if not self._is_missing_object_error(exc):
                raise

        await self._files.delete_storage_object_by_id(storage_object_id=storage_object.id)

    async def cleanup_tracked_objects(self) -> None:
        while self._tracked_objects:
            bucket, key = self._tracked_objects.pop()
            try:
                await self._storage.remove_object(bucket=bucket, key=key)
            except S3Error as exc:
                if not self._is_missing_object_error(exc):
                    raise

    async def _store(self, *, upload: PreparedUpload) -> File:
        if self._files is None:
            raise RuntimeError("File repository is not configured")

        await self._files.acquire_storage_object_lock(content_sha256=upload.content_sha256)
        storage_object = await self._files.get_storage_object_by_content_hash(
            content_sha256=upload.content_sha256,
            size_bytes=upload.size_bytes,
        )

        if storage_object is None:
            storage_object = await self._create_storage_object(upload=upload)
        else:
            await self._ensure_storage_object_content(storage_object=storage_object, upload=upload)

        return await self._files.create(
            storage_object_id=storage_object.id,
            original_name=upload.original_name,
        )

    async def _create_storage_object(self, *, upload: PreparedUpload) -> StorageObject:
        if self._files is None:
            raise RuntimeError("File repository is not configured")

        storage_bucket = settings.s3_bucket
        storage_key = f"objects/{upload.content_sha256}"
        await self._storage.upload_object(
            bucket=storage_bucket,
            key=storage_key,
            content_bytes=upload.content_bytes,
            content_type=upload.mime_type,
        )
        self._tracked_objects.append((storage_bucket, storage_key))

        try:
            return await self._files.create_storage_object(
                storage_bucket=storage_bucket,
                storage_key=storage_key,
                content_sha256=upload.content_sha256,
                mime_type=upload.mime_type,
                size_bytes=upload.size_bytes,
            )
        except Exception:
            try:
                await self._storage.remove_object(bucket=storage_bucket, key=storage_key)
            except S3Error as exc:
                if not self._is_missing_object_error(exc):
                    raise
            self._tracked_objects = [
                item for item in self._tracked_objects
                if item != (storage_bucket, storage_key)
            ]
            raise

    async def _ensure_storage_object_content(
        self,
        *,
        storage_object: StorageObject,
        upload: PreparedUpload,
    ) -> None:
        try:
            await self._storage.stat_object(
                bucket=storage_object.storage_bucket,
                key=storage_object.storage_key,
            )
        except S3Error as exc:
            if not self._is_missing_object_error(exc):
                raise
            await self._storage.upload_object(
                bucket=storage_object.storage_bucket,
                key=storage_object.storage_key,
                content_bytes=upload.content_bytes,
                content_type=storage_object.mime_type,
            )

    @staticmethod
    def _require_storage_object(db_file: File) -> StorageObject:
        storage_object = getattr(db_file, "storage_object", None)
        if storage_object is None:
            raise NotFound("File content not found")
        return storage_object

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        basename = Path(filename).name.strip()
        if not basename:
            raise Conflict("File name is required")
        if basename != filename.strip():
            raise Conflict("Unsafe file name")
        return basename

    @staticmethod
    def _is_zip_based_office_document(*, content: bytes, required_entry: str) -> bool:
        if not content.startswith(b"PK\x03\x04"):
            return False
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                names = set(archive.namelist())
                return required_entry in names
        except zipfile.BadZipFile:
            return False

    @classmethod
    def _magic_signature_matches(cls, *, extension: str, content: bytes) -> bool:
        if extension == ".pdf":
            return content.startswith(b"%PDF-")
        if extension == ".png":
            return content.startswith(b"\x89PNG\r\n\x1a\n")
        if extension in {".jpg", ".jpeg"}:
            return content.startswith(b"\xff\xd8\xff")
        if extension in {".txt", ".md", ".csv"}:
            try:
                content.decode("utf-8")
            except UnicodeDecodeError:
                return False
            return True
        if extension in {".doc", ".docs", ".xls", ".exl"}:
            return content.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")
        if extension == ".docx":
            return cls._is_zip_based_office_document(content=content, required_entry="word/document.xml")
        if extension == ".xlsx":
            return cls._is_zip_based_office_document(content=content, required_entry="xl/workbook.xml")
        if extension == ".ods":
            if not content.startswith(b"PK\x03\x04"):
                return False
            try:
                with zipfile.ZipFile(io.BytesIO(content)) as archive:
                    names = set(archive.namelist())
                    if "mimetype" in names:
                        mimetype = archive.read("mimetype")
                        if mimetype == b"application/vnd.oasis.opendocument.spreadsheet":
                            return True
                    return "content.xml" in names
            except (zipfile.BadZipFile, KeyError):
                return False
        return False

    @staticmethod
    def _is_missing_object_error(exc: S3Error) -> bool:
        return exc.code in {"NoSuchKey", "NoSuchObject", "NoSuchBucket"}
