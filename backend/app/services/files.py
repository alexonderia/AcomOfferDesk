from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.domain.exceptions import Conflict, NotFound, UploadRejected
from app.infrastructure.minio_client import MinioStorage, S3Error
from app.models.orm_models import File, StorageObject
from app.repositories.files import FileRepository
from app.services.file_upload_guard import FileUploadGuardService


logger = logging.getLogger(__name__)


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
        upload_guard: FileUploadGuardService | None = None,
    ) -> None:
        self._files = files
        self._storage = storage or MinioStorage()
        self._upload_guard = upload_guard or FileUploadGuardService()
        self._tracked_objects: list[tuple[str, str]] = []

    async def ensure_bucket_exists(self) -> None:
        await self._storage.ensure_bucket_exists(bucket=settings.s3_bucket)

    async def prepare_upload(self, upload: UploadFile) -> PreparedUpload:
        logger.info(
            "Receiving upload from HTTP request: filename=%s content_type=%s",
            upload.filename or "",
            upload.content_type or "application/octet-stream",
        )
        content_bytes = await self._read_upload_bytes(upload)
        return await self.prepare_bytes(
            original_name=upload.filename or "",
            content_bytes=content_bytes,
            mime_type=upload.content_type,
        )

    async def prepare_bytes(
        self,
        *,
        original_name: str,
        content_bytes: bytes,
        mime_type: str | None = None,
    ) -> PreparedUpload:
        logger.info(
            "Preparing upload bytes for validation: filename=%s size_bytes=%s claimed_mime=%s",
            original_name,
            len(content_bytes),
            (mime_type or "application/octet-stream").strip() or "application/octet-stream",
        )
        if len(content_bytes) == 0:
            logger.warning(
                "Upload contains no bytes and will be rejected by file guard: filename=%s claimed_mime=%s",
                original_name,
                (mime_type or "application/octet-stream").strip() or "application/octet-stream",
            )
        if len(content_bytes) > settings.max_upload_size_bytes:
            logger.warning(
                "Upload rejected before scan because size exceeds backend limit: filename=%s size_bytes=%s max_size_bytes=%s",
                original_name,
                len(content_bytes),
                settings.max_upload_size_bytes,
            )
            raise UploadRejected(reason_code="file_too_large", detail="Файл слишком большой.")
        guarded = await self._upload_guard.scan_bytes(
            original_name=original_name,
            content_bytes=content_bytes,
            content_type=mime_type,
        )
        safe_name = self._sanitize_filename(guarded.original_name)
        logger.info(
            "Upload prepared successfully: filename=%s size_bytes=%s mime_type=%s sha256_prefix=%s",
            safe_name,
            len(guarded.content_bytes),
            guarded.mime_type,
            _hash_prefix(guarded.content_sha256),
        )
        return PreparedUpload(
            original_name=safe_name,
            content_bytes=guarded.content_bytes,
            mime_type=guarded.mime_type,
            content_sha256=guarded.content_sha256,
        )

    async def create_request_file(self, *, request_id: str, upload: PreparedUpload) -> File:
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
            logger.info(
                "Cleaning up tracked storage object after failed flow: bucket=%s key=%s",
                bucket,
                key,
            )
            try:
                await self._storage.remove_object(bucket=bucket, key=key)
            except S3Error as exc:
                if not self._is_missing_object_error(exc):
                    raise

    async def _store(self, *, upload: PreparedUpload) -> File:
        if self._files is None:
            raise RuntimeError("File repository is not configured")

        logger.info(
            "Persisting prepared upload: filename=%s size_bytes=%s sha256_prefix=%s",
            upload.original_name,
            upload.size_bytes,
            _hash_prefix(upload.content_sha256),
        )
        await self._files.acquire_storage_object_lock(content_sha256=upload.content_sha256)
        storage_object = await self._files.get_storage_object_by_content_hash(
            content_sha256=upload.content_sha256,
            size_bytes=upload.size_bytes,
        )

        if storage_object is None:
            logger.info(
                "No existing storage object found; creating new object: sha256_prefix=%s",
                _hash_prefix(upload.content_sha256),
            )
            storage_object = await self._create_storage_object(upload=upload)
        else:
            logger.info(
                "Reusing existing storage object: storage_object_id=%s sha256_prefix=%s",
                storage_object.id,
                _hash_prefix(upload.content_sha256),
            )
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
        logger.info(
            "Uploading new storage object: bucket=%s key=%s size_bytes=%s mime_type=%s sha256_prefix=%s",
            storage_bucket,
            storage_key,
            upload.size_bytes,
            upload.mime_type,
            _hash_prefix(upload.content_sha256),
        )
        await self._storage.upload_object(
            bucket=storage_bucket,
            key=storage_key,
            content_bytes=upload.content_bytes,
            content_type=upload.mime_type,
        )
        self._tracked_objects.append((storage_bucket, storage_key))

        try:
            storage_object = await self._files.create_storage_object(
                storage_bucket=storage_bucket,
                storage_key=storage_key,
                content_sha256=upload.content_sha256,
                mime_type=upload.mime_type,
                size_bytes=upload.size_bytes,
            )
            logger.info(
                "Storage object metadata created: storage_object_id=%s bucket=%s key=%s",
                storage_object.id,
                storage_bucket,
                storage_key,
            )
            return storage_object
        except Exception:
            logger.exception(
                "Failed to create storage object metadata; removing uploaded object: bucket=%s key=%s",
                storage_bucket,
                storage_key,
            )
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
            logger.info(
                "Verified existing storage object content: storage_object_id=%s bucket=%s key=%s",
                storage_object.id,
                storage_object.storage_bucket,
                storage_object.storage_key,
            )
        except S3Error as exc:
            if not self._is_missing_object_error(exc):
                raise
            logger.warning(
                "Storage object metadata exists but content is missing; re-uploading: storage_object_id=%s bucket=%s key=%s",
                storage_object.id,
                storage_object.storage_bucket,
                storage_object.storage_key,
            )
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
    async def _read_upload_bytes(upload: UploadFile) -> bytes:
        max_size = settings.max_upload_size_bytes
        total_size = 0
        chunks: list[bytes] = []
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > max_size:
                logger.warning(
                    "Upload stream exceeded backend size limit while reading: filename=%s size_bytes=%s max_size_bytes=%s",
                    upload.filename or "",
                    total_size,
                    max_size,
                )
                raise UploadRejected(reason_code="file_too_large", detail="Файл слишком большой.")
            chunks.append(chunk)
        logger.info(
            "Upload stream read successfully: filename=%s size_bytes=%s",
            upload.filename or "",
            total_size,
        )
        return b"".join(chunks)

    @staticmethod
    def _is_missing_object_error(exc: S3Error) -> bool:
        return exc.code in {"NoSuchKey", "NoSuchObject", "NoSuchBucket"}


def _hash_prefix(value: str) -> str:
    return value[:12]
