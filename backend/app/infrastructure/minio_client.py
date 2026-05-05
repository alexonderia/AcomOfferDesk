from __future__ import annotations

import io
from datetime import timedelta
from urllib.parse import urlsplit, urlunsplit

import anyio
from minio import Minio
from minio.error import S3Error

from app.core.config import settings


class MinioStorage:
    def __init__(self) -> None:
        self._client = Minio(
            endpoint=settings.s3_endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            secure=settings.s3_secure,
        )

    async def ensure_bucket_exists(self, *, bucket: str) -> None:
        exists = await anyio.to_thread.run_sync(self._client.bucket_exists, bucket)
        if not exists:
            try:
                await anyio.to_thread.run_sync(self._client.make_bucket, bucket)
            except S3Error as exc:
                if exc.code != "BucketAlreadyOwnedByYou":
                    raise

    async def upload_object(
        self,
        *,
        bucket: str,
        key: str,
        content_bytes: bytes,
        content_type: str,
    ) -> None:
        await anyio.to_thread.run_sync(
            self._put_object,
            bucket,
            key,
            content_bytes,
            content_type,
        )

    def _put_object(self, bucket: str, key: str, content_bytes: bytes, content_type: str) -> None:
        data = io.BytesIO(content_bytes)
        self._client.put_object(
            bucket_name=bucket,
            object_name=key,
            data=data,
            length=len(content_bytes),
            content_type=content_type,
        )

    async def remove_object(self, *, bucket: str, key: str) -> None:
        await anyio.to_thread.run_sync(self._client.remove_object, bucket, key)

    async def stat_object(self, *, bucket: str, key: str):
        return await anyio.to_thread.run_sync(self._client.stat_object, bucket, key)

    async def get_object_bytes(self, *, bucket: str, key: str) -> bytes:
        return await anyio.to_thread.run_sync(self._read_object, bucket, key)

    def _read_object(self, bucket: str, key: str) -> bytes:
        response = self._client.get_object(bucket, key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    async def generate_presigned_get_url(
        self,
        *,
        bucket: str,
        key: str,
        ttl_seconds: int,
    ) -> str:
        return await anyio.to_thread.run_sync(
            self._presigned_get_object,
            bucket,
            key,
            ttl_seconds,
        )

    def _presigned_get_object(self, bucket: str, key: str, ttl_seconds: int) -> str:
        presigned_url = self._client.presigned_get_object(
            bucket_name=bucket,
            object_name=key,
            expires=timedelta(seconds=ttl_seconds),
        )
        if not settings.s3_public_endpoint:
            return presigned_url

        parsed = urlsplit(presigned_url)
        public_endpoint = settings.s3_public_endpoint.strip()
        if "://" in public_endpoint:
            public_parts = urlsplit(public_endpoint)
            scheme = public_parts.scheme or parsed.scheme
            netloc = public_parts.netloc
        else:
            scheme = parsed.scheme
            netloc = public_endpoint
        return urlunsplit((scheme, netloc, parsed.path, parsed.query, parsed.fragment))


__all__ = ["MinioStorage", "S3Error"]
