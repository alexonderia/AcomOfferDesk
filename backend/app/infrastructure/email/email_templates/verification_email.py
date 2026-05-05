from __future__ import annotations

from app.infrastructure.email.email_message_payload import EmailMessagePayload


VERIFICATION_EMAIL_SUBJECT = "AcomOfferDesk — подтверждение электронной почты"


def build_verification_email_payload(
    *,
    to_email: str,
    verification_link: str,
    ttl_seconds: int,
    service_name: str,
) -> EmailMessagePayload:
    return EmailMessagePayload(
        to_email=to_email,
        subject=VERIFICATION_EMAIL_SUBJECT,
        text_content=_build_verification_text_template(
            verification_link=verification_link,
            ttl_seconds=ttl_seconds,
        ),
        html_content=_build_verification_html_template(
            verification_link=verification_link,
            ttl_seconds=ttl_seconds,
            service_name=service_name,
        ),
    )


def _build_verification_text_template(*, verification_link: str, ttl_seconds: int) -> str:
    ttl_minutes = max(1, ttl_seconds // 60)
    return (
        "Здравствуйте!\n\n"
        "Вы получили это письмо, потому что был запрошен доступ к подтверждению электронной почты в AcomOfferDesk.\n\n"
        "Подтвердите адрес по ссылке:\n"
        f"{verification_link}\n\n"
        f"Ссылка действительна {ttl_minutes} минут.\n\n"
        "Если вы не запрашивали подтверждение — просто проигнорируйте это письмо."
    )


def _build_verification_html_template(*, verification_link: str, ttl_seconds: int, service_name: str) -> str:
    ttl_minutes = max(1, ttl_seconds // 60)
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
                {service_name}
              </td>
            </tr>
            <tr>
              <td style="padding:0 28px 0 28px;font-family:Arial,Helvetica,sans-serif;color:#111827;font-size:16px;line-height:24px;">
                Здравствуйте!<br/><br/>
                Подтвердите адрес электронной почты для вашей учетной записи.
              </td>
            </tr>
            <tr>
              <td style="padding:24px 28px 8px 28px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                  <tr>
                    <td bgcolor="#0969da" style="border-radius:6px;">
                      <a href="{verification_link}" style="display:inline-block;padding:12px 20px;font-family:Arial,Helvetica,sans-serif;font-size:16px;color:#ffffff;text-decoration:none;">
                        Подтвердить email
                      </a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:8px 28px 0 28px;font-family:Arial,Helvetica,sans-serif;color:#374151;font-size:14px;line-height:22px;">
                Если кнопка не работает, откройте ссылку вручную:<br/>
                <a href="{verification_link}" style="color:#0969da;text-decoration:underline;word-break:break-all;">{verification_link}</a>
              </td>
            </tr>
            <tr>
              <td style="padding:16px 28px 0 28px;font-family:Arial,Helvetica,sans-serif;color:#374151;font-size:14px;line-height:22px;">
                Срок действия ссылки: <strong>{ttl_minutes} минут</strong>.
              </td>
            </tr>
            <tr>
              <td style="padding:16px 28px 24px 28px;font-family:Arial,Helvetica,sans-serif;color:#6b7280;font-size:13px;line-height:20px;">
                Если вы не запрашивали подтверждение — проигнорируйте это письмо.<br/>
                © AcomOfferDesk
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()
