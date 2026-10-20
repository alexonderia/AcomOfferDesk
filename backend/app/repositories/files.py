from __future__ import annotations

from collections.abc import Sequence

from dataclasses import dataclass

from sqlalchemy import delete, func, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.orm_models import File, MessageFile, NormativeFile, OfferFile, RequestFile, StorageObject


@dataclass(frozen=True, slots=True)
class NormativeFileListRow:
    id: int
    file_id: int
    original_name: str
    status: str
    created_at: str


class FileRepository:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._normative_status_column_cache: bool | None = None

    async def _normative_status_column_supported(self) -> bool:
        if self._normative_status_column_cache is not None:
            return self._normative_status_column_cache
        result = await self._session.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'normative_files'
                      AND column_name IN ('document_status', 'status')
                )
                """
            )
        )
        self._normative_status_column_cache = bool(result.scalar_one())
        return self._normative_status_column_cache

    @staticmethod
    def _normalize_normative_status(value: str | None) -> str:
        if value in {"actual", "outdated"}:
            return value
        if value == "archived":
            return "outdated"
        return "actual"

    async def acquire_storage_object_lock(self, *, content_sha256: str) -> None:
        await self._acquire_transaction_lock(lock_key=content_sha256)

    async def acquire_normative_file_name_lock(self, *, original_name: str) -> None:
        await self._acquire_transaction_lock(lock_key=f"normative-name:{original_name}")

    async def acquire_normative_file_id_allocation_lock(self) -> None:
        await self._acquire_transaction_lock(lock_key="normative-id-allocation")

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

    async def find_normative_file_id_by_original_name(
        self,
        *,
        original_name: str,
    ) -> int | None:
        stmt = (
            select(NormativeFile.id)
            .join(File, File.id == NormativeFile.id_file)
            .where(File.original_name == original_name)
            .order_by(NormativeFile.id.asc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        value = result.scalar_one_or_none()
        return int(value) if value is not None else None

    async def get_normative_file_status(self, *, normative_id: int) -> str | None:
        file_id = await self.get_normative_file_id(normative_id=normative_id)
        if file_id is None:
            return None
        if not await self._normative_status_column_supported():
            return "actual"

        stmt = select(NormativeFile.status).where(NormativeFile.id == normative_id)
        result = await self._session.execute(stmt)
        value = result.scalar_one_or_none()
        if value is None:
            return None
        return self._normalize_normative_status(str(value))

    async def list_normative_files(self, *, status: str | None = None) -> list[NormativeFileListRow]:
        normalized_status = self._normalize_normative_status(status) if status is not None else None
        if not await self._normative_status_column_supported():
            if normalized_status is not None and normalized_status != "actual":
                return []
            stmt = (
                select(
                    NormativeFile.id,
                    NormativeFile.id_file,
                    File.original_name,
                    File.created_at,
                )
                .join(File, File.id == NormativeFile.id_file)
                .order_by(NormativeFile.id.desc())
            )
            result = await self._session.execute(stmt)
            return [
                NormativeFileListRow(
                    id=int(row.id),
                    file_id=int(row.id_file),
                    original_name=row.original_name,
                    status="actual",
                    created_at=str(row.created_at),
                )
                for row in result.all()
            ]

        stmt = (
            select(
                NormativeFile.id,
                NormativeFile.id_file,
                NormativeFile.status,
                File.original_name,
                File.created_at,
            )
            .join(File, File.id == NormativeFile.id_file)
            .order_by(NormativeFile.id.desc())
        )
        if normalized_status is not None:
            legacy_status = "archived" if normalized_status == "outdated" else normalized_status
            stmt = stmt.where(NormativeFile.status.in_([normalized_status, legacy_status]))
        result = await self._session.execute(stmt)
        rows = [
            NormativeFileListRow(
                id=int(row.id),
                file_id=int(row.id_file),
                original_name=row.original_name,
                status=self._normalize_normative_status(row.status),
                created_at=str(row.created_at),
            )
            for row in result.all()
        ]
        if normalized_status is None:
            return rows
        return [row for row in rows if row.status == normalized_status]

    async def supports_normative_status_column(self) -> bool:
        return await self._normative_status_column_supported()

    async def get_normative_file_row(self, *, normative_id: int) -> NormativeFileListRow | None:
        if not await self._normative_status_column_supported():
            stmt = (
                select(
                    NormativeFile.id,
                    NormativeFile.id_file,
                    File.original_name,
                    File.created_at,
                )
                .join(File, File.id == NormativeFile.id_file)
                .where(NormativeFile.id == normative_id)
                .limit(1)
            )
            result = await self._session.execute(stmt)
            row = result.first()
            if row is None:
                return None
            return NormativeFileListRow(
                id=int(row.id),
                file_id=int(row.id_file),
                original_name=row.original_name,
                status="actual",
                created_at=str(row.created_at),
            )

        stmt = (
            select(
                NormativeFile.id,
                NormativeFile.id_file,
                NormativeFile.status,
                File.original_name,
                File.created_at,
            )
            .join(File, File.id == NormativeFile.id_file)
            .where(NormativeFile.id == normative_id)
            .limit(1)
        )
        result = await self._session.execute(stmt)
        row = result.first()
        if row is None:
            return None
        return NormativeFileListRow(
            id=int(row.id),
            file_id=int(row.id_file),
            original_name=row.original_name,
            status=self._normalize_normative_status(row.status),
            created_at=str(row.created_at),
        )

    async def get_next_normative_file_id(self) -> int:
        stmt = select(func.coalesce(func.max(NormativeFile.id), 0))
        result = await self._session.execute(stmt)
        current_max = int(result.scalar_one())
        return current_max + 1

    async def create_normative_file_record(
        self,
        *,
        normative_id: int,
        file_id: int,
        status: str = "actual",
    ) -> None:
        normalized_status = self._normalize_normative_status(status)
        if await self._normative_status_column_supported():
            self._session.add(
                NormativeFile(
                    id=normative_id,
                    id_file=file_id,
                    status=normalized_status,
                )
            )
        else:
            await self._session.execute(
                text("INSERT INTO normative_files (id, id_file) VALUES (:id, :file_id)"),
                {"id": normative_id, "file_id": file_id},
            )
        await self._session.flush()

    async def update_normative_file_status(self, *, normative_id: int, status: str) -> bool:
        if not await self._normative_status_column_supported():
            return False

        normalized_status = self._normalize_normative_status(status)
        stmt = (
            update(NormativeFile)
            .where(NormativeFile.id == normative_id)
            .values(status=normalized_status)
        )
        result = await self._session.execute(stmt)
        return bool(result.rowcount)

    async def get_normative_file(self, *, normative_id: int) -> File | None:
        stmt = (
            select(File)
            .options(joinedload(File.storage_object))
            .join(NormativeFile, NormativeFile.id_file == File.id)
            .where(NormativeFile.id == normative_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_normative_file(self, *, normative_id: int, file_id: int, status: str = "actual") -> None:
        normalized_status = self._normalize_normative_status(status)
        if await self._normative_status_column_supported():
            await self._session.execute(
                pg_insert(NormativeFile)
                .values(id=normative_id, id_file=file_id, status=normalized_status)
                .on_conflict_do_update(
                    index_elements=[NormativeFile.id],
                    set_={"id_file": file_id},
                )
            )
            return

        await self._session.execute(
            text(
                """
                INSERT INTO normative_files (id, id_file)
                VALUES (:id, :file_id)
                ON CONFLICT (id) DO UPDATE SET id_file = EXCLUDED.id_file
                """
            ),
            {"id": normative_id, "file_id": file_id},
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

    async def is_normative_file(self, *, file_id: int) -> bool:
        stmt = select(NormativeFile.id).where(NormativeFile.id_file == file_id).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

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

    async def _acquire_transaction_lock(self, *, lock_key: str) -> None:
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
            {"lock_key": lock_key},
        )
