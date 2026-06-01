from __future__ import annotations

from html import escape

from app.infrastructure.email.email_message_payload import EmailMessagePayload
from app.infrastructure.email.email_templates.email_contact_blocks import (
    EmailContactInfo,
    build_contact_html_block,
    build_contact_text_block,
    build_primary_button_html,
)
from app.infrastructure.email.email_templates.email_invitation_content import (
    PORTAL_BUTTON_LABEL,
    build_invitation_intro_html,
    build_invitation_intro_text_lines,
)

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
    contact = EmailContactInfo(
        name=contact_name,
        email=contact_email,
        phone=contact_phone,
    )
    return EmailMessagePayload(
        to_email=to_email,
        subject=INVITATION_SUBJECT,
        text_content=_build_invitation_text(
            portal_url=portal_url,
            contact=contact,
            contact_text=contact_text,
        ),
        html_content=_build_invitation_html(
            portal_url=portal_url,
            contact=contact,
            contact_text=contact_text,
        ),
    )


def _build_invitation_text(
    *,
    portal_url: str | None,
    contact: EmailContactInfo,
    contact_text: str | None,
) -> str:
    lines = [
        "AcomOfferDesk",
        "",
        *build_invitation_intro_text_lines(),
    ]
    if portal_url:
        lines.append(f"{PORTAL_BUTTON_LABEL}: {portal_url}")

    contact_lines = build_contact_text_block(
        contact=contact,
        intro="Если удобнее, вы можете связаться с контактным лицом напрямую:",
    )
    if contact_lines:
        lines.append("")
        lines.extend(contact_lines)

    if contact_text:
        lines.extend(["", contact_text])

    lines.append("")
    return "\n".join(lines)


def _build_invitation_html(
    *,
    portal_url: str | None,
    contact: EmailContactInfo,
    contact_text: str | None,
) -> str:
    escaped_contact_text = escape(contact_text) if contact_text else ""
    contact_html = build_contact_html_block(contact=contact)
    button_html = build_primary_button_html(label=PORTAL_BUTTON_LABEL, url=portal_url) if portal_url else ""
    portal_fallback_html = (
        f"""
            <tr>
              <td style="padding:8px 28px 24px 28px;font-family:Arial,Helvetica,sans-serif;color:#374151;font-size:14px;line-height:22px;">
                Ссылка для входа:<br/>
                <a href="{escape(portal_url)}" style="color:#0969da;text-decoration:underline;word-break:break-all;">{escape(portal_url)}</a>
              </td>
            </tr>
        """.rstrip()
        if portal_url
        else ""
    )
    extra_text_html = (
        f"""
            <tr>
              <td style="padding:8px 28px 0 28px;font-family:Arial,Helvetica,sans-serif;color:#374151;font-size:14px;line-height:22px;">
                {escaped_contact_text}
              </td>
            </tr>
        """.rstrip()
        if escaped_contact_text
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
                {build_invitation_intro_html()}
              </td>
            </tr>
            {button_html}
            {contact_html}
            {extra_text_html}
            {portal_fallback_html}
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()
