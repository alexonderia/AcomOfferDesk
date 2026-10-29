# Backend AcomOfferDesk

FastAPI backend отвечает за HTTP API, бизнес-политики, unit scope, хранение данных, файлы, уведомления и интеграцию с IAM.

## Слои

- `app/api/v1` — маршруты и HTTP-контракты;
- `app/domain` — permissions, политики и auth context;
- `app/services` — orchestration сценариев;
- `app/repositories` — доступ к данным;
- `app/infrastructure` — IAM, email и внешние адаптеры;
- `app/core/uow.py` — транзакционные границы.

## Аутентификация

Browser flow начинается через `GET /api/v1/auth/login`, проходит через IAM и завершается на `GET /api/v1/auth/callback`. Backend хранит access/refresh tokens только в HttpOnly cookies, локально проверяет подпись access token и связывает `sub` только через активную запись `user_auth_accounts(provider='iam')`.

Основные endpoints:

- `GET /api/v1/auth/login`;
- `GET /api/v1/auth/callback`;
- `GET /api/v1/auth/session`;
- `POST /api/v1/auth/refresh`;
- `POST /api/v1/auth/logout`;
- `GET /api/v1/auth/csrf`.

## Авторизация

- functional permissions приходят в проверенном IAM access token;
- индивидуальные grants хранятся в IAM и входят в effective permissions;
- `users.id_role` не вычисляет permissions;
- unit hierarchy, memberships и data scope остаются в Acom;
- бизнес-ограничения реализуются domain policies.

## Проверка

```powershell
$env:PYTHONPATH = (Resolve-Path backend).Path
.\.venv\Scripts\python.exe -m pytest backend/tests -q
```
