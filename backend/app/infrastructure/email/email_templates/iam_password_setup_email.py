from __future__ import annotations

from dataclasses import dataclass
from html import escape


@dataclass(frozen=True, slots=True)
class IamPasswordSetupEmail:
    subject: str
    text_content: str
    html_content: str


def build_iam_password_setup_email(*, setup_url: str, is_reset: bool = False) -> IamPasswordSetupEmail:
    title = "Восстановление доступа к AcomOfferDesk" if is_reset else "Создание пароля AcomOfferDesk"
    action = "установить новый пароль" if is_reset else "создать пароль для первого входа"
    safe_url = escape(setup_url, quote=True)
    return IamPasswordSetupEmail(
        subject=title,
        text_content=f"Чтобы {action}, откройте одноразовую ссылку:\n{setup_url}\n",
        html_content=(
            f"<p>Чтобы {escape(action)}, перейдите по ссылке:</p>"
            f'<p><a href="{safe_url}">Продолжить</a></p>'
            "<p>Ссылка одноразовая и действует ограниченное время.</p>"
        ),
    )
