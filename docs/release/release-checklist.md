# Чек-лист релиза

## Граница ответственности документа

Этот документ — практический чек-лист релиза для `test/prod` запуска.

Смежные документы:
- [Окружения](../operations/environments.md)
- [Production: переменные окружения и секреты](./production-env.md)
- [Roadmap production-readiness](./release-preparation-tz.md)

## A. Ветки и продвижение

- [ ] Для target commit в `dev_process/dev/test` успешно прошел CI (`backend unit` + `backend integration` + `frontend lint` + `frontend unit` + `frontend build`).
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

- [ ] Выполнены backend unit и integration тесты (локально/в CI артефактах).
- [ ] Для релизов, затрагивающих requests/offers/chat/users enforcement, подтвержден проход integration suites:
  `test_request_lifecycle_integration.py`, `test_offer_lifecycle_integration.py`,
  `test_chat_endpoints_integration.py`, `test_admin_users_enforcement_integration.py`.
- [ ] Для релизов, затрагивающих dashboard/files/feedback/normative/auth-email contracts, подтвержден проход
  `backend/tests/integration/test_p1_backend_contract_gaps_integration.py`.
- [ ] CI для target commit зеленый: backend unit, backend integration/API contracts, frontend lint, frontend unit/component tests, frontend build.
- [ ] На поднятом стенде выполнены `smoke-infra` и `check-keycloak` через локальные скрипты или workflow `Release Smoke (Manual)`.
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
- [ ] E2E smoke выполнен вручную через `scripts/e2e-smoke.*` или workflow `E2E Smoke (Manual)` на поднятом стенде.
- [ ] Extended e2e suites (`@roles`, `@registration`, `@request-offer`, `@dashboard`, `@files-chat`) выполнены вручную, если релиз затрагивает role UX/access, dashboard behavior, request-offer lifecycle или files/chat.
- [ ] Release smoke workflow `Release Smoke (Manual)` выполнен на поднятом стенде (обязательные `smoke-infra` + `check-keycloak`, optional e2e через `include_e2e=true`).
- [ ] Email tests прошли без реальной внешней отправки (`fake transport`/`fake outbox`, без real SMTP creds в CI), включая request-email-verification и `/auth/verify-email` lifecycle в backend integration.
- [ ] Подтверждено, что CI/workflows не отправляют реальные письма наружу.
- [ ] Если в окружении есть MailHog/Mailpit: выполнен mailbox smoke (письмо попало в test inbox).

PowerShell-команды для ручной проверки:
- `./scripts/smoke-infra.ps1 -EnvFile .env.dev`
- `./scripts/check-keycloak.ps1 -EnvFile .env.dev`
- `./scripts/e2e-smoke.ps1 -EnvFile .env.dev -ProvisionUsers`
- `./scripts/test-release.ps1 -EnvFile .env.dev -IncludeE2E -ProvisionE2EUsers`

Bash-команды для ручной проверки:
- `./scripts/smoke-infra.sh .env.dev`
- `./scripts/check-keycloak.sh .env.dev`
- `ENV_FILE=.env.dev PROVISION_USERS=true ./scripts/e2e-smoke.sh`
- `ENV_FILE=.env.dev INCLUDE_E2E=true PROVISION_E2E_USERS=true ./scripts/test-release.sh`

## H. Откат (плейсхолдер)

- [ ] Зафиксирован предыдущий стабильный git ref/image.
- [ ] Определены места просмотра логов (`docker compose logs`, reverse proxy logs).
- [ ] Задокументирована команда отката compose/env.
- [ ] Задокументированы и выполнимы post-rollback smoke-проверки.
- [ ] Rollback notes включают предыдущий image/ref, env-файл, порядок `docker compose ... down/up`, проверку `smoke-infra`, `check-keycloak` и краткую ручную проверку login/request flow после отката.
