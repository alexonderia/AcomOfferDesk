from __future__ import annotations

from datetime import datetime

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, Message, ReplyKeyboardMarkup

from app.services.backend_client import BackendClientError, get_backend_client

router = Router()


def _is_access_blocked(*, tg_status: str | None, user_status: str | None) -> bool:
    if tg_status == "disapproved":
        return True
    if user_status in {"inactive", "blacklist"}:
        return True
    return False

def _format_deadline(deadline_at: str) -> str:
    normalized = deadline_at.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return deadline_at
    return parsed.strftime("%d.%m.%Y, %H:%M")


def _quick_actions_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/start"), KeyboardButton(text="/info")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите команду",
    )


@router.message(Command("info"))
async def handle_info(message: Message) -> None:
    if not message.from_user:
        return

    try:
        client = get_backend_client()
        result = await client.start(message.from_user.id)
    except BackendClientError:
        await message.answer("Сервис временно недоступен. Попробуйте позже.", protect_content=True)
        return

    if _is_access_blocked(tg_status=result.tg_status, user_status=result.user_status):
        await message.answer(
            "⛔ Доступ к Telegram-боту ограничен. Обратитесь к администратору.",
            protect_content=True,
        )
        return


    await message.answer(
        "ℹ️ О сервисе\n"
        "Этот бот помогает контрагентам быстро перейти к регистрации и авторизации в веб-сервисе.\n\n"
        "Как это работает:\n"
        "1. Нажмите /start.\n"
        "2. Если вы новый пользователь, получите кнопку регистрации.\n"
        "3. После регистрации ваши данные переходят на проверку.\n"
        "4. После активации доступа бот покажет открытые заявки и ссылки для входа.",
        reply_markup=_quick_actions_keyboard(),
        protect_content=True,
    )


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    if not message.from_user:
        return

    try:
        client = get_backend_client()
        result = await client.start(message.from_user.id)
    except BackendClientError:
        await message.answer("Сервис временно недоступен. Попробуйте позже.", protect_content=True)
        return
    
    if _is_access_blocked(tg_status=result.tg_status, user_status=result.user_status):
        await message.answer(
            "⛔ Доступ к Telegram-боту ограничен. Обратитесь к администратору.",
            protect_content=True,
        )
        return

    if result.action == "open_requests":
        await message.answer(
            "✅ Ваш доступ активен. Ниже опубликованы актуальные открытые заявки.",
            reply_markup=_quick_actions_keyboard(),
            protect_content=True,
        )
        if not result.requests:
            await message.answer(
                "Сейчас открытых заявок нет. Мы сообщим, когда появятся новые.",
                protect_content=True,
            )
            return
        
        for request in result.requests:
            description = request.description or "Описание отсутствует."
            link = request.link
            if not link or len(link) > 256:
                await message.answer("Ссылка на сервис временно недоступна. Попробуйте позже.", protect_content=True)
                return
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Перейти в сервис", url=link)],
                ]
            )
            deadline_text = _format_deadline(request.deadline_at)
            await message.answer(
                f"Заявка №{request.request_id}\n\n📝 Описание: {description}\n⏰ Дедлайн приёма КП: {deadline_text}",
                reply_markup=keyboard,
                protect_content=True,
            )
        return

    if result.action == "pending":
        await message.answer(
            "🕒 Регистрация завершена, данные обрабатываются службой безопасности.\n"
            "Когда доступ будет изменён, вы получите уведомление.",
            reply_markup=_quick_actions_keyboard(),
            protect_content=True,
        )
        return

    if result.action == "register":
        url = result.registration_link
        if not url:
            await message.answer(
                "Ссылка на регистрацию временно недоступна. Пожалуйста, попробуйте позже.",
                protect_content=True,
            )
            return
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="📝 Зарегистрироваться", url=url)]],
        )
        await message.answer(
            "👋 Добро пожаловать в сервис закупок.\n\n"
            "Чтобы получать доступ к заявкам и чату, пройдите регистрацию в веб-сервисе по кнопке ниже.",
            reply_markup=_quick_actions_keyboard(),
            protect_content=True,
        )
        await message.answer(
            "После отправки анкеты вы получите уведомление о результате проверки.",
            reply_markup=keyboard,
            protect_content=True,
        )
        return

    await message.answer(
        "Не удалось обработать запрос. Попробуйте позже.",
        reply_markup=_quick_actions_keyboard(),
        protect_content=True,
    )
