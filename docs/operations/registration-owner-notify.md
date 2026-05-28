# Уведомление владельцу о новой регистрации

Цепочка (как IAM-алерты): **backend** → **incident-relay** → **YouGile** → **Hermes vps** → Telegram `@Hermes_koara_bot`.

Не используется max-bot-log и не связано с MAX messenger.

## Env (`/opt/acome-offer-desk/backend/.env`)

```env
REGISTRATION_NOTIFY_ENABLED=true
REGISTRATION_NOTIFY_URL=http://incident-relay:8080/ingest/registration
REGISTRATION_NOTIFY_SERVICE=acom-registration
# REGISTRATION_NOTIFY_TOKEN=   # только если на relay задан REGISTRATION_INGEST_TOKEN
```

Backend и `incident-relay` должны быть в одной Docker-сети (`project_net`).

## Источники регистрации

| `source` | Когда |
|----------|--------|
| `contractor_tg` | Telegram-регистрация контрагента |
| `admin_register` | Создание сотрудника в админке |
| `oidc_invite` | Первый вход по invite Keycloak |
| `manual_contractor` | Ручной контрагент в админке |

Текст уведомления включает сверку прав по `backend/app/domain/permissions.py` и роль Keycloak `app.*`.

## Relay

Репозиторий `vvv-web/sherlockops-incident-relay`, endpoint `POST /ingest/registration`, маршрут `services.acom-registration` в `config/incident-routing.yml`. См. `docs/REGISTRATION_INGEST.md` в том репо.

## Деплой

1. `git pull` relay + пересборка `incident-relay` (acome-monitoring compose).
2. `git pull` приложение, пересборка `backend`, env выше.
3. Koara: Hermes vps с `HERMES_TRIGGER_MODE=http` (уже для алертов).
