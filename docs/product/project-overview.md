# AcomOfferDesk

AcomOfferDesk — monorepo приложения для заявок, предложений, подрядчиков, файлов, чатов, планов и уведомлений.

## Пакеты

- `backend` — FastAPI API и business/domain authorization;
- `web` — React клиент;
- `iam` — аутентификация, role permissions и individual grants;
- `notifications_worker` — асинхронная доставка email;
- `file_guard` — проверка загружаемых файлов;
- `shared` — общие межсервисные контракты;
- `infra` — gateway и runtime infrastructure.

## Ownership

- IAM владеет credentials, sessions, system roles, role permissions и account grants.
- Acom владеет users business records, units, memberships, data scope и domain policies.
- Frontend использует backend-provided permissions/actions только для UX; backend остаётся enforcement point.
