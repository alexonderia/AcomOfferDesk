from __future__ import annotations

from html import escape

from shared.notification_copy import NOTIFICATION_BUTTON_LABEL

INVITATION_GREETING = "Вы приглашены к работе в системе AcomOfferDesk."
INSTRUCTION_LINE = (
    "Инструкция по получению доступа приложена к письму в виде презентации."
)
PORTAL_BUTTON_LABEL = NOTIFICATION_BUTTON_LABEL


def build_invitation_intro_text_lines() -> list[str]:
    return [
        INVITATION_GREETING,
        INSTRUCTION_LINE,
        "",
    ]


def build_invitation_intro_html() -> str:
    return (
        f"{escape(INVITATION_GREETING)}<br/><br/>"
        f"{escape(INSTRUCTION_LINE)}<br/><br/>"
    )
