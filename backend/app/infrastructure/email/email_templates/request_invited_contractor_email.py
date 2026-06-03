from __future__ import annotations

from datetime import datetime
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
from app.infrastructure.email.email_templates.request_notification_email import _request_header


def build_request_invited_contractor_email_payload(
    *,
    to_email: str,
    request_id: str,
    description: str | None,
    deadline_at: datetime,
    portal_url: str,
    contact: EmailContactInfo,
    attachment_warning: str | None = None,
) -> EmailMessagePayload:
    subject = f"AcomOfferDesk — новая заявка №{request_id}"
    return EmailMessagePayload(
        to_email=to_email,
        subject=subject,
        text_content=_build_text(
            request_id=request_id,
            description=description,
            deadline_at=deadline_at,
            portal_url=portal_url,
            contact=contact,
            attachment_warning=attachment_warning,
        ),
        html_content=_build_html(
            request_id=request_id,
            description=description,
            deadline_at=deadline_at,
            portal_url=portal_url,
            contact=contact,
            attachment_warning=attachment_warning,
        ),
    )


def _build_text(
    *,
    request_id: str,
    description: str | None,
    deadline_at: datetime,
    portal_url: str,
    contact: EmailContactInfo,
    attachment_warning: str | None,
) -> str:
    deadline_label, request_description = _request_header(
        request_id=request_id,
        description=description,
        deadline_at=deadline_at,
    )
    warning_block = f"\n\nВнимание: {attachment_warning}" if attachment_warning else ""

    contact_lines = build_contact_text_block(
        contact=contact,
        intro="Если удобнее, вы можете связаться с контактным лицом напрямую:",
    )
    contact_block = ""
    if contact_lines:
        contact_block = "\n\n" + "\n".join(contact_lines)

    intro_lines = build_invitation_intro_text_lines()
    return (
        "AcomOfferDesk\n\n"
        f"{chr(10).join(intro_lines)}"
        f"Поступила новая заявка №{request_id}.\n"
        f"Описание: {request_description}\n"
        f"Дедлайн: {deadline_label}\n\n"
        f"{PORTAL_BUTTON_LABEL}: {portal_url}\n"
        f"{contact_block}\n"
        f"Ссылка для входа: {portal_url}"
        f"{warning_block}\n"
    )


def _build_html(
    *,
    request_id: str,
    description: str | None,
    deadline_at: datetime,
    portal_url: str,
    contact: EmailContactInfo,
    attachment_warning: str | None,
) -> str:
    deadline_label, request_description = _request_header(
        request_id=request_id,
        description=description,
        deadline_at=deadline_at,
    )
    contact_html = build_contact_html_block(contact=contact)
    escaped_description = escape(request_description)
    escaped_portal_url = escape(portal_url)
    invitation_intro_html = build_invitation_intro_html()
    button_html = build_primary_button_html(label=PORTAL_BUTTON_LABEL, url=portal_url)
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
                {invitation_intro_html}
                Поступила новая заявка <strong>№{request_id}</strong>.<br/><br/>
                <strong>Описание:</strong> {escaped_description}<br/>
                <strong>Дедлайн:</strong> {deadline_label}
              </td>
            </tr>
            {button_html}
            {contact_html}
            {warning_html}
            <tr>
              <td style="padding:8px 28px 24px 28px;font-family:Arial,Helvetica,sans-serif;color:#374151;font-size:14px;line-height:22px;">
                Ссылка для входа:<br/>
                <a href="{escaped_portal_url}" style="color:#0969da;text-decoration:underline;word-break:break-all;">{escaped_portal_url}</a>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()
