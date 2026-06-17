SERVICE_UNAVAILABLE = "Сервис временно недоступен. Попробуйте позже."

BOT_WELCOME = (
    "Добро пожаловать в AcomOfferDesk.\n\n"
    "Введите команду /start или /info в поле сообщения."
)

def format_register_intro(*, existing_account_link_token: str | None) -> str:
    lines = [
        "Вы еще не зарегистрированы в системе.",
        "",
        "Если это новый аккаунт, пройдите регистрацию по кнопке ниже.",
    ]
    if existing_account_link_token:
        lines.extend(
            [
                "",
                "Если аккаунт в системе уже есть, войдите в него через сайт и укажите в профиле ваш MAX ID:",
                existing_account_link_token,
            ]
        )
    return "\n".join(lines)

PENDING_REVIEW = (
    "Ваша регистрация получена и ожидает проверки.\n\n"
    "После подтверждения доступа вы сможете получать открытые заявки через MAX."
)

NO_OPEN_REQUESTS = "Сейчас нет доступных открытых заявок."

OPEN_REQUESTS_HEADER = "Доступные открытые заявки:"

BLOCKED_ACCESS = (
    "Доступ к системе ограничен.\n\n"
    "Для уточнения статуса обратитесь к администратору."
)

INFO_TEXT = (
    "MAX-бот AcomOfferDesk помогает получать доступные заявки и быстро переходить в систему.\n\n"
    "Что можно сделать:\n"
    "• пройти регистрацию;\n"
    "• проверить статус доступа;\n"
    "• открыть доступные заявки после подтверждения регистрации.\n\n"
    "Для начала работы отправьте команду /start."
)


def format_request_message(*, request_id: str, description: str | None, deadline_at: str | None) -> str:
    title = description or "Описание отсутствует."
    deadline_line = f"Срок: {deadline_at}" if deadline_at else "Срок: не указан"
    return f"Заявка №{request_id}\n{title}\n{deadline_line}"
