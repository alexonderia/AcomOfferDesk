# Стратегия тестирования

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
[`req-003-request-closure.md`](req-003-request-closure.md).

## Live smoke

Основные проверки 47 исходных QA-сценариев автоматизированы в `web/e2e/qa47.regression.spec.ts`. Генератор `backend/tests/runtime/seed_qa47.py` создаёт отдельный набор для локального стека без почты; credentials не хранятся в Git. [Метод, воспроизведение и границы покрытия](../qa/expanded-regression-2026-11-02.md). Чат проверяется в двух браузерных контекстах, включая восстановление сети и запрет кадров на открытом WebSocket после отзыва членства.

PostgreSQL-регресс новой миграции: `backend/tests/sql/qa_v108_regression.sql` запускать через `psql -v ON_ERROR_STOP=1` на мигрированной копии. Fixtures откатываются транзакцией. Сквозные тесты режима без почты — `web/e2e/no-mail.remediation.spec.ts`; переключение на включённую почту — `email-mode-transition.spec.ts`. Они требуют `E2E_QA_CREDENTIALS` с отдельными тестовыми identity, второй также требует `E2E_EXPECT_EMAIL_ENABLED=true` и управляемого почтового окружения. [Фактические результаты и ограничения](../qa/runtime-verification-2026-11-02.md).

Регрессия ручного QA и режима без почты: [чеклист](../qa/no-mail-regression-checklist.md), [результаты реализации](../qa/remediation-progress.md). Новые тесты покрывают прямую выдачу credentials, идемпотентность без сброса, смену пароля и отзыв refresh/browser sessions, отсутствие почтовых обращений, точный ИНН, сохранение автора/времени feedback и пересчёт chat memberships. Repository-тесты используют SQLite; выполнение PostgreSQL-функции требует отдельной проверки на PostgreSQL.

`scripts/smoke-infra.*` работает с поднятым stack. `scripts/check-iam.*` сверяет и при явном repair синхронизирует RBAC. E2E требует заранее подготовленные IAM credentials; автоматического identity-provider provisioning нет.
