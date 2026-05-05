from __future__ import annotations

from html import escape

from app.infrastructure.email.email_message_payload import EmailMessagePayload


def build_contractor_review_email_payload(*, to_email: str) -> EmailMessagePayload:
    subject = "AcomOfferDesk — профиль контрагента на рассмотрении"
    return EmailMessagePayload(
        to_email=to_email,
        subject=subject,
        text_content=(
            "Здравствуйте!\n\n"
            "Регистрация в AcomOfferDesk завершена. Ваш профиль находится на рассмотрении.\n"
            "Мы сообщим дополнительно, когда доступ в сервис будет открыт.\n"
        ),
        html_content="""
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
                Регистрация завершена.<br/><br/>
                Ваш профиль находится на рассмотрении. Мы сообщим, когда доступ к сервису будет открыт.
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
    subject = "AcomOfferDesk — доступ в сервис открыт"
    escaped_url = escape(authorization_url or "")

    text_with_url = (
        "Здравствуйте!\n\n"
        "Доступ в AcomOfferDesk открыт. Вы можете войти в сервис по ссылке:\n"
        f"{authorization_url}\n"
        if authorization_url
        else "Здравствуйте!\n\nДоступ в AcomOfferDesk открыт.\n"
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
                Доступ в сервис открыт.<br/>
                Теперь вы можете войти в AcomOfferDesk.
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
    subject = "AcomOfferDesk — доступ в сервис ограничен"
    return EmailMessagePayload(
        to_email=to_email,
        subject=subject,
        text_content=(
            "Здравствуйте!\n\n"
            "Ваш доступ в AcomOfferDesk временно ограничен.\n"
            "Для уточнения причины обратитесь к администратору.\n"
        ),
        html_content="""
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
                Ваш доступ в сервис временно ограничен.<br/>
                Для уточнения причины обратитесь к администратору.
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
