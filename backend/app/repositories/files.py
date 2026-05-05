from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import delete, func, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.orm_models import File, MessageFile, NormativeFile, OfferFile, RequestFile, StorageObject


class FileRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def acquire_storage_object_lock(self, *, content_sha256: str) -> None:
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:content_sha256))"),
            {"content_sha256": content_sha256},
        )

    async def get_storage_object_by_content_hash(
        self,
        *,
        content_sha256: str,
        size_bytes: int,
    ) -> StorageObject | None:
        stmt = (
            select(StorageObject)
            .where(
                StorageObject.content_sha256 == content_sha256,
                StorageObject.size_bytes == size_bytes,
            )
            .order_by(StorageObject.id.asc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def create_storage_object(
        self,
        *,
        storage_bucket: str,
        storage_key: str,
        content_sha256: str,
        mime_type: str,
        size_bytes: int,
    ) -> StorageObject:
        storage_object = StorageObject(
            storage_bucket=storage_bucket,
            storage_key=storage_key,
            content_sha256=content_sha256,
            mime_type=mime_type,
            size_bytes=size_bytes,
        )
        self._session.add(storage_object)
        await self._session.flush()
        return storage_object

    async def delete_storage_object_by_id(self, *, storage_object_id: int) -> bool:
        stmt = delete(StorageObject).where(StorageObject.id == storage_object_id)
        result = await self._session.execute(stmt)
        return bool(result.rowcount)

    async def count_files_by_storage_object_id(self, *, storage_object_id: int) -> int:
        stmt = select(func.count(File.id)).where(File.id_storage_object == storage_object_id)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def create(self, *, storage_object_id: int, original_name: str) -> File:
        db_file = File(id_storage_object=storage_object_id, original_name=original_name)
        self._session.add(db_file)
        await self._session.flush()
        await self._session.refresh(db_file)
        return db_file

    async def get_normative_file_id(self, *, normative_id: int) -> int | None:
        stmt = select(NormativeFile.id_file).where(NormativeFile.id == normative_id)
        result = await self._session.execute(stmt)
        value = result.scalar_one_or_none()
        return int(value) if value is not None else None

    async def get_normative_file(self, *, normative_id: int) -> File | None:
        stmt = (
            select(File)
            .options(joinedload(File.storage_object))
            .join(NormativeFile, NormativeFile.id_file == File.id)
            .where(NormativeFile.id == normative_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_normative_file(self, *, normative_id: int, file_id: int) -> None:
        await self._session.execute(
            pg_insert(NormativeFile)
            .values(id=normative_id, id_file=file_id)
            .on_conflict_do_update(
                index_elements=[NormativeFile.id],
                set_={"id_file": file_id},
            )
        )

    async def count_links(self, *, file_id: int) -> int:
        request_count = await self._scalar_count(select(func.count(RequestFile.id)).where(RequestFile.id == file_id))
        offer_count = await self._scalar_count(select(func.count(OfferFile.id)).where(OfferFile.id == file_id))
        message_count = await self._scalar_count(select(func.count(MessageFile.id)).where(MessageFile.id == file_id))
        normative_count = await self._scalar_count(select(func.count(NormativeFile.id)).where(NormativeFile.id_file == file_id))
        return request_count + offer_count + message_count + normative_count

    async def delete_by_id(self, *, file_id: int) -> bool:
        stmt = delete(File).where(File.id == file_id)
        result = await self._session.execute(stmt)
        return bool(result.rowcount)

    async def get_by_id(self, file_id: int) -> File | None:
        stmt = (
            select(File)
            .options(joinedload(File.storage_object))
            .where(File.id == file_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_ids(self, *, file_ids: Sequence[int]) -> list[File]:
        if not file_ids:
            return []
        stmt = (
            select(File)
            .options(joinedload(File.storage_object))
            .where(File.id.in_(file_ids))
            .order_by(File.id.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def _scalar_count(self, stmt) -> int:
        result = await self._session.execute(stmt)
        return int(result.scalar_one())
