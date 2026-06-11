from __future__ import annotations

from maxapi.types.attachments.buttons.link_button import LinkButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder


def registration_keyboard(url: str | None):
    if not url or not url.startswith(("http://", "https://")):
        return None
    builder = InlineKeyboardBuilder()
    builder.row(LinkButton(text="Зарегистрироваться", url=url))
    return builder.as_markup()


def request_keyboard(url: str | None):
    if not url or not url.startswith(("http://", "https://")):
        return None
    builder = InlineKeyboardBuilder()
    builder.row(LinkButton(text="Открыть заявку", url=url))
    return builder.as_markup()


def open_system_keyboard(url: str | None):
    if not url or not url.startswith(("http://", "https://")):
        return None
    builder = InlineKeyboardBuilder()
    builder.row(LinkButton(text="Открыть систему", url=url))
    return builder.as_markup()
