from __future__ import annotations

import imaplib
import logging
import re
import socket
from dataclasses import dataclass
from email import message_from_bytes
from email.message import EmailMessage
from email.policy import default

import anyio

from app.infrastructure.email.email_attachment_parser import EmailAttachmentParser, ParsedEmailAttachment

logger = logging.getLogger("gunicorn.error")


@dataclass(slots=True, frozen=True)
class InboxEmail:
    uid: str
    message_id: str
    from_email: str
    subject: str
    text: str
    message: EmailMessage
    attachments: list[ParsedEmailAttachment]


class IMAPInboxService:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str,
        password: str,
        mailbox: str = "INBOX",
        attachment_parser: EmailAttachmentParser | None = None,
        poll_limit: int = 20,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._mailbox = mailbox
        self._attachment_parser = attachment_parser or EmailAttachmentParser()
        self._poll_limit = max(1, poll_limit)
        self._last_seen_uid = 0

    async def read_unseen(self) -> list[InboxEmail]:
        raw_emails = await anyio.to_thread.run_sync(self._read_unseen_sync)
        logger.info("IMAP read_unseen finished: raw_emails=%s", len(raw_emails))
        emails: list[InboxEmail] = []
        for item in raw_emails:
            attachments = await self._attachment_parser.parse_attachments(item["message"])
            logger.info(
                "IMAP email parsed: uid=%s message_id=%s from=%s subject=%s text_len=%s attachments=%s",
                item["uid"],
                item["message_id"],
                item["from_email"],
                item["subject"],
                len(str(item["text"])),
                len(attachments),
            )
            emails.append(
                InboxEmail(
                    uid=item["uid"],
                    message_id=item["message_id"],
                    from_email=item["from_email"],
                    subject=item["subject"],
                    text=item["text"],
                    message=item["message"],
                    attachments=attachments,
                )
            )
        return emails

    def _read_unseen_sync(self) -> list[dict[str, str | EmailMessage]]:
        conn: imaplib.IMAP4_SSL | None = None
        try:
            conn = imaplib.IMAP4_SSL(self._host, self._port)
            conn.login(self._username, self._password)
            conn.select(self._mailbox)
            logger.info("IMAP mailbox selected: mailbox=%s", self._mailbox)
            all_status, all_data = conn.uid("search", None, "ALL")
            unseen_status, unseen_data = conn.uid("search", None, "UNSEEN")
            if all_status != "OK":
                return []

            all_uids = [uid.decode("utf-8") for uid in (all_data[0] or b"").split() if uid]
            unseen_count = len((unseen_data[0] or b"").split()) if unseen_status == "OK" else 0
            uids = self._select_uids_to_poll(all_uids)
            logger.info(
                "IMAP emails selected: total_uids=%s unseen_uids=%s polled_uids=%s poll_limit=%s last_seen_uid=%s",
                len(all_uids),
                unseen_count,
                len(uids),
                self._poll_limit,
                self._last_seen_uid,
            )
            emails: list[dict[str, str | EmailMessage]] = []
            for uid in uids:
                fetched = self._fetch_email(conn=conn, uid=uid)
                if fetched is not None:
                    emails.append(fetched)
                try:
                    self._last_seen_uid = max(self._last_seen_uid, int(uid))
                except ValueError:
                    continue
            return emails
        except (socket.gaierror, TimeoutError, OSError, imaplib.IMAP4.error) as exc:
            logger.warning(
                "IMAP polling skipped due to connection error: host=%s port=%s mailbox=%s error=%s",
                self._host,
                self._port,
                self._mailbox,
                exc,
            )
            return []
        finally:
            if conn is not None:
                try:
                    conn.close()
                except imaplib.IMAP4.error:
                    pass
                try:
                    conn.logout()
                except imaplib.IMAP4.error:
                    pass

    def _select_uids_to_poll(self, all_uids: list[str]) -> list[str]:
        if not all_uids:
            return []

        parsed_uids: list[tuple[int, str]] = []
        for uid in all_uids:
            try:
                parsed_uids.append((int(uid), uid))
            except ValueError:
                continue

        if not parsed_uids:
            return []

        if self._last_seen_uid <= 0:
            return [uid for _, uid in parsed_uids[-self._poll_limit :]]

        new_uids = [uid for numeric_uid, uid in parsed_uids if numeric_uid > self._last_seen_uid]
        return new_uids[: self._poll_limit]

    def _fetch_email(self, *, conn: imaplib.IMAP4_SSL, uid: str) -> dict[str, str | EmailMessage] | None:
        status, data = conn.uid("fetch", uid, "(BODY.PEEK[])")
        if status != "OK" or not data or not data[0]:
            return None

        raw = data[0][1]
        if not isinstance(raw, bytes):
            return None

        parsed = message_from_bytes(raw, policy=default)
        if not isinstance(parsed, EmailMessage):
            return None

        return {
            "uid": uid,
            "message_id": str(parsed.get("Message-ID", "")).strip(),
            "from_email": str(parsed.get("From", "")).strip(),
            "subject": str(parsed.get("Subject", "")).strip(),
            "text": self._extract_text(parsed),
            "message": parsed,
        }

    def _extract_text(self, message: EmailMessage) -> str:
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_disposition() == "attachment":
                    continue
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if not payload:
                        continue
                    charset = part.get_content_charset() or "utf-8"
                    decoded_text = payload.decode(charset, errors="replace")
                    return self._normalize_reply_text(decoded_text)

        payload = message.get_payload(decode=True)
        if payload:
            charset = message.get_content_charset() or "utf-8"
            decoded_text = payload.decode(charset, errors="replace")
            return self._normalize_reply_text(decoded_text)
        return ""

    def _normalize_reply_text(self, raw_text: str) -> str:
        text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
        lines = text.split("\n")

        quote_markers = (
            "-----original message-----",
            "-- original message --",
            "исходное сообщение",
            "от:",
            "from:",
        )

        cleaned: list[str] = []
        for line in lines:
            stripped = line.strip()
            lowered = stripped.lower()

            if lowered.startswith(">"):
                break
            if any(marker in lowered for marker in quote_markers):
                break
            if re.match(r"^on\s.+wrote:$", lowered):
                break
            if re.match(r"^в\s.+писал\(а\):$", lowered):
                break
            if re.match(r"^(пн|вт|ср|чт|пт|сб|вс),\s+\d{1,2}\s+[а-яё]{3,}\.?\s+\d{4}\s*г\.?\s*в\s*\d{1,2}:\d{2},?$", lowered):
                break
            if re.match(r"^(mon|tue|wed|thu|fri|sat|sun),\s+\w+\s+\d{1,2},?\s+\d{4}.*\d{1,2}:\d{2}.*$", lowered):
                break
            if re.search(r"<[^>]+@[^>]+>:$", stripped):
                break

            cleaned.append(line)

        normalized = "\n".join(cleaned)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
        return normalized.strip()
