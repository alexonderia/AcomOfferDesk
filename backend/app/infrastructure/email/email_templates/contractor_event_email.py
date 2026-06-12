from __future__ import annotations

from html import escape

from app.infrastructure.email.email_message_payload import EmailMessagePayload
from app.infrastructure.email.email_templates.email_contact_blocks import build_primary_button_html
from shared.notification_copy import NOTIFICATION_BUTTON_LABEL


def build_contractor_event_email_payload(
    *,
    to_email: str,
    subject: str,
    body_text: str,
    body_html: str,
    action_url: str | None = None,
    action_label: str = NOTIFICATION_BUTTON_LABEL,
) -> EmailMessagePayload:
    return EmailMessagePayload(
        to_email=to_email,
        subject=subject,
        text_content=_build_text(body_text=body_text, action_url=action_url, action_label=action_label),
        html_content=_build_html(body_html=body_html, action_url=action_url, action_label=action_label),
    )


def _build_text(*, body_text: str, action_url: str | None, action_label: str) -> str:
    lines = ["AcomOfferDesk", "", body_text.strip(), ""]
    if action_url:
        lines.append(f"{action_label}: {action_url}")
    lines.append("")
    return "\n".join(lines)


def _build_html(*, body_html: str, action_url: str | None, action_label: str) -> str:
    button_html = build_primary_button_html(label=action_label, url=action_url) if action_url else ""
    fallback_html = (
        f"""
            <tr>
              <td style="padding:8px 28px 0 28px;font-family:Arial,Helvetica,sans-serif;color:#374151;font-size:14px;line-height:22px;">
                Если кнопка не работает, откройте ссылку вручную:<br/>
                <a href="{escape(action_url)}" style="color:#0969da;text-decoration:underline;word-break:break-all;">{escape(action_url)}</a>
              </td>
            </tr>
        """.rstrip()
        if action_url
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
                {body_html}
              </td>
            </tr>
            {button_html}
            {fallback_html}
            <tr>
              <td style="padding:8px 28px 24px 28px;"></td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()
