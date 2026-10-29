from __future__ import annotations


class IamError(Exception):
    status_code = 400
    public_detail = "Некорректный запрос"


class InvalidCredentials(IamError):
    status_code = 401
    public_detail = "Неверный логин или пароль"


class AccountUnavailable(InvalidCredentials):
    """Credentials are not usable because the account is not approved/active."""

    public_detail = "Доступ ограничен. Ожидайте подтверждения или обратитесь к администратору"


class Unauthorized(IamError):
    status_code = 401
    public_detail = "Сессия недействительна или истекла"


class Forbidden(IamError):
    status_code = 403
    public_detail = "Доступ запрещён"


class NotFound(IamError):
    status_code = 404
    public_detail = "Данные не найдены"


class Conflict(IamError):
    status_code = 409
    public_detail = "Конфликт данных"


class RateLimited(IamError):
    status_code = 429
    public_detail = "Слишком много попыток. Повторите позже"
