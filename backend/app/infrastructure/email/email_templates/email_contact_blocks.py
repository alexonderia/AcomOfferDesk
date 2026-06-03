from __future__ import annotations

from dataclasses import dataclass
from html import escape


@dataclass(frozen=True, slots=True)
class EmailContactInfo:
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    phone_label: str = "Тел. (MAX)"

    @property
    def has_any(self) -> bool:
        return bool(self.name or self.email or self.phone)


DEFAULT_INVITATION_CONTACT = EmailContactInfo(
    name="Владислав Хлистун",
    email="VKhlistun@alabuga.ru",
    phone="+7 927 455-80-89",
)


def build_contact_text_block(*, contact: EmailContactInfo, intro: str | None = None) -> list[str]:
    if not contact.has_any:
        return []

    lines: list[str] = []
    if intro:
        lines.append(intro)
    if contact.name:
        lines.append(contact.name)
    if contact.phone:
        lines.append(f"{contact.phone_label}: {contact.phone}")
    if contact.email:
        lines.append(f"Эл. почта: {contact.email}")
    return lines


def build_contact_html_block(
    *,
    contact: EmailContactInfo,
    intro: str = "Если удобнее, вы можете связаться с контактным лицом напрямую:",
) -> str:
    if not contact.has_any:
        return ""

    parts: list[str] = [escape(intro), "<br/><br/>"]
    if contact.name:
        parts.append(f"<strong>{escape(contact.name)}</strong><br/>")
    if contact.phone:
        tel_href = _phone_href(contact.phone)
        parts.append(
            f"{escape(contact.phone_label)}: "
            f'<a href="{tel_href}" style="color:#0969da;text-decoration:underline;">'
            f"{escape(contact.phone)}</a><br/>"
        )
    if contact.email:
        escaped_email = escape(contact.email)
        parts.append(
            "Эл. почта: "
            f'<a href="mailto:{escaped_email}" style="color:#0969da;text-decoration:underline;">'
            f"{escaped_email}</a>"
        )

    body = "".join(parts)
    return f"""
            <tr>
              <td style="padding:16px 28px 0 28px;font-family:Arial,Helvetica,sans-serif;color:#374151;font-size:14px;line-height:22px;">
                {body}
              </td>
            </tr>
    """.rstrip()


def build_primary_button_html(*, label: str, url: str) -> str:
    escaped_url = escape(url)
    escaped_label = escape(label)
    return f"""
            <tr>
              <td style="padding:24px 28px 8px 28px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                  <tr>
                    <td bgcolor="#0969da" style="border-radius:6px;">
                      <a href="{escaped_url}" style="display:inline-block;padding:12px 20px;font-family:Arial,Helvetica,sans-serif;font-size:16px;color:#ffffff;text-decoration:none;">
                        {escaped_label}
                      </a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
    """.rstrip()


def _phone_href(phone: str) -> str:
    digits = "".join(character for character in phone if character.isdigit() or character == "+")
    return escape(f"tel:{digits}" if digits else phone)


def _normalize_contact_field(value: str | None) -> str | None:
    normalized = (value or "").strip()
    return normalized or None


def contact_info_from_invitation_settings(
    *,
    contact_name: str | None,
    contact_email: str | None,
    contact_phone: str | None,
) -> EmailContactInfo:
    """Build contact block for invitation/registration emails.

    Uses INVITATION_CONTACT_* from settings when set; otherwise falls back to the
    default contact person so unregistered recipients always see support details.
    """
    return EmailContactInfo(
        name=_normalize_contact_field(contact_name) or DEFAULT_INVITATION_CONTACT.name,
        email=_normalize_contact_field(contact_email) or DEFAULT_INVITATION_CONTACT.email,
        phone=_normalize_contact_field(contact_phone) or DEFAULT_INVITATION_CONTACT.phone,
        phone_label=DEFAULT_INVITATION_CONTACT.phone_label,
    )
