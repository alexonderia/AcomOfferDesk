from __future__ import annotations

import logging
from dataclasses import dataclass
from email.utils import parseaddr

from app.core.config import settings
from app.core.uow import UnitOfWork
from app.infrastructure.email.imap_inbox_service import IMAPInboxService, InboxEmail
from app.infrastructure.email.reply_token_codec import ReplyTokenCodec
from app.repositories.messages import (
    AUTO_EMAIL_OFFER_CREATED_TEXT,
    build_auto_email_content,
    build_email_message_text,
)
from app.services.files import FileService

logger = logging.getLogger("gunicorn.error")


@dataclass(slots=True, frozen=True)
class ReplyProcessingResult:
    processed_emails: int
    created_offers: int
    created_messages: int
    saved_files: int
    skipped_emails: int


class ProcessRequestReplyUseCase:
    def __init__(
        self,
        *,
        uow_factory: type[UnitOfWork] = UnitOfWork,
        inbox_service: IMAPInboxService,
        reply_token_codec: ReplyTokenCodec,
    ) -> None:
        self._uow_factory = uow_factory
        self._inbox_service = inbox_service
        self._reply_token_codec = reply_token_codec

    @classmethod
    def from_settings(cls) -> "ProcessRequestReplyUseCase":
        if not settings.imap_host:
            raise ValueError("IMAP host is not configured")
        if not settings.imap_username or not settings.imap_password:
            raise ValueError("IMAP credentials are not configured")
        if not settings.reply_email_token_secret:
            raise ValueError("Reply token secret is not configured")

        inbox_service = IMAPInboxService(
            host=settings.imap_host,
            port=settings.imap_port,
            username=settings.imap_username,
            password=settings.imap_password,
            mailbox=settings.imap_mailbox,
            poll_limit=settings.request_mailbox_poll_limit,
        )
        token_codec = ReplyTokenCodec(secret=settings.reply_email_token_secret)
        return cls(
            inbox_service=inbox_service,
            reply_token_codec=token_codec,
        )

    async def execute(self) -> ReplyProcessingResult:
        emails = await self._inbox_service.read_unseen()
        logger.info("Reply processing poll started: fetched_emails=%s", len(emails))

        created_offers = 0
        created_messages = 0
        saved_files = 0
        skipped_emails = 0

        for incoming in emails:
            logger.info(
                "Processing inbound email: uid=%s message_id=%s from=%s subject=%s text_len=%s attachments=%s",
                incoming.uid,
                incoming.message_id,
                incoming.from_email,
                incoming.subject,
                len(incoming.text or ""),
                len(incoming.attachments),
            )
            try:
                processed, offer_created, message_created, attached_files = await self._process_single_email(incoming)
            except Exception:
                skipped_emails += 1
                logger.exception(
                    "Inbound email processing failed with exception: uid=%s message_id=%s from=%s",
                    incoming.uid,
                    incoming.message_id,
                    incoming.from_email,
                )
                continue

            if not processed:
                skipped_emails += 1
                continue
            if offer_created:
                created_offers += 1
            if message_created:
                created_messages += 1
            saved_files += attached_files

        result = ReplyProcessingResult(
            processed_emails=len(emails) - skipped_emails,
            created_offers=created_offers,
            created_messages=created_messages,
            saved_files=saved_files,
            skipped_emails=skipped_emails,
        )
        logger.info(
            "Reply processing poll finished: processed=%s skipped=%s offers=%s messages=%s files=%s",
            result.processed_emails,
            result.skipped_emails,
            result.created_offers,
            result.created_messages,
            result.saved_files,
        )
        return result

    async def _process_single_email(self, incoming: InboxEmail) -> tuple[bool, bool, bool, int]:
        if not incoming.message_id:
            logger.info("Skip email: empty Message-ID uid=%s from=%s", incoming.uid, incoming.from_email)
            return False, False, False, 0

        from_email = parseaddr(incoming.from_email)[1].strip().lower()
        if not from_email:
            logger.info(
                "Skip email: cannot parse sender address uid=%s raw_from=%s message_id=%s",
                incoming.uid,
                incoming.from_email,
                incoming.message_id,
            )
            return False, False, False, 0

        reply_token = await self._reply_token_codec.extract_token_from_email(incoming.message)
        if not reply_token:
            logger.info(
                "Skip email: reply token not found uid=%s message_id=%s subject=%s",
                incoming.uid,
                incoming.message_id,
                incoming.subject,
            )
            return False, False, False, 0

        claims = await self._reply_token_codec.parse_token(reply_token)
        logger.info(
            "Reply token decoded: uid=%s message_id=%s request_id=%s user_id=%s",
            incoming.uid,
            incoming.message_id,
            claims.request_id,
            claims.user_id,
        )

        async with self._uow_factory() as uow:
            assert uow.profiles is not None
            assert uow.messages is not None
            assert uow.offers is not None
            assert uow.requests is not None
            assert uow.files is not None
            file_service = FileService(uow.files)
            try:
                duplicate = await uow.messages.exists_with_email_message_id(email_message_id=incoming.message_id)
                if duplicate:
                    logger.info(
                        "Skip email: duplicate Message-ID already exists uid=%s message_id=%s",
                        incoming.uid,
                        incoming.message_id,
                    )
                    return False, False, False, 0

                contractor_profile = await uow.profiles.get_active_contractor_by_mail(
                    email=from_email,
                    contractor_role_id=settings.contractor_role_id,
                )
                if contractor_profile is None:
                    logger.info(
                        "Skip email: contractor profile not found or inactive uid=%s message_id=%s sender=%s",
                        incoming.uid,
                        incoming.message_id,
                        from_email,
                    )
                    return False, False, False, 0

                if contractor_profile.id != claims.user_id:
                    logger.info(
                        "Skip email: token user mismatch uid=%s message_id=%s sender_user_id=%s token_user_id=%s",
                        incoming.uid,
                        incoming.message_id,
                        contractor_profile.id,
                        claims.user_id,
                    )
                    return False, False, False, 0

                request = await uow.requests.get_by_id(request_id=claims.request_id)
                if request is None:
                    logger.info(
                        "Skip email: request not found uid=%s message_id=%s request_id=%s",
                        incoming.uid,
                        incoming.message_id,
                        claims.request_id,
                    )
                    return False, False, False, 0

                if await uow.requests.is_hidden_for_contractor(
                    request_id=claims.request_id,
                    contractor_user_id=contractor_profile.id,
                ):
                    logger.info(
                        "Skip email: request is hidden for contractor uid=%s message_id=%s request_id=%s contractor_id=%s",
                        incoming.uid,
                        incoming.message_id,
                        claims.request_id,
                        contractor_profile.id,
                    )
                    return False, False, False, 0

                offer = await uow.offers.get_contractor_offer_for_request(
                    request_id=claims.request_id,
                    contractor_user_id=contractor_profile.id,
                )

                is_new_offer = offer is None
                if is_new_offer:
                    offer = await uow.offers.create(
                        request_id=claims.request_id,
                        contractor_user_id=contractor_profile.id,
                    )
                    logger.info(
                        "Created new offer from email: uid=%s message_id=%s offer_id=%s request_id=%s contractor_id=%s",
                        incoming.uid,
                        incoming.message_id,
                        offer.id,
                        claims.request_id,
                        contractor_profile.id,
                    )
                else:
                    logger.info(
                        "Using existing offer for email: uid=%s message_id=%s offer_id=%s",
                        incoming.uid,
                        incoming.message_id,
                        offer.id,
                    )

                assert offer is not None
                files_saved = 0
                message_created = False

                if is_new_offer:
                    await uow.messages.create(
                        chat_id=offer.id,
                        user_id=contractor_profile.id,
                        text=AUTO_EMAIL_OFFER_CREATED_TEXT,
                        message_type="system",
                    )
                    logger.info(
                        "Created system auto-offer message: uid=%s message_id=%s chat_id=%s",
                        incoming.uid,
                        incoming.message_id,
                        offer.id,
                    )
                    message_created = True

                    email_text = build_auto_email_content(text=incoming.text)
                    if incoming.text.strip():
                        message = await uow.messages.create(
                            chat_id=offer.id,
                            user_id=contractor_profile.id,
                            text=build_email_message_text(text=email_text, message_id=incoming.message_id),
                            message_type="email",
                        )
                        logger.info(
                            "Created initial message for new offer: uid=%s message_id=%s chat_id=%s message_id_db=%s",
                            incoming.uid,
                            incoming.message_id,
                            offer.id,
                            message.id,
                        )
                    elif incoming.attachments:
                        logger.info(
                            "Attachment-only email for new offer: skip extra text message uid=%s message_id=%s chat_id=%s",
                            incoming.uid,
                            incoming.message_id,
                            offer.id,
                        )
                    else:
                        logger.info(
                            "New offer created with system message only: empty text and no attachments uid=%s message_id=%s",
                            incoming.uid,
                            incoming.message_id,
                        )

                    for attachment in incoming.attachments:
                        prepared = await file_service.prepare_bytes(
                            original_name=attachment.original_name,
                            content_bytes=attachment.content_bytes,
                            mime_type=attachment.content_type,
                        )
                        db_file = await file_service.create_offer_file(
                            offer_id=offer.id,
                            upload=prepared,
                        )
                        await uow.offers.attach_file(offer_id=offer.id, file_id=db_file.id)
                        logger.info(
                            "Attached file to offer: uid=%s message_id=%s offer_id=%s file_id=%s file_name=%s storage_key=%s bytes=%s",
                            incoming.uid,
                            incoming.message_id,
                            offer.id,
                            db_file.id,
                            attachment.original_name,
                            db_file.storage_key,
                            len(attachment.content_bytes),
                        )
                        files_saved += 1

                    return True, True, message_created, files_saved

                if not incoming.text.strip() and not incoming.attachments:
                    logger.info(
                        "Skip email for existing offer: empty text and no attachments uid=%s message_id=%s offer_id=%s",
                        incoming.uid,
                        incoming.message_id,
                        offer.id,
                    )
                    return False, False, False, 0

                message_text = build_email_message_text(
                    text=build_auto_email_content(text=incoming.text),
                    message_id=incoming.message_id,
                )
                message = await uow.messages.create(
                    chat_id=offer.id,
                    user_id=contractor_profile.id,
                    text=message_text,
                    message_type="email",
                )
                logger.info(
                    "Created message in existing offer chat: uid=%s message_id=%s chat_id=%s message_id_db=%s",
                    incoming.uid,
                    incoming.message_id,
                    offer.id,
                    message.id,
                )
                message_created = True

                for attachment in incoming.attachments:
                    prepared = await file_service.prepare_bytes(
                        original_name=attachment.original_name,
                        content_bytes=attachment.content_bytes,
                        mime_type=attachment.content_type,
                    )
                    db_file = await file_service.create_chat_message_file(
                        offer_id=offer.id,
                        upload=prepared,
                    )
                    await uow.messages.attach_file(message_id=message.id, file_id=db_file.id)
                    logger.info(
                        "Attached file to message: uid=%s message_id=%s message_id_db=%s file_id=%s file_name=%s storage_key=%s bytes=%s",
                        incoming.uid,
                        incoming.message_id,
                        message.id,
                        db_file.id,
                        attachment.original_name,
                        db_file.storage_key,
                        len(attachment.content_bytes),
                    )
                    files_saved += 1

                return True, False, message_created, files_saved
            except Exception:
                await file_service.cleanup_tracked_objects()
                raise
