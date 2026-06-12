from __future__ import annotations

from html import escape

from app.infrastructure.email.email_message_payload import EmailMessagePayload
from shared.notification_copy import (
    ACCESS_CLOSED_BODY,
    ACCESS_OPENED_BODY,
    REGISTRATION_COMPLETED_BODY,
    email_subject,
)


def build_contractor_review_email_payload(*, to_email: str) -> EmailMessagePayload:
    subject = email_subject("регистрация пройдена")
    return EmailMessagePayload(
        to_email=to_email,
        subject=subject,
        text_content=f"{REGISTRATION_COMPLETED_BODY}\n",
        html_content=f"""
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
              <td style="padding:0 28px 24px 28px;font-family:Arial,Helvetica,sans-serif;color:#111827;font-size:16px;line-height:24px;">
                {escape(REGISTRATION_COMPLETED_BODY)}
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip(),
    )


def build_contractor_access_opened_email_payload(
    *,
    to_email: str,
    authorization_url: str | None,
) -> EmailMessagePayload:
    subject = email_subject("доступ открыт")
    escaped_url = escape(authorization_url or "")

    text_with_url = (
        f"{ACCESS_OPENED_BODY}\n{authorization_url}\n"
        if authorization_url
        else f"{ACCESS_OPENED_BODY}\n"
    )

    html_link_block = (
        f"""
            <tr>
              <td style="padding:24px 28px 8px 28px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                  <tr>
                    <td bgcolor="#0969da" style="border-radius:6px;">
                      <a href="{escaped_url}" style="display:inline-block;padding:12px 20px;font-family:Arial,Helvetica,sans-serif;font-size:16px;color:#ffffff;text-decoration:none;">
                        Перейти к авторизации
                      </a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:8px 28px 24px 28px;font-family:Arial,Helvetica,sans-serif;color:#374151;font-size:14px;line-height:22px;">
                Если кнопка не работает, откройте ссылку вручную:<br/>
                <a href="{escaped_url}" style="color:#0969da;text-decoration:underline;word-break:break-all;">{escaped_url}</a>
              </td>
            </tr>
        """.rstrip()
        if authorization_url
        else ""
    )

    return EmailMessagePayload(
        to_email=to_email,
        subject=subject,
        text_content=text_with_url,
        html_content=f"""
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
              <td style="padding:0 28px 0 28px;font-family:Arial,Helvetica,sans-serif;color:#111827;font-size:16px;line-height:24px;">
                {escape(ACCESS_OPENED_BODY)}
              </td>
            </tr>
            {html_link_block}
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip(),
    )


def build_contractor_access_closed_email_payload(*, to_email: str) -> EmailMessagePayload:
    subject = email_subject("доступ ограничен")
    return EmailMessagePayload(
        to_email=to_email,
        subject=subject,
        text_content=f"{ACCESS_CLOSED_BODY}\n",
        html_content=f"""
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
              <td style="padding:0 28px 24px 28px;font-family:Arial,Helvetica,sans-serif;color:#111827;font-size:16px;line-height:24px;">
                {escape(ACCESS_CLOSED_BODY)}
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip(),
    )
