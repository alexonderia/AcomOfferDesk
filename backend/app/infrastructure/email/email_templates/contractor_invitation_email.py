from __future__ import annotations

from html import escape

from app.infrastructure.email.email_message_payload import EmailMessagePayload

INVITATION_SUBJECT = "Приглашение в AcomOfferDesk"


def build_contractor_invitation_email_payload(
    *,
    to_email: str,
    portal_url: str | None,
    contact_name: str | None,
    contact_email: str | None,
    contact_phone: str | None,
    contact_text: str | None,
) -> EmailMessagePayload:
    return EmailMessagePayload(
        to_email=to_email,
        subject=INVITATION_SUBJECT,
        text_content=_build_invitation_text(
            portal_url=portal_url,
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            contact_text=contact_text,
        ),
        html_content=_build_invitation_html(
            portal_url=portal_url,
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            contact_text=contact_text,
        ),
    )


def _build_invitation_text(
    *,
    portal_url: str | None,
    contact_name: str | None,
    contact_email: str | None,
    contact_phone: str | None,
    contact_text: str | None,
) -> str:
    lines = [
        "AcomOfferDesk",
        "",
        "Вы приглашены к работе в системе AcomOfferDesk.",
        "Инструкция по подключению приложена к письму отдельным файлом.",
    ]
    if portal_url:
        lines.extend(["", f"Ссылка для входа/регистрации: {portal_url}"])

    contact_block = _contact_lines(
        contact_name=contact_name,
        contact_email=contact_email,
        contact_phone=contact_phone,
        contact_text=contact_text,
    )
    if contact_block:
        lines.extend(["", "Контакты для связи:"])
        lines.extend(contact_block)

    lines.append("")
    return "\n".join(lines)


def _build_invitation_html(
    *,
    portal_url: str | None,
    contact_name: str | None,
    contact_email: str | None,
    contact_phone: str | None,
    contact_text: str | None,
) -> str:
    escaped_portal_url = escape(portal_url) if portal_url else None
    contact_lines = _contact_lines(
        contact_name=contact_name,
        contact_email=contact_email,
        contact_phone=contact_phone,
        contact_text=contact_text,
    )
    contact_html = "<br/>".join(escape(line) for line in contact_lines) if contact_lines else ""
    portal_html = (
        f"""
            <tr>
              <td style="padding:8px 28px 0 28px;font-family:Arial,Helvetica,sans-serif;color:#374151;font-size:14px;line-height:22px;">
                Ссылка для входа/регистрации:<br/>
                <a href="{escaped_portal_url}" style="color:#0969da;text-decoration:underline;word-break:break-all;">{escaped_portal_url}</a>
              </td>
            </tr>
        """.rstrip()
        if escaped_portal_url
        else ""
    )
    contacts_section = (
        f"""
            <tr>
              <td style="padding:12px 28px 24px 28px;font-family:Arial,Helvetica,sans-serif;color:#374151;font-size:14px;line-height:22px;">
                <strong>Контакты для связи:</strong><br/>
                {contact_html}
              </td>
            </tr>
        """.rstrip()
        if contact_html
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
                Вы приглашены к работе в системе AcomOfferDesk.<br/><br/>
                Инструкция по подключению приложена к письму отдельным файлом.
              </td>
            </tr>
            {portal_html}
            {contacts_section}
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()


def _contact_lines(
    *,
    contact_name: str | None,
    contact_email: str | None,
    contact_phone: str | None,
    contact_text: str | None,
) -> list[str]:
    lines: list[str] = []
    if contact_name:
        lines.append(f"Контакт: {contact_name}")
    if contact_email:
        lines.append(f"Email: {contact_email}")
    if contact_phone:
        lines.append(f"Телефон: {contact_phone}")
    if contact_text:
        lines.append(contact_text)
    return lines
