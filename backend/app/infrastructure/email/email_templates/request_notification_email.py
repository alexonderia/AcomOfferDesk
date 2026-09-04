from __future__ import annotations

from datetime import datetime
from html import escape

from app.infrastructure.email.email_message_payload import EmailMessagePayload
from shared.notification_copy import (
    NOTIFICATION_BUTTON_LABEL,
    request_created_body,
)
from app.infrastructure.email.email_templates.email_contact_blocks import build_primary_button_html


def build_request_notification_email_payload(
    *,
    to_email: str,
    request_id: str,
    description: str | None,
    deadline_at: datetime,
    request_url: str,
    reply_token: str | None,
    attachment_warning: str | None = None,
) -> EmailMessagePayload:
    subject = f"AcomOfferDesk — новая заявка №{request_id}"
    return EmailMessagePayload(
        to_email=to_email,
        subject=subject,
        text_content=_build_standard_text(
            request_id=request_id,
            description=description,
            deadline_at=deadline_at,
            request_url=request_url,
            reply_token=reply_token,
            attachment_warning=attachment_warning,
        ),
        html_content=_build_standard_html(
            request_id=request_id,
            description=description,
            deadline_at=deadline_at,
            request_url=request_url,
            reply_token=reply_token,
            attachment_warning=attachment_warning,
        ),
        reply_token=reply_token,
    )


def _request_header(*, request_id: str, description: str | None, deadline_at: datetime) -> tuple[str, str]:
    deadline_label = deadline_at.strftime("%d.%m.%Y %H:%M")
    request_description = description or "Описание не указано"
    return deadline_label, request_description


def _reply_token_mail_footer_text(*, reply_token: str) -> str:
    return (
        "\n\n---\n"
        "Ответ по почте: при ответе не удаляйте строку ниже целиком (можно оставить в цитате).\n"
        f"{reply_token}\n"
    )


def _reply_token_mail_footer_html(*, reply_token: str) -> str:
    escaped_token = escape(reply_token)
    return f"""
            <tr>
              <td style="padding:16px 28px 24px 28px;font-family:Arial,Helvetica,sans-serif;color:#374151;font-size:13px;line-height:20px;border-top:1px solid #e6e8eb;">
                <strong>Ответ по почте:</strong> при ответе не удаляйте строку целиком (допустимо оставить в цитате).<br/>
                <span style="display:block;margin-top:8px;padding:10px 12px;background:#f3f4f6;border-radius:6px;font-family:ui-monospace,Consolas,monospace;word-break:break-all;">{escaped_token}</span>
              </td>
            </tr>
    """.rstrip()


def _build_standard_text(
    *,
    request_id: str,
    description: str | None,
    deadline_at: datetime,
    request_url: str,
    reply_token: str | None,
    attachment_warning: str | None,
) -> str:
    deadline_label, request_description = _request_header(
        request_id=request_id,
        description=description,
        deadline_at=deadline_at,
    )
    warning_block = f"\n\nВнимание: {attachment_warning}" if attachment_warning else ""
    reply_block = (
        "Вариант 2. Ответьте на это письмо — мы автоматически создадим отклик с чатом для обсуждения в веб-сервисе.\n"
        "Если есть документы, пожалуйста, прикрепите файлы к ответному письму.\n\n"
        if reply_token
        else "\n"
    )

    return (
        "AcomOfferDesk\n\n"
        f"{request_created_body(request_id=request_id)}\n"
        f"Описание: {request_description}\n"
        f"Дедлайн: {deadline_label}\n\n"
        "Как можно оставить отклик:\n"
        "Вариант 1. Откройте веб-сервис по ссылке ниже и оставьте отклик самостоятельно.\n"
        f"{reply_block}"
        f"{NOTIFICATION_BUTTON_LABEL}: {request_url}"
        f"{warning_block}"
        f"{_reply_token_mail_footer_text(reply_token=reply_token) if reply_token else ''}\n"
    )


def _build_standard_html(
    *,
    request_id: str,
    description: str | None,
    deadline_at: datetime,
    request_url: str,
    reply_token: str | None,
    attachment_warning: str | None,
) -> str:
    deadline_label, request_description = _request_header(
        request_id=request_id,
        description=description,
        deadline_at=deadline_at,
    )
    escaped_description = escape(request_description)
    escaped_url = escape(request_url)
    warning_html = (
        f"""
            <tr>
              <td style="padding:8px 28px 0 28px;font-family:Arial,Helvetica,sans-serif;color:#b45309;font-size:14px;line-height:22px;">
                <strong>Внимание:</strong> {escape(attachment_warning)}
              </td>
            </tr>
        """.rstrip()
        if attachment_warning
        else ""
    )
    reply_block_html = (
        """
                Вариант 2. Ответьте на это письмо — мы автоматически создадим отклик с чатом для обсуждения в веб-сервисе.<br/>
                Если есть документы, пожалуйста, прикрепите файлы к ответному письму.
        """.rstrip()
        if reply_token
        else ""
    )
    reply_token_footer_html = _reply_token_mail_footer_html(reply_token=reply_token) if reply_token else ""
    button_html = build_primary_button_html(label=NOTIFICATION_BUTTON_LABEL, url=request_url)

    return f"""
<!DOCTYPE html>
<html lang="ru">
  <body style="margin:0;padding:0;background-color:#f6f8fb;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color:#f6f8fb;padding:24px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="600" style="width:600px;max-width:600px;background:#ffffff;border:1px solid #e6e8eb;border-radius:10px;">
            <tr>
              <td style="padding:24px 28px 8px 28px;font-family:Arial,Helvetica,sans-serif;color:#111827;font-size:22px;font-weight:700;">
                AcomOfferDesk
              </td>
            </tr>
            <tr>
              <td style="padding:0 28px;font-family:Arial,Helvetica,sans-serif;color:#111827;font-size:16px;line-height:24px;">
                Поступила новая заявка <strong>№{request_id}</strong>.<br/><br/>
                <strong>Описание:</strong> {escaped_description}<br/>
                <strong>Дедлайн:</strong> {deadline_label}
              </td>
            </tr>
            <tr>
              <td style="padding:14px 28px 0 28px;font-family:Arial,Helvetica,sans-serif;color:#374151;font-size:14px;line-height:22px;">
                <strong>Как можно оставить отклик:</strong><br/>
                Вариант 1. Откройте веб-сервис по ссылке ниже и оставьте отклик самостоятельно.<br/>
                {reply_block_html}
              </td>
            </tr>
            {button_html}
            {warning_html}
            <tr>
              <td style="padding:8px 28px 0 28px;font-family:Arial,Helvetica,sans-serif;color:#374151;font-size:14px;line-height:22px;">
                Если кнопка не работает, откройте ссылку вручную:<br/>
                <a href="{escaped_url}" style="color:#0969da;text-decoration:underline;word-break:break-all;">{escaped_url}</a>
              </td>
            </tr>
            {reply_token_footer_html}
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()
