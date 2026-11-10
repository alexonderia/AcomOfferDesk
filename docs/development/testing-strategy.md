# Стратегия тестирования

## Команды и окружение

- Backend unit: `./scripts/test-unit.ps1` или `./scripts/test-unit.sh`.
- Backend integration: `./scripts/test-integration.ps1` или `./scripts/test-integration.sh`.
- IAM: `PYTHONPATH=iam python -m pytest iam/tests -q`; в PowerShell сначала `$env:PYTHONPATH = (Resolve-Path iam).Path`.
- Frontend: `npm --prefix web run lint`, `npm --prefix web run test:unit`, `npm --prefix web run build`.
- Локальные ссылки документации: `python scripts/check_docs.py` (также выполняется в CI).
- Русские тексты: `python scripts/check_mojibake.py`.
- Release gate: `./scripts/test-release.ps1 -EnvFile .env.dev` или `ENV_FILE=.env.dev ./scripts/test-release.sh`; E2E включается отдельным флагом.

Python-команды выполняются в окружении проекта с установленными зависимостями. Указывайте `PYTHONPATH` для соответствующего пакета, поскольку backend и IAM запускаются раздельно.

## Локальный обязательный контур

1. Backend unit/integration tests.
2. IAM tests.
3. Frontend lint, unit tests and build.
4. Automated forbidden runtime integration scan:
   `backend/tests/unit/test_forbidden_integrations.py`.
5. `docker compose ... config` for supported overlays.

## Security focus

Проверяются local RS256 validation с ACTIVE/RETIRING key ring,
issuer/audience/kid, expiry, required claims, IAM binding, blocked
user/account, refresh rotation/revoke, logout, CSRF, live/readiness и
недоступность IAM. Любая ошибка должна завершаться fail-closed.

## Authorization focus

Проверяются effective permissions из IAM, individual grants, role-inherited permissions после удаления grant, неизвестные permissions, Acom unit hierarchy, request/offer visibility и domain policies. `users.id_role` не должен создавать permissions.

### Видимость Request для Contractor

Новая заявка, созданная Operator и остающаяся на Operator, является внутренней
рабочей заявкой: Contractor не видит её в списке, не открывает contractor view
и не создаёт Offer, в том числе при общем root unit. После штатного назначения
владельца не-Operator применяются
существующие ограничения root-unit scope и hidden contractors; только
допустимый Contractor получает доступ к заявке и видит её текущего
ответственного. Это правило защищается lifecycle regression tests и не требует
отдельного publication/status механизма. AOD-BL-002 является Specification
Sync / Regression Protection, а не production defect: текущая роль Operator
служит только отрицательным lifecycle-invariant, а не whitelist ролей для
публикации.

### REQ-003: закрытие Request и final_amount

При ненулевом `initial_amount` сервер разрешает закрытие только с исходной
суммой либо с суммой принятого Offer, если она указана. Нулевой `initial_amount`
сохраняет особое правило: итоговая сумма должна быть положительной. Создание
Request без initial amount запрещено. Неразрешённый `submitted` Offer блокирует закрытие; при ошибке
не изменяются `status`, `closed_at` и `id_offer`. Полный ручной и API-кейс:
[`req-003-request-closure.md`](../qa/manual-regression.md).

## Live smoke

Основные проверки 47 исходных QA-сценариев автоматизированы в `web/e2e/qa47.regression.spec.ts`. Генератор `backend/tests/runtime/seed_qa47.py` создаёт отдельный набор для локального стека без почты; credentials не хранятся в Git. [Метод, воспроизведение и границы покрытия](../reports/qa/2026-11-02-expanded-regression.md). Чат проверяется в двух браузерных контекстах, включая восстановление сети и запрет кадров на открытом WebSocket после отзыва членства.

PostgreSQL-регресс новой миграции: `backend/tests/sql/qa_v108_regression.sql` запускать через `psql -v ON_ERROR_STOP=1` на мигрированной копии. Fixtures откатываются транзакцией. Сквозные тесты режима без почты — `web/e2e/no-mail.remediation.spec.ts`; переключение на включённую почту — `email-mode-transition.spec.ts`. Они требуют `E2E_QA_CREDENTIALS` с отдельными тестовыми identity, второй также требует `E2E_EXPECT_EMAIL_ENABLED=true` и управляемого почтового окружения. [Фактические результаты и ограничения](../reports/qa/2026-11-02-runtime-verification.md).

Регрессия ручного QA и режима без почты: [чеклист](../archive/qa/2026-11-10-no-mail-regression-checklist.md), [результаты реализации](../archive/qa/2026-11-02-remediation-progress.md). Новые тесты покрывают прямую выдачу credentials, идемпотентность без сброса, смену пароля и отзыв refresh/browser sessions, отсутствие почтовых обращений, точный ИНН, сохранение автора/времени feedback и пересчёт chat memberships. Repository-тесты используют SQLite; выполнение PostgreSQL-функции требует отдельной проверки на PostgreSQL.

`scripts/smoke-infra.*` работает с поднятым stack. `scripts/check-iam.*` сверяет и при явном repair синхронизирует RBAC. E2E требует заранее подготовленные IAM credentials; автоматического identity-provider provisioning нет.

## Каталог тестов

- `backend/tests/unit` — domain/service/auth unit tests;
- `backend/tests/integration` — FastAPI and cross-service contracts with fakes;
- `iam/tests` — credentials, token/session security, RBAC and grants;
- `web/src/**/*.test.ts(x)` — frontend unit/component tests;
- `web/e2e` — Playwright smoke/extended scenarios;
- `scripts/smoke-infra.*` — live environment connectivity and public perimeter;
- `scripts/check-iam.*` — IAM RBAC seed report and account reconciliation;
- `scripts/test-release.*` — aggregated release gate.

E2E login uses `/api/v1/auth/login` and prepared IAM credentials. Test scripts do not create accounts through a removed identity provider.

## Test coverage map

| Контур | Основное покрытие |
|---|---|
| IAM credentials, sessions, refresh/revoke | `iam/tests/test_authentication_flow.py`, `iam/tests/test_api_security.py` |
| Role permissions и individual grants | `iam/tests/test_permission_grants.py`, backend delegation tests |
| JWT issuer/audience/kid/expiry/unknown claims | `backend/tests/unit/test_iam_authentication_unit.py` |
| BFF callback/refresh/logout/cookies/CSRF | backend auth integration/unit tests |
| IAM binding only | `backend/tests/unit/test_iam_authentication_unit.py` |
| Unit scope и domain policies | backend service/policy/integration tests |
| Frontend session/permission guards | `web/src/**/*.test.ts(x)` |
| Browser login/logout | `web/e2e/auth.smoke.spec.ts` |
| Compose/runtime smoke | `backend/app/scripts/smoke_services.py`, `scripts/smoke-infra.*` |

Security regression должна оставаться fail-closed для invalid/expired JWT, неверных issuer/audience/kid, отсутствующего IAM binding, blocked account, revoked refresh, CSRF failures и IAM unavailability.

## Auth test scenarios

- valid IAM login creates HttpOnly session cookies;
- invalid password and blocked account do not create a session;
- missing IAM binding rejects an otherwise valid token;
- invalid/expired token, issuer, audience, algorithm or kid returns unauthorized/unavailable without fallback;
- refresh rotates the session; revoked/expired refresh clears it;
- logout is idempotent and clears local cookies;
- role changes and individual grant add/remove appear after token/session refresh;
- removal of an individual grant preserves the same permission when it is inherited from the role;
- unknown permissions are rejected;
- missing/invalid CSRF blocks state-changing calls;
- IAM outage fails closed;
- unit hierarchy and request/offer visibility remain enforced by Acom policies.
