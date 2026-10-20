from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

import anyio


class SensitiveEmailDeliveryError(RuntimeError):
    """Sanitized failure that cannot retain a secret-bearing email payload."""


class SensitiveEmailService:
    """Send secret-bearing mail directly so tokens never rest in a broker queue."""

    def __init__(
        self,
        *,
        smtp_host: str,
        smtp_port: int,
        smtp_security: str,
        username: str,
        password: str,
        from_address: str,
        from_name: str,
    ) -> None:
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._smtp_security = smtp_security
        self._username = username
        self._password = password
        self._from_address = from_address
        self._from_name = from_name

    async def send_email(
        self,
        *,
        to_email: str,
        subject: str,
        text_content: str,
        html_content: str,
    ) -> None:
        try:
            await anyio.to_thread.run_sync(
                self._send_sync,
                to_email,
                subject,
                text_content,
                html_content,
            )
        except Exception:
            raise SensitiveEmailDeliveryError("Sensitive email delivery failed") from None

    def _send_sync(
        self,
        to_email: str,
        subject: str,
        text_content: str,
        html_content: str,
    ) -> None:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = formataddr((self._from_name, self._from_address))
        message["To"] = to_email
        message.set_content(text_content, subtype="plain", charset="utf-8")
        message.add_alternative(html_content, subtype="html", charset="utf-8")

        mode = self._smtp_security.strip().lower()
        if mode == "auto":
            mode = "ssl" if self._smtp_port == 465 else "starttls"
        context = ssl.create_default_context()
        if mode == "ssl":
            smtp = smtplib.SMTP_SSL(
                self._smtp_host,
                self._smtp_port,
                timeout=20,
                context=context,
            )
        else:
            smtp = smtplib.SMTP(self._smtp_host, self._smtp_port, timeout=20)
        with smtp:
            if mode == "starttls":
                smtp.ehlo()
                smtp.starttls(context=context)
                smtp.ehlo()
            smtp.login(self._username, self._password)
            smtp.send_message(message, from_addr=self._from_address, to_addrs=[to_email])
