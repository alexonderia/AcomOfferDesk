from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.core.chat_upload_tokens import create_chat_upload_token, decode_chat_upload_token
from app.core.uow import UnitOfWork
from app.domain.exceptions import Forbidden, NotFound, Unauthorized
from app.domain.policies import CurrentUser
from app.services.files import FileService
from app.services.keycloak_admin import KeycloakAdminService
from app.services.offers import (
    AttachmentFileInput,
    ExistingAttachmentFileInput,
    OfferMessageAckResult,
    OfferMessageMutationResult,
    OfferService,
)


@dataclass(frozen=True, slots=True)
class ChatSyncSnapshot:
    chat_id: int
    last_message_id: int | None
    last_read_message_id: int | None
    last_read_at: object
    is_muted: bool
    is_archived: bool
    resync_required: bool


def build_offer_service(uow: UnitOfWork, *, file_service: FileService | None = None) -> OfferService:
    assert uow.requests is not None
    assert uow.offers is not None
    assert uow.chats is not None
    assert uow.files is not None
    assert uow.messages is not None
    assert uow.profiles is not None
    assert uow.company_contacts is not None
    assert uow.users is not None
    return OfferService(
        uow.requests,
        uow.offers,
        uow.chats,
        uow.files,
        uow.messages,
        uow.profiles,
        uow.company_contacts,
        uow.users,
        file_service=file_service,
        keycloak_admin=KeycloakAdminService(),
    )


class ChatRealtimeService:
    def __init__(self, *, uow_factory: type[UnitOfWork] = UnitOfWork) -> None:
        self._uow_factory = uow_factory

    async def upload_message_file(
        self,
        *,
        current_user: CurrentUser,
        offer_id: int,
        upload: AttachmentFileInput,
    ) -> dict:
        file_service: FileService | None = None
        try:
            async with self._uow_factory() as uow:
                file_service = FileService(uow.files)
                service = build_offer_service(uow, file_service=file_service)
                uploaded = await service.create_message_upload(
                    current_user=current_user,
                    offer_id=offer_id,
                    upload=upload,
                )
        except Exception:
            if file_service is not None:
                await file_service.cleanup_tracked_objects()
            raise

        upload_token = await create_chat_upload_token(
            file_id=uploaded.file_id,
            offer_id=offer_id,
            user_id=current_user.user_id,
        )
        return {
            "offer_id": offer_id,
            "file_id": uploaded.file_id,
            "name": uploaded.name,
            "path": uploaded.path,
            "upload_token": upload_token,
            "download_url": f"/api/v1/files/{uploaded.file_id}/download",
        }

    async def create_message(
        self,
        *,
        current_user: CurrentUser,
        offer_id: int,
        text: str,
        file_refs: Sequence[dict] | None = None,
    ) -> tuple[OfferMessageMutationResult, dict]:
        existing_file_refs = await self._validate_uploaded_files(
            current_user=current_user,
            offer_id=offer_id,
            file_refs=file_refs or [],
        )

        file_service: FileService | None = None
        try:
            async with self._uow_factory() as uow:
                file_service = FileService(uow.files)
                service = build_offer_service(uow, file_service=file_service)
                result = await service.create_message(
                    current_user=current_user,
                    offer_id=offer_id,
                    text=text,
                    existing_file_refs=existing_file_refs,
                )
                message_payload = await self._build_message_payload(
                    uow=uow,
                    offer_id=result.offer_id,
                    message_id=result.message_id,
                )
        except Exception:
            if file_service is not None:
                await file_service.cleanup_tracked_objects()
            raise

        return result, message_payload

    async def mark_read(
        self,
        *,
        current_user: CurrentUser,
        offer_id: int,
        message_ids: list[int] | None = None,
        up_to_message_id: int | None = None,
    ) -> OfferMessageAckResult:
        async with self._uow_factory() as uow:
            service = build_offer_service(uow)
            return await service.mark_messages_read(
                current_user=current_user,
                offer_id=offer_id,
                message_ids=message_ids,
                up_to_message_id=up_to_message_id,
            )

    async def sync_chat(
        self,
        *,
        current_user: CurrentUser,
        offer_id: int,
        last_known_message_id: int | None,
    ) -> ChatSyncSnapshot:
        async with self._uow_factory() as uow:
            service = build_offer_service(uow)
            chat_state = await service.get_chat_state(current_user=current_user, offer_id=offer_id)

        return ChatSyncSnapshot(
            chat_id=offer_id,
            last_message_id=chat_state.last_message_id,
            last_read_message_id=chat_state.last_read_message_id,
            last_read_at=chat_state.last_read_at,
            is_muted=chat_state.is_muted,
            is_archived=chat_state.is_archived,
            resync_required=chat_state.last_message_id != last_known_message_id,
        )

    async def load_message_payload(self, *, offer_id: int, message_id: int) -> dict:
        async with self._uow_factory() as uow:
            return await self._build_message_payload(uow=uow, offer_id=offer_id, message_id=message_id)

    async def mark_delivered_for_online_user(
        self,
        *,
        offer_id: int,
        user_id: str,
        message_ids: list[int] | None = None,
        up_to_message_id: int | None = None,
    ) -> OfferMessageAckResult:
        async with self._uow_factory() as uow:
            assert uow.chats is not None
            participant = await uow.chats.get_active_participant(chat_id=offer_id, user_id=user_id)
            if participant is None:
                return OfferMessageAckResult(offer_id=offer_id, chat_id=offer_id, updated_message_ids=[])

            assert uow.messages is not None
            updated_message_ids = await uow.messages.mark_delivered(
                chat_id=offer_id,
                recipient_user_id=user_id,
                message_ids=message_ids,
                up_to_message_id=up_to_message_id,
            )
            return OfferMessageAckResult(
                offer_id=offer_id,
                chat_id=offer_id,
                updated_message_ids=updated_message_ids,
            )

    async def _validate_uploaded_files(
        self,
        *,
        current_user: CurrentUser,
        offer_id: int,
        file_refs: Sequence[dict],
    ) -> list[ExistingAttachmentFileInput]:
        validated_refs: list[ExistingAttachmentFileInput] = []
        for file_ref in file_refs:
            token = str(file_ref.get("upload_token") or "").strip()
            file_id = int(file_ref.get("file_id") or 0)
            if file_id <= 0 or not token:
                raise Unauthorized("Invalid token payload")

            claims = await decode_chat_upload_token(token)
            if claims.offer_id != offer_id or claims.file_id != file_id:
                raise Unauthorized("Invalid token payload")
            if claims.user_id != current_user.user_id:
                raise Forbidden("Insufficient permissions to send chat message")

            async with self._uow_factory() as uow:
                assert uow.files is not None
                db_file = await uow.files.get_by_id(file_id)
                if db_file is None:
                    raise NotFound("File not found")

            validated_refs.append(ExistingAttachmentFileInput(file_id=file_id))
        return validated_refs

    async def _build_message_payload(self, *, uow: UnitOfWork, offer_id: int, message_id: int) -> dict:
        assert uow.messages is not None
        assert uow.profiles is not None

        message = await uow.messages.get_by_id(message_id=message_id)
        if message is None:
            raise NotFound("Message not found")

        attachments = []
        for _, db_file in await uow.messages.list_files_by_message_ids(message_ids=[message_id]):
            attachments.append(
                {
                    "id": db_file.id,
                    "path": db_file.path,
                    "name": db_file.name,
                    "download_url": f"/api/v1/files/{db_file.id}/download",
                }
            )

        profile = await uow.profiles.get_by_id(message.id_user)
        return {
            "chat_id": offer_id,
            "message": {
                "id": message.id,
                "offer_id": offer_id,
                "user_id": message.id_user,
                "user_full_name": profile.full_name if profile else None,
                "text": message.text,
                "type": message.type,
                "status": "send",
                "created_at": message.created_at.isoformat(),
                "updated_at": message.updated_at.isoformat(),
                "read_by": [],
                "attachments": attachments,
            },
        }
