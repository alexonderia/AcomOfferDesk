# Production: переменные окружения и секреты

## Граница ответственности документа

Этот документ фиксирует production env/secrets contract, требования к секретам и ротации.

Смежные документы:
- [Окружения](./environments.md)
- [Чек-лист релиза](./release-checklist.md)
- [Аутентификация и онбординг](./auth-and-onboarding.md)

`.env.example` предназначен только для локальных/dev значений.  
Для production-like, test и prod используйте `.env.prod-like.example` как базовый контракт.

## Обязательный контракт Keycloak (test/prod)

- `KEYCLOAK_START_COMMAND=start`
- `KC_HTTP_RELATIVE_PATH=/iam`
- `KC_PROXY_HEADERS=xforwarded`
- `KC_HTTP_ENABLED=true` (TLS завершается на внешнем reverse proxy)
- `KC_HOSTNAME=https://<public-domain>/iam`
- `KEYCLOAK_PUBLIC_BASE_URL=https://<public-domain>/iam`
- `KEYCLOAK_ISSUER_URL=https://<public-domain>/iam/realms/acom-offerdesk`

Проверка OIDC discovery:

```bash
curl -fsSL https://app.example.com/iam/realms/acom-offerdesk/.well-known/openid-configuration
```

Проверьте, что `issuer` в ответе полностью совпадает с `KEYCLOAK_ISSUER_URL`.

## Инвентарь секретов

| Переменная окружения | Сервис | Назначение | Обязательность | Минимальные требования | Ротация без пересоздания данных | Что перезапускать после ротации |
|---|---|---|---|---|---|---|
| `DATABASE_URL` | backend | подключение к основной БД | да | сильный пароль БД, private host | обычно да | backend |
| `KC_DB_USERNAME` | keycloak | пользователь БД Keycloak | да | отдельный least-privilege user | обычно нет (зависит от политики БД) | keycloak, init jobs |
| `KC_DB_PASSWORD` | keycloak | пароль БД Keycloak | да | сильный случайный пароль | да | keycloak, init jobs |
| `KC_BOOTSTRAP_ADMIN_USERNAME` | keycloak bootstrap | имя bootstrap-админа | да | уникальное, не default | n/a после bootstrap | только keycloak_bootstrap |
| `KC_BOOTSTRAP_ADMIN_PASSWORD` | keycloak bootstrap | пароль bootstrap-админа | да | сильный случайный пароль | да | только keycloak_bootstrap |
| `KEYCLOAK_BOOTSTRAP_APP_PASSWORD` | keycloak bootstrap | пароль начального app superadmin | да | сильный случайный пароль | да | только keycloak_bootstrap |
| `JWT_SECRET` | backend | подпись legacy JWT | да | 64+ случайных символов | да | backend |
| `REFRESH_TOKEN_SECRET` | backend | отдельная подпись refresh-токена | опционально/рекомендуется | 64+ случайных символов | да (сбросит сессии) | backend |
| `EMAIL_VERIFICATION_SECRET` | backend | подпись токенов верификации email | да | 32+ случайных символов | да (старые ссылки станут недействительны) | backend |
| `EMAIL_REPLY_SECRET` / `REPLY_EMAIL_TOKEN_SECRET` | backend/worker | подпись reply-токенов | да, если включён reply flow | 32+ случайных символов | да (старые ссылки станут недействительны) | backend, notifications_worker |
| `TG_LINK_SECRET` | backend/tg legacy | подпись tg link-токенов | опционально (обязательно только при включённом legacy tg) | 32+ случайных символов | да | backend, tg_bot |
| `RABBITMQ_DEFAULT_USER` | rabbitmq | логин брокера | да | уникальный, не default | да | rabbitmq + зависимые сервисы |
| `RABBITMQ_DEFAULT_PASS` | rabbitmq | пароль брокера | да | сильный случайный пароль | да | rabbitmq + зависимые сервисы |
| `RABBITMQ_URL` | backend/worker | URL подключения AMQP | да | должен соответствовать реальным creds брокера | да | backend, notifications_worker |
| `MINIO_ROOT_USER` | minio | root-логин MinIO | да | уникальный, не default | да | minio + зависимые сервисы |
| `MINIO_ROOT_PASSWORD` | minio | root-пароль MinIO | да | сильный случайный пароль | да | minio + зависимые сервисы |
| `S3_ACCESS_KEY` | backend | access key для S3 | да | отдельный app key | да | backend |
| `S3_SECRET_KEY` | backend | secret key для S3 | да | сильный случайный пароль | да | backend |
| `EMAIL_APP_PASSWORD` | backend/worker | пароль приложения для SMTP | да | пароль приложения от провайдера | да | backend, notifications_worker |
| `SMTP_HOST` / `SMTP_PORT` / SMTP creds | backend/worker/keycloak | исходящая почта | да | TLS endpoint + валидная auth | да | backend, notifications_worker, keycloak |
| `IMAP_HOST` / `IMAP_PORT` / IMAP creds | backend/worker | mailbox polling | опционально | выделенный read account | да | backend, notifications_worker |

## Политика по credentials

- В test/prod запрещены: `guest/guest`, `minioadmin/minioadmin`, `start-dev`, публичные URL вида localhost.
- Плейсхолдеры `CHANGE_ME_*` допустимы только в `*.example` и должны быть заменены в реальных env-файлах.
- Реальные `.env.test`, `.env.prod`, `.env.prod-like.local` не должны попадать в git.
