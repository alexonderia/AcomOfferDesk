# AcomOfferDesk — инструкции для агентов

## Порядок работы

- Работайте непосредственно с кодом и актуальной документацией; Trellis, его skills, hooks и обязательные фазы больше не используются.
- Перед правкой проверьте ветку, `git status` и затрагиваемые файлы. Сохраняйте чужие незакоммиченные изменения.
- Читайте документы по теме задачи из `docs/README.md`; не загружайте весь архив или все инструкции перед каждой правкой.
- Для крупных изменений фиксируйте согласованный план; для обычной правки достаточно краткого плана и проверки результата.
- По умолчанию выполняйте задачу в основной сессии. Субагенты нужны только при явном запросе на делегирование.
- Сначала ищите существующий сервис, компонент, helper или контракт. Расширяйте существующего владельца поведения.
- Не выполняйте deploy, восстановление backup, изменение реальных данных, commit или push без соответствующего поручения.
- В конце сообщайте результат, выполненные проверки и ограничения. Исторические результаты тестов не подтверждают текущую версию.

## Структура и контракты

| Область | Назначение | Документ по теме |
|---|---|---|
| `backend/` | FastAPI, domain/service/repository, API DTO | `docs/development/backend-guidelines.md` |
| `web/` | React, TypeScript, Vite, MUI | `docs/development/frontend-guidelines.md` |
| `iam/` | Credentials, sessions, роли, permissions, grants | `docs/security/auth-and-onboarding.md` |
| Доступ и оргструктура | IAM permissions + локальный unit/resource scope | `docs/security/permissions-matrix.md` |
| Заявки и КП | Статусы, chosen offer, суммы, блокировки | `docs/development/request-offer-lifecycle.md` |
| `file_guard/` | Проверка файлов до сохранения | `docs/file-security.md` |
| `notifications_worker/`, `shared/` | Email и общие межсервисные контракты | `docs/development/notification-service.md` |
| `infra/`, compose | Gateway, сети, эксплуатация | `docs/operations/environments.md` |
| `deploy/order_database/` | Снимок миграций основной БД для rollout | `docs/operations/order-database-vps.md` |

## Архитектурные ограничения

- HTTP routes валидируют запрос, вызывают use case и сериализуют ответ; бизнес-решения принадлежат domain/services.
- Repositories отвечают за persistence. Транзакционные границы принадлежат `backend/app/core/uow.py`.
- Frontend — тонкий клиент: permissions/actions из backend определяют доступность UI; сервер повторно проверяет каждую операцию.
- Отсутствующий action flag означает скрытое или недоступное действие.
- IAM — единственный runtime identity provider. Identity связывается только через активный `user_auth_accounts(provider='iam')`.
- Functional permissions берутся из проверенного IAM JWT. `users.id_role` не является их источником или fallback.
- Назначать роль «Оператор» при создании пользователя или смене роли может только суперадмин по проверенной IAM-роли; общие permissions и индивидуальные grants не отменяют этот инвариант.
- Индивидуальные grants хранятся в IAM и добавляются к permissions роли; удаление grant не отнимает право, унаследованное от роли.
- Unit hierarchy, memberships, business status и resource policies остаются в Acom.
- Session bootstrap, refresh и logout идут через BFF; SPA не хранит и не декодирует access/refresh tokens.
- Парольные операции идут через выделенные backend/IAM adapters; пароли и токены нельзя сохранять или логировать в Acom.
- Режим без почты — действующий контракт: `docs/operations/no-mail-accounts.md`. Не возвращайте обязательную email-зависимость в этот режим.
- При изменении доступа проследите IAM → auth context → service/policy → response actions → frontend guard.
- Синхронизируйте permission vocabulary, IAM seed, backend enforcement, DTO, frontend guards и соответствующие проверки.

## Runtime, БД и файлы

- `gateway` — единственная публичная точка входа: `/` → web, `/api/*` → backend, разрешённые `/iam/*` → IAM.
- Internal IAM API и сервисные/admin ports в test/prod извне закрыты; tunnel подключается к gateway.
- PostgreSQL — внешний runtime через external Docker network `project_net`; не добавляйте его в основной compose без задачи на изменение окружения.
- `file_guard` — отдельный внутренний сервис с минимальным env, без DB/IAM/MinIO secrets.
- Все uploads, включая byte sources, проходят общий guard до MinIO и DB links; ошибка scanner/antivirus завершается fail-closed.
- HTTP upload подготавливается один раз и передаётся сервисам как `PreparedUpload`.
- Email, business events и delivery results сохраняют существующие RabbitMQ-контракты; меняйте publisher/shared/consumer согласованно.
- Внешние messenger bots удалены из runtime. Совместимые provider/channel значения в БД не означают работающую интеграцию.
- Не меняйте схему без требования задачи. Изменения схемы сопровождаются миграцией и порядком rollout.
- Существующие Flyway-миграции не удаляются как «старые документы» и не переписываются из-за возраста.
- Не полагайтесь на предполагаемое ручное состояние БД; проверяйте фактические schema/API контракты.
- Не добавляйте production stubs, фиктивные данные, debug-only поведение или hardcoded secrets.

## UI и язык

- Пользовательские labels, валидация, ошибки, toast, IAM формы и письма — на русском.
- Технические identifiers, permission codes, API paths и имена переменных могут оставаться английскими.
- Ошибки UI не должны раскрывать SQL, traceback, JWT, SMTP/RabbitMQ details или raw permission codes.
- Используйте общие поля форм, dialog chrome и toast helpers; не размножайте одинаковую валидацию и API clients.
- Состояние и side effects принадлежат feature hooks/providers; подписки и polling очищаются владельцем.
- Контракты wire DTO определяет backend; преобразование выполняется на границе API, без параллельных несовместимых типов.
- При изменении UI проверяйте desktop/mobile, keyboard доступность и disabled/error/loading состояния затронутых элементов.

## Проверки

- Запускайте минимальный достаточный набор проверок по изменению; полный release gate нужен для подготовки релиза.
- Backend unit: `./scripts/test-unit.ps1` или `./scripts/test-unit.sh`.
- Backend integration: `./scripts/test-integration.ps1` или `./scripts/test-integration.sh`.
- IAM: установите `PYTHONPATH=iam` и запустите `python -m pytest iam/tests -q` из окружения проекта.
- Frontend: `npm --prefix web run lint`, `npm --prefix web run test:unit`, `npm --prefix web run build`.
- Документация: `python scripts/check_docs.py`; русские тексты: `python scripts/check_mojibake.py`.
- Compose: `docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml config --quiet`.
- Полный порядок, live smoke, E2E credentials и ограничения — `docs/development/testing-strategy.md`.
- Live/E2E проверки требуют выделенных тестовых данных; не запускайте seed или destructive smoke на реальных данных.

## Документация и история

- `docs/` содержит актуальные тематические документы; точка входа — `docs/README.md`.
- `docs/qa/` содержит повторяемые ручные сценарии; `docs/reports/` — датированные результаты и наблюдения.
- `docs/archive/` хранит предыдущие решения, завершённые планы, старые выгрузки и backups; это не источник текущего поведения.
- Называйте новые отчёты `YYYY-MM-DD-topic.ext`, указывайте версию/ветку, окружение, выполненные проверки и ограничения.
- Исправляйте документ при изменении его контракта; поддерживайте один источник описания вместо копий.
- Личные `.env`, локальный архив контекста и секреты не публикуются. `.gitignore` не ограничивает чтение файлов агентом.
