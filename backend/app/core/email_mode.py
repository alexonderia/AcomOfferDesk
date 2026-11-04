from app.core.config import settings
from app.domain.exceptions import Conflict


def ensure_email_enabled() -> None:
    if not settings.email_enabled:
        raise Conflict("Почтовый сервис отключён. Приложение работает в режиме без почты.")
