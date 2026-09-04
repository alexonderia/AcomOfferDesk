from __future__ import annotations

import base64
import hashlib
import logging
import mimetypes
import os
import smtplib
import ssl
import time
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr

logger = logging.getLogger(__name__)

_DEDUP_TTL_SECONDS = max(10, int(os.getenv("EMAIL_DEDUP_TTL_SECONDS", "120")))
_SPAM_COOLDOWN_SECONDS = max(60, int(os.getenv("EMAIL_SPAM_COOLDOWN_SECONDS", "600")))
_recent_payloads_until: dict[str, float] = {}
_recipient_spam_block_until: dict[str, float] = {}


@dataclass(frozen=True, slots=True)
class EmailSendResult:
    success: bool
    safe_error_code: str | None = None
    safe_error_message: str | None = None


def _cleanup_runtime_state(now_mono: float) -> None:
    expired_payload_keys = [key for key, until in _recent_payloads_until.items() if until <= now_mono]
    for key in expired_payload_keys:
        _recent_payloads_until.pop(key, None)

    expired_recipient_keys = [key for key, until in _recipient_spam_block_until.items() if until <= now_mono]
    for key in expired_recipient_keys:
        _recipient_spam_block_until.pop(key, None)


def _build_payload_fingerprint(payload: dict) -> str:
    to_email = str(payload.get("to_email") or "").strip().lower()
    subject = str(payload.get("subject") or "").strip()
    text_content = str(payload.get("text_content") or "")
    html_content = str(payload.get("html_content") or "")
    reply_token = str(payload.get("reply_token") or "")

    attachments = payload.get("attachments") or []
    attachment_parts: list[str] = []
    for item in attachments:
        filename = str(item.get("filename") or "")
        mime_type = str(item.get("mime_type") or "")
        content_base64 = str(item.get("content_base64") or "")
        attachment_parts.append(f"{filename}:{mime_type}:{len(content_base64)}")

    raw = "\n".join(
        [
            to_email,
            subject,
            text_content,
            html_content,
            reply_token,
            "|".join(attachment_parts),
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _is_spam_rejection(exc: smtplib.SMTPDataError) -> bool:
    smtp_error = exc.smtp_error
    if isinstance(smtp_error, bytes):
        error_text = smtp_error.decode("utf-8", errors="ignore").lower()
    else:
        error_text = str(smtp_error).lower()

    return exc.smtp_code == 554 and ("spam" in error_text or "suspicion" in error_text or "5.7.1" in error_text)


def _build_reply_to_address(from_address: str, from_name: str, reply_token: str | None) -> str:
    if not reply_token:
        return formataddr((from_name, from_address))

    local_part, _, domain_part = from_address.partition("@")
    if not local_part or not domain_part:
        return formataddr((from_name, from_address))

    tagged = f"{local_part}+rt-{reply_token}@{domain_part}"
    return formataddr((from_name, tagged))


def _format_recipient_log(payload: dict) -> str:
    to_email = str(payload.get("to_email", "")).strip()
    recipient_context = payload.get("recipient_context")
    user_login = ""
    if isinstance(recipient_context, dict):
        user_login = str(recipient_context.get("user_login") or "").strip()
    if not user_login:
        user_login = str(payload.get("recipient_user_id") or "").strip()
    if user_login:
        return f'"{to_email}" - "зарегистрированный пользователь - login={user_login}"'
    return f'"{to_email}" - "внешний получатель"'


def _resolve_smtp_security_mode(smtp_port: int) -> str:
    mode = os.getenv("SMTP_SECURITY", "auto").strip().lower()
    if mode not in {"auto", "ssl", "starttls", "none"}:
        logger.warning("Unknown SMTP_SECURITY=%r, fallback to auto", mode)
        mode = "auto"

    if mode == "auto":
        return "ssl" if smtp_port == 465 else "starttls" if smtp_port == 587 else "none"
    return mode


async def send_email(payload: dict) -> EmailSendResult:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    username = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_APP_PASSWORD")

    if not smtp_host or not username or not password:
        logger.warning("SMTP env vars are not configured. Skip email delivery")
        return EmailSendResult(
            success=False,
            safe_error_code="SMTP_NOT_CONFIGURED",
            safe_error_message="Не удалось отправить письмо. Проверьте настройки почты.",
        )

    to_email = str(payload.get("to_email", "")).strip()
    if not to_email:
        logger.warning("Email payload has no recipient")
        return EmailSendResult(
            success=False,
            safe_error_code="INVALID_PAYLOAD",
            safe_error_message="Не удалось отправить письмо. Некорректный адрес получателя.",
        )
    subject = str(payload.get("subject") or "").strip()
    if not subject:
        logger.warning("Email payload has no subject: recipient=%s", to_email)
        return EmailSendResult(
            success=False,
            safe_error_code="INVALID_PAYLOAD",
            safe_error_message="Не удалось отправить письмо. Некорректные параметры письма.",
        )
    text_content = str(payload.get("text_content") or "")
    if not text_content.strip():
        logger.warning("Email payload has no text content: recipient=%s", to_email)
        return EmailSendResult(
            success=False,
            safe_error_code="INVALID_PAYLOAD",
            safe_error_message="Не удалось отправить письмо. Некорректные параметры письма.",
        )

    normalized_to_email = to_email.lower()
    now_mono = time.monotonic()
    _cleanup_runtime_state(now_mono)

    blocked_until = _recipient_spam_block_until.get(normalized_to_email)
    if blocked_until is not None and blocked_until > now_mono:
        remaining_seconds = int(blocked_until - now_mono)
        logger.warning(
            "Skip email delivery due to spam cooldown: recipient=%s remaining_seconds=%s",
            normalized_to_email,
            remaining_seconds,
        )
        return EmailSendResult(
            success=False,
            safe_error_code="SMTP_SPAM_COOLDOWN",
            safe_error_message="Отправка временно ограничена провайдером почты. Попробуйте позже.",
        )

    payload_fingerprint = _build_payload_fingerprint(payload)
    duplicate_until = _recent_payloads_until.get(payload_fingerprint)
    if duplicate_until is not None and duplicate_until > now_mono:
        logger.info("Duplicate email payload skipped for %s", _format_recipient_log(payload))
        return EmailSendResult(
            success=True,
        )
    _recent_payloads_until[payload_fingerprint] = now_mono + _DEDUP_TTL_SECONDS

    from_address = str(payload.get("from_address") or username)
    from_name = str(payload.get("from_name") or os.getenv("EMAIL_FROM_NAME", "AcomOfferDesk"))

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr((from_name, from_address))
    message["To"] = to_email
    message["Reply-To"] = _build_reply_to_address(from_address, from_name, payload.get("reply_token"))

    html_content = payload.get("html_content")
    message.set_content(text_content, subtype="plain", charset="utf-8")
    if html_content:
        message.add_alternative(str(html_content), subtype="html", charset="utf-8")

    for item in payload.get("attachments") or []:
        filename = str(item.get("filename") or "attachment.bin")
        content_base64 = item.get("content_base64")
        if not content_base64:
            continue
        try:
            content_bytes = base64.b64decode(content_base64)
        except (ValueError, TypeError):
            logger.warning("Skip email attachment with invalid base64 payload: %s", filename)
            continue
        guessed = mimetypes.guess_type(filename)[0]
        mime_type = guessed or str(item.get("mime_type") or "application/octet-stream")
        if "/" in mime_type:
            maintype, subtype = mime_type.split("/", 1)
        else:
            maintype, subtype = "application", "octet-stream"
        message.add_attachment(content_bytes, maintype=maintype, subtype=subtype, filename=filename)

    context = ssl.create_default_context()
    smtp_security = _resolve_smtp_security_mode(smtp_port)
    try:
        if smtp_security == "ssl":
            smtp = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=20, context=context)
        else:
            smtp = smtplib.SMTP(smtp_host, smtp_port, timeout=20)

        with smtp:
            if smtp_security == "starttls":
                smtp.ehlo()
                smtp.starttls(context=context)
                smtp.ehlo()
            smtp.login(username, password)
            smtp.send_message(message, from_addr=from_address, to_addrs=[to_email])
        logger.info("Email sent to %s", _format_recipient_log(payload))
        return EmailSendResult(success=True)
    except smtplib.SMTPDataError as exc:
        if _is_spam_rejection(exc):
            _recipient_spam_block_until[normalized_to_email] = time.monotonic() + _SPAM_COOLDOWN_SECONDS
            logger.error(
                "Email rejected as suspected spam for %s; cooldown_seconds=%s",
                _format_recipient_log(payload),
                _SPAM_COOLDOWN_SECONDS,
            )
            return EmailSendResult(
                success=False,
                safe_error_code="SMTP_SPAM_REJECTED",
                safe_error_message="Письмо отклонено почтовым сервером. Попробуйте позже.",
            )
        _recent_payloads_until.pop(payload_fingerprint, None)
        logger.exception("Failed to send email to %s", _format_recipient_log(payload))
        return EmailSendResult(
            success=False,
            safe_error_code="SMTP_DATA_ERROR",
            safe_error_message="Не удалось отправить письмо. Проверьте настройки почты.",
        )
    except (smtplib.SMTPException, ssl.SSLError, OSError):
        _recent_payloads_until.pop(payload_fingerprint, None)
        logger.exception("Failed to send email to %s", _format_recipient_log(payload))
        return EmailSendResult(
            success=False,
            safe_error_code="SMTP_DELIVERY_ERROR",
            safe_error_message="Не удалось отправить письмо. Проверьте настройки почты.",
        )
