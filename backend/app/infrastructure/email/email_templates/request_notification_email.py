from __future__ import annotations

from datetime import datetime
from html import escape

from app.infrastructure.email.email_message_payload import EmailMessagePayload


def build_request_notification_email_payload(
    *,
    to_email: str,
    request_id: int,
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


def build_request_registration_email_payload(
    *,
    to_email: str,
    request_id: int,
    description: str | None,
    deadline_at: datetime,
    tg_bot_url: str | None,
    registration_url: str,
    registration_ttl_seconds: int,
    attachment_warning: str | None = None,
) -> EmailMessagePayload:
    subject = f"AcomOfferDesk — новая заявка №{request_id}"
    return EmailMessagePayload(
        to_email=to_email,
        subject=subject,
        text_content=_build_registration_text(
            request_id=request_id,
            description=description,
            deadline_at=deadline_at,
            tg_bot_url=tg_bot_url,
            registration_url=registration_url,
            registration_ttl_seconds=registration_ttl_seconds,
            attachment_warning=attachment_warning,
        ),
        html_content=_build_registration_html(
            request_id=request_id,
            description=description,
            deadline_at=deadline_at,
            tg_bot_url=tg_bot_url,
            registration_url=registration_url,
            registration_ttl_seconds=registration_ttl_seconds,
            attachment_warning=attachment_warning,
        ),
    )


def _request_header(*, request_id: int, description: str | None, deadline_at: datetime) -> tuple[str, str]:
    deadline_label = deadline_at.strftime("%d.%m.%Y %H:%M")
    request_description = description or "Описание не указано"
    return deadline_label, request_description


def _registration_ttl_label(*, registration_ttl_seconds: int) -> str:
    ttl_minutes = max(1, registration_ttl_seconds // 60)
    if ttl_minutes % 60 == 0:
        return f"{ttl_minutes // 60} ч."
    return f"{ttl_minutes} мин."


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
    request_id: int,
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
        f"Новая заявка №{request_id}\n"
        f"Описание: {request_description}\n"
        f"Дедлайн: {deadline_label}\n\n"
        "Как можно оставить отклик:\n"
        "Вариант 1. Откройте веб-сервис по ссылке ниже и оставьте отклик самостоятельно.\n"
        f"{reply_block}"
        f"Открыть заявку: {request_url}"
        f"{warning_block}"
        f"{_reply_token_mail_footer_text(reply_token=reply_token) if reply_token else ''}\n"
    )


def _build_registration_text(
    *,
    request_id: int,
    description: str | None,
    deadline_at: datetime,
    tg_bot_url: str | None,
    registration_url: str,
    registration_ttl_seconds: int,
    attachment_warning: str | None,
) -> str:
    deadline_label, request_description = _request_header(
        request_id=request_id,
        description=description,
        deadline_at=deadline_at,
    )
    warning_block = f"\n\nВнимание: {attachment_warning}" if attachment_warning else ""
    ttl_label = _registration_ttl_label(registration_ttl_seconds=registration_ttl_seconds)

    legacy_tg_block = (
        "Если ссылка истекла, получить новую можно через legacy Telegram-бота через /start.\n\n"
        f"Открыть legacy Telegram-бот: {tg_bot_url}"
    ) if tg_bot_url else ""

    return (
        "AcomOfferDesk\n\n"
        f"Новая заявка №{request_id}\n"
        f"Описание: {request_description}\n"
        f"Дедлайн: {deadline_label}\n\n"
        "Чтобы пользоваться сервисом и оставлять отклики по заявкам, сначала пройдите регистрацию, либо свяжитесь с контактным лицом лично:\n"
        "Владислав Хлистун\n"
        "Тел. (MAX): +79274558089 \n"
        "Эл. почта: VKhlistun@alabuga.ru \n"  
        f"Ссылка на регистрацию: {registration_url}\n"
        f"Срок действия ссылки: {ttl_label}.\n"
        f"{legacy_tg_block}"
        f"{warning_block}\n"
    )

def _registration_contact_html() -> str:
    return """
            <tr>
              <td style="padding:16px 28px 0 28px;font-family:Arial,Helvetica,sans-serif;color:#374151;font-size:14px;line-height:22px;">
                Если удобнее, вы можете связаться с контактным лицом напрямую:<br/><br/>
                <strong>Владислав Хлистун</strong><br/>
                Тел. (MAX):
                <a href="tel:+79274558089" style="color:#0969da;text-decoration:underline;">+7 927 455-80-89</a><br/>
                Эл. почта:
                <a href="mailto:VKhlistun@alabuga.ru" style="color:#0969da;text-decoration:underline;">VKhlistun@alabuga.ru</a>
              </td>
            </tr>
    """.rstrip()

def _build_standard_html(
    *,
    request_id: int,
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
            <tr>
              <td style="padding:24px 28px 8px 28px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                  <tr>
                    <td bgcolor="#0969da" style="border-radius:6px;">
                      <a href="{escaped_url}" style="display:inline-block;padding:12px 20px;font-family:Arial,Helvetica,sans-serif;font-size:16px;color:#ffffff;text-decoration:none;">
                        Открыть заявку
                      </a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
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


def _build_registration_html(
    *,
    request_id: int,
    description: str | None,
    deadline_at: datetime,
    tg_bot_url: str | None,
    registration_url: str,
    registration_ttl_seconds: int,
    attachment_warning: str | None,
) -> str:
    deadline_label, request_description = _request_header(
        request_id=request_id,
        description=description,
        deadline_at=deadline_at,
    )
    contact_html = _registration_contact_html()
    escaped_description = escape(request_description)
    escaped_bot_url = escape(tg_bot_url) if tg_bot_url else None
    escaped_registration_url = escape(registration_url)
    ttl_label = _registration_ttl_label(registration_ttl_seconds=registration_ttl_seconds)
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

    legacy_tg_button_html = (
        f"""
                    <td style="width:10px;"></td>
                    <td bgcolor="#0969da" style="border-radius:6px;">
                      <a href="{escaped_bot_url}" style="display:inline-block;padding:12px 20px;font-family:Arial,Helvetica,sans-serif;font-size:16px;color:#ffffff;text-decoration:none;">
                        Открыть legacy Telegram-бот
                      </a>
                    </td>
        """.rstrip()
        if escaped_bot_url
        else ""
    )
    legacy_tg_info_html = (
        f"""
                Если ссылка истекла, получить новую можно в legacy Telegram-боте через /start.<br/><br/>
                Если кнопка не работает, откройте ссылку вручную:<br/>
                <a href="{escaped_bot_url}" style="color:#0969da;text-decoration:underline;word-break:break-all;">{escaped_bot_url}</a>
        """.rstrip()
        if escaped_bot_url
        else ""
    )

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
                Для доступа к заявке зарегистрируйтесь в сервисе по ссылке ниже.
              </td>
            </tr>
            <tr>
              <td style="padding:24px 28px 8px 28px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                  <tr>
                    <td bgcolor="#0969da" style="border-radius:6px;">
                      <a href="{escaped_registration_url}" style="display:inline-block;padding:12px 20px;font-family:Arial,Helvetica,sans-serif;font-size:16px;color:#ffffff;text-decoration:none;">
                        Перейти к регистрации
                      </a>
                    </td>
                    {legacy_tg_button_html}
                  </tr>
                </table>
              </td>
            </tr>
            {contact_html}
            {warning_html}
            <tr>
              <td style="padding:8px 28px 0 28px;font-family:Arial,Helvetica,sans-serif;color:#374151;font-size:14px;line-height:22px;">
                Ссылка на регистрацию:<br/>
                <a href="{escaped_registration_url}" style="color:#0969da;text-decoration:underline;word-break:break-all;">{escaped_registration_url}</a><br/><br/>
                Срок действия ссылки: <strong>{ttl_label}</strong>.<br/>
                {legacy_tg_info_html}
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()
