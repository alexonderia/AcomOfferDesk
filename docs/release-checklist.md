# Чек-лист релиза

## Граница ответственности документа

Этот документ — практический чек-лист релиза для `test/prod` запуска.

Смежные документы:
- [Окружения](./environments.md)
- [Production: переменные окружения и секреты](./production-env.md)
- [Roadmap production-readiness](./release-preparation-tz.md)

## A. Ветки и продвижение

- [ ] Завершён merge `dev -> test`.
- [ ] Автодеплой test успешно прошёл на целевом VPS.
- [ ] Smoke-проверки на test выполнены.
- [ ] `test -> prod` одобрен и выполнен.
- [ ] Определён владелец hotfix-процедуры (плейсхолдер: закрепить цепочку incident-approval).

## B. Compose и env

- [ ] Команда dev-стека:
  `docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up -d --build`
- [ ] Команда local production-like:
  `docker compose --env-file .env.prod-like.local -f docker-compose.yml -f docker-compose.prod-like.yml up -d --build`
- [ ] Команда test perimeter:
  `docker compose --env-file .env.test -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.test.yml up -d --build`
- [ ] Команда prod perimeter:
  `docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up -d --build`
- [ ] Проверена итоговая конфигурация:
  `docker compose ... config`

## C. TLS и домен

- [ ] DNS указывает на reverse proxy хост.
- [ ] Установлен валидный TLS-сертификат.
- [ ] Настроен редирект HTTP `:80 -> :443`.
- [ ] Включён `Strict-Transport-Security`.
- [ ] Security headers настроены на внешнем reverse proxy.
- [ ] Настроен лимит размера body (`client_max_body_size`).

## D. Keycloak

- [ ] В test/prod не используется `start-dev`.
- [ ] `/iam` доступен только через публичный HTTPS-домен.
- [ ] `issuer` из OIDC discovery совпадает с `KEYCLOAK_ISSUER_URL`.
- [ ] Redirect URIs и Web Origins соответствуют публичному домену.
- [ ] Проверены realm/client/bootstrap admin и app users.

## E. Порты и firewall

- [ ] Публично открыты только `443` (или `80` + `443` с редиректом).
- [ ] Не открыты публично: `8000`, `8080` (Keycloak direct), `5432`, `5672`, `15672`, `9000`, `9001`, `5050`.
- [ ] Admin-only доступ идёт только через terminal server / VPN / private network.

## F. Секреты

- [ ] Нет default credentials (`guest/guest`, `minioadmin/minioadmin`).
- [ ] Заполнены все обязательные секреты из [production-env.md](./production-env.md).
- [ ] Реальные `.env` файлы не закоммичены.
- [ ] Назначены владельцы секретов и политика ротации.

## G. Smoke-проверки

- [ ] Открывается главная страница приложения.
- [ ] Работает login.
- [ ] Работает OIDC callback.
- [ ] Работает refresh/session restore.
- [ ] Работает logout.
- [ ] Открывается `/requests`.
- [ ] Открывается карточка заявки.
- [ ] Открывается workspace оффера (если есть тестовые данные).
- [ ] WebSocket работает через HTTPS (без ticket hardening на этом этапе).
- [ ] Работает upload-сценарий (если предусмотрен).
- [ ] RabbitMQ UI и MinIO Console недоступны из публичного интернета.

## H. Откат (плейсхолдер)

- [ ] Зафиксирован предыдущий стабильный git ref/image.
- [ ] Определены места просмотра логов (`docker compose logs`, reverse proxy logs).
- [ ] Задокументирована команда отката compose/env.
- [ ] Задокументированы и выполнимы post-rollback smoke-проверки.
