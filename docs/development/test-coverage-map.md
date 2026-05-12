# Карта покрытия тестами

_Последнее обновление: 2026-05-12 (ветка `dev_process`)._

## Область и метод

Источники, проверенные в этой итерации:
- `backend/tests/unit`
- `backend/tests/integration`
- `web/src/**/*.test.ts`
- `web/src/**/*.test.tsx`
- `web/e2e`
- `.github/workflows`
- `scripts/test-*.*`
- `scripts/e2e-smoke.*`
- `scripts/smoke-infra.*`
- `scripts/check-keycloak.*`

Легенда:
- `Да` = есть прямое автоматизированное покрытие.
- `Частично` = покрыт только поднабор сценария/негативный путь/форма контракта.
- `Нет` = прямое автоматизированное покрытие не найдено в проверенной области.

## Auth / registration / onboarding

| Сценарий | Тест есть сейчас | Уровень | Файл(ы) тестов | Что не покрыто | Приоритет | Рекомендуемый следующий тест |
|---|---|---|---|---|---|---|
| OIDC callback: невалидный `state` / отсутствует `code` / отсутствует cookie | Да | integration | `backend/tests/integration/test_auth_oidc_flows.py` | Позитивный callback-путь с успешным sync/link | P0 | Добавить integration-тест успешного callback с валидным `state` и привязанной учеткой |
| Контракт refresh возвращает `permissions/app_roles/delegation_roles` | Да | integration, frontend unit | `backend/tests/integration/test_auth_session_contract.py`; `web/src/app/providers/AuthProvider.test.tsx` | Edge-case'ы срока жизни токена и конфликты ротации refresh | P0 | Добавить integration-кейс: ротация refresh token + обработка устаревшей cookie |
| Logout очищает сессию при сбоях провайдера | Да | integration, e2e smoke | `backend/tests/integration/test_auth_oidc_flows.py`; `web/e2e/auth.smoke.spec.ts` | Явная проверка инвалидирования backend-сессии после повторного logout | P1 | Добавить integration-тест на идемпотентную последовательность logout |
| Обработка mismatch invite при регистрации / already registered | Да | integration | `backend/tests/integration/test_auth_oidc_flows.py` | Успешный onboarding-путь регистрации (`review` + первый login UX) | P0 | Добавить integration-тест успешного завершения регистрации по invite |
| Гейтинг auth по статусам review/inactive/blacklist | Да | unit, integration | `backend/tests/unit/test_authorization_unit.py`; `backend/tests/integration/test_auth_enforcement_contract.py` | Матрица по всем защищенным endpoint'ам | P0 | Добавить параметризованную integration-матрицу ключевых защищенных endpoint'ов по статусам |

## Матрица role access

| Сценарий | Тест есть сейчас | Уровень | Файл(ы) тестов | Что не покрыто | Приоритет | Рекомендуемый следующий тест |
|---|---|---|---|---|---|---|
| Извлечение permissions из ролей Keycloak (`resource_access.<api>.roles`) | Да | unit | `backend/tests/unit/test_auth_context_unit.py` | Полная сверка с актуальной permission-матрицей по role profile | P0 | Добавить data-driven unit-тест сравнения role bundles со snapshot-моделью |
| Доступ по ролям на уровне маршрутов (admin/dashboard/feedback) | Да | e2e smoke, frontend unit | `web/e2e/roles.smoke.spec.ts`; `web/src/app/routes/RoleRoute.test.tsx` | Паритет backend-enforcement для каждой роли (не только frontend redirects) | P0 | Добавить backend integration-матрицу role vs endpoint |
| Поведение action-flags по ролям (request/offer/chat/user actions) | Да | unit, integration | `backend/tests/unit/test_action_builders_unit.py`; `backend/tests/integration/test_api_contracts.py` | Полная action-матрица по статусам и ownership-комбинациям | P1 | Добавить параметризованные action-builder тесты: role + ownership + status |

## Жизненный цикл заявок

| Сценарий | Тест есть сейчас | Уровень | Файл(ы) тестов | Что не покрыто | Приоритет | Рекомендуемый следующий тест |
|---|---|---|---|---|---|---|
| Контракт списка/деталей заявок включает `actions` и скрывает top-level `permissions` | Да | integration | `backend/tests/integration/test_api_contracts.py` | Бизнес-флоу create/update/status transition | P0 | Добавить integration-тесты для `POST /requests` и `PATCH /requests/{id}` (happy/forbidden) |
| Open requests для contractor | Частично | integration, e2e smoke | `backend/tests/integration/test_api_contracts.py`; `web/e2e/requests.smoke.spec.ts` | Переходы offered/open tabs и ownership-фильтры на уровне API | P1 | Добавить integration-тесты видимости `/requests/open` vs `/requests/offered` для contractor |
| Deleted alerts viewed / побочные действия на уровне request | Частично | unit | `backend/tests/unit/test_action_builders_unit.py` | Endpoint-поведение `/requests/deleted-alerts/viewed` | P1 | Добавить integration-тест endpoint'а mark viewed |
| `requests.description` update | Нет | N/A | N/A | В текущем `RequestEditPayload` и `RequestEditInput` нет поля `description`, поэтому API/service-контракт не поддерживает update описания | P2 | Сначала принять product/API-решение: добавлять ли редактирование description; только после этого писать тест |
| Прямой backend-enforcement `requests.contractor_view.read` для contractor-view | Частично | integration (fake service) | `backend/tests/integration/test_request_lifecycle_integration.py` | Реальный `OfferService.get_request_view` сейчас проверяет видимость заявки + `offers.create`, а не `requests.contractor_view.read` | P0 | Добавить/изменить service-level enforcement на `requests.contractor_view.read`, затем заменить fake-service тест на проверку реального service path |

## Жизненный цикл офферов

| Сценарий | Тест есть сейчас | Уровень | Файл(ы) тестов | Что не покрыто | Приоритет | Рекомендуемый следующий тест |
|---|---|---|---|---|---|---|
| Контракт workspace оффера (`request.actions`, `offer.actions`, `chat_actions`) | Да | integration | `backend/tests/integration/test_api_contracts.py` | Переходы create/edit/status для офферов по ролям | P0 | Добавить integration-тесты create/edit/status endpoint'ов офферов |
| Ограничения ownership для доступа contractor к офферу | Да | unit | `backend/tests/unit/test_policies_unit.py` | Endpoint-enforcement для non-owner contractor при мутациях оффера | P0 | Добавить integration forbidden-тесты редактирования чужого оффера contractor'ом |
| Ветка manual offer | Частично | unit | `backend/tests/unit/test_policies_unit.py` | API-поведение manual offer create/file operations | P1 | Добавить integration-тесты `/requests/{id}/offers/manual` и ограничений на manual files |
| Accept offer для closed/cancelled request | Нет | xfail integration | `backend/tests/integration/test_offer_lifecycle_integration.py` | Бизнес-правило не реализовано: `OfferService.update_status` не проверяет статус заявки перед accept | P0 | Реализовать guard в `OfferService.update_status` и снять `xfail` с теста |
| Auto-reject остальных submitted offers при accept одного | Частично | DB trigger, integration фиксирует service-level fake | `order_database/init/02-triggers.sql`; `backend/tests/integration/test_offer_lifecycle_integration.py` | В `order_database` правило реализовано триггером `offers_accept_reject_others`, но текущий backend integration fake не моделирует DB trigger и показывает только service-level update целевого offer | P0 | Добавить DB-backed contract test или обновить fake repository так, чтобы тестовый контур явно моделировал trigger behavior |

## Email notifications

| Сценарий | Тест есть сейчас | Уровень | Файл(ы) тестов | Что не покрыто | Приоритет | Рекомендуемый следующий тест |
|---|---|---|---|---|---|---|
| Payload builders для request/invite/verification/status писем | Да | unit | `backend/tests/unit/test_email_payload_builders_unit.py` | End-to-end rendering в реальном mailbox | P1 | Добавить mailbox smoke на MailHog/Mailpit (если появится в dev/test) |
| Постановка email-событий для request/invite flow (fake outbox) | Да | integration | `backend/tests/integration/test_email_notifications_integration.py` | Endpoint-level contract `POST /requests/{id}/email-notifications` через API-роут с явным fake outbox assert | P1 | Добавить API integration-тест endpoint'а manual email notification |
| Dedup дополнительных email и безопасная обработка пустых/hidden получателей | Да | integration | `backend/tests/integration/test_email_notifications_integration.py` | Защитный сценарий при гонках нескольких одновременных отправок | P2 | Добавить concurrency stress-тест dedup |
| notifications_worker: valid/invalid payload, mandatory fields, SMTP error handling | Да | unit | `backend/tests/unit/test_notifications_worker_unit.py` | Dead-letter queue контракт (в текущей реализации не внедрен) | P2 | Добавить тесты DLQ после внедрения retry/DLQ механизма |
| Доступ к запросу email verification | Да | integration | `backend/tests/integration/test_auth_enforcement_contract.py` | Жизненный цикл verify-email token (`/auth/verify-email`) | P1 | Добавить integration-тесты success/expired-path для verify-email |

## Файлы

| Сценарий | Тест есть сейчас | Уровень | Файл(ы) тестов | Что не покрыто | Приоритет | Рекомендуемый следующий тест |
|---|---|---|---|---|---|---|
| Авторизация скачивания файлов (allow/deny) | Да | integration | `backend/tests/integration/test_auth_enforcement_contract.py`; `backend/tests/integration/test_api_contracts.py` | Upload/delete endpoint'ы для requests/offers | P0 | Добавить integration-тесты upload/delete файлов requests/offers с permission matrix |
| Ограничения видимости связанных файлов для contractor | Частично | integration | `backend/tests/integration/test_auth_enforcement_contract.py` | Позитивный путь contractor access при валидной linkage | P1 | Добавить integration-тест contractor allowed download при связанной сущности |

## Chat/workspace

| Сценарий | Тест есть сейчас | Уровень | Файл(ы) тестов | Что не покрыто | Приоритет | Рекомендуемый следующий тест |
|---|---|---|---|---|---|---|
| Chat action flags в payload workspace | Да | unit, integration | `backend/tests/unit/test_action_builders_unit.py`; `backend/tests/integration/test_api_contracts.py` | Поведение endpoint'ов send/attach/read-receipt | P0 | Добавить integration-тесты endpoint'ов `/offers/{id}/messages*` и проверок permissions |
| Навигация по workspace route в UI | Частично | e2e smoke | `web/e2e/requests.smoke.spec.ts` | Глубокие workspace-сценарии (chat + files + status updates) | P1 | Добавить extended e2e-сценарий совместной работы contractor/economist |

## Dashboards

| Сценарий | Тест есть сейчас | Уровень | Файл(ы) тестов | Что не покрыто | Приоритет | Рекомендуемый следующий тест |
|---|---|---|---|---|---|---|
| Frontend route gating для `/pm-dashboard*` | Частично | e2e smoke | `web/e2e/roles.smoke.spec.ts` | Контракт/enforcement backend dashboard endpoint'ов | P1 | Добавить integration-тесты read-permissions для `/dashboard/responsibility` и `/plans*` |
| Dashboard tabs по split-permissions | Частично | frontend unit (косвенно) | `web/src/app/routes/RoleRoute.test.tsx` | Видимость компонентов и API failure states | P2 | Добавить frontend unit-тесты dashboard widgets для permission subsets |

## Admin/users

| Сценарий | Тест есть сейчас | Уровень | Файл(ы) тестов | Что не покрыто | Приоритет | Рекомендуемый следующий тест |
|---|---|---|---|---|---|---|
| Гейт `/admin` по разрешениям маршрута | Да | frontend unit, e2e smoke | `web/src/app/routes/RoleRoute.test.tsx`; `web/e2e/roles.smoke.spec.ts`; `web/e2e/requests.smoke.spec.ts` | Backend endpoint'ы `/users*` (CRUD/status/role/manager enforcement) | P0 | Добавить integration-тесты ключевых `/users` мутаций с role/status ограничениями |
| User action flags для управления подчиненными | Да | unit | `backend/tests/unit/test_action_builders_unit.py`; `backend/tests/unit/test_policies_unit.py` | End-to-end флоу обновления подчиненных и conflict handling | P1 | Добавить integration-тесты endpoint'ов subordinate profile и unavailability |

## Feedback

| Сценарий | Тест есть сейчас | Уровень | Файл(ы) тестов | Что не покрыто | Приоритет | Рекомендуемый следующий тест |
|---|---|---|---|---|---|---|
| Доступ к feedback route по ролям | Частично | e2e smoke | `web/e2e/roles.smoke.spec.ts` | Backend-поведение `GET/POST /feedback` и валидация | P1 | Добавить integration-тесты create/read permissions и валидации payload |

## Normative files

| Сценарий | Тест есть сейчас | Уровень | Файл(ы) тестов | Что не покрыто | Приоритет | Рекомендуемый следующий тест |
|---|---|---|---|---|---|---|
| Permissions для normative files route/API | Нет | N/A | N/A | Нет прямого покрытия флоу `normative_files.read/create/manage` | P1 | Добавить integration-тесты upload/manage для normative files |

## Frontend route/page access

| Сценарий | Тест есть сейчас | Уровень | Файл(ы) тестов | Что не покрыто | Приоритет | Рекомендуемый следующий тест |
|---|---|---|---|---|---|---|
| Защита anonymous vs authenticated (`ProtectedRoute`) | Да | frontend unit | `web/src/app/routes/ProtectedRoute.test.tsx` | Сохранение deep link при redirect и callback race conditions | P1 | Добавить frontend unit-тест redirect на исходный target после auth bootstrap |
| Permission-gated pages (`RoleRoute`) | Да | frontend unit | `web/src/app/routes/RoleRoute.test.tsx` | Покрытие специфичных правил `/feedback`, `/pm-dashboard/savings`, `/pm-dashboard/plan` | P1 | Добавить table-driven `RoleRoute` tests для всех guarded paths в `AppRoutes` |
| Bootstrap сессии и UX flags в Auth provider | Да | frontend unit | `web/src/app/providers/AuthProvider.test.tsx` | Retry/backoff refresh-сессии и token-expired transitions | P1 | Добавить AuthProvider тесты для retry refresh и forced anonymous fallback |
| Page-level регрессии requests/offers | Частично | e2e smoke | `web/e2e/requests.smoke.spec.ts` | Детальные component assertions для create/edit/detail pages | P2 | Добавить frontend unit или e2e assertions для критичных widgets и CTA visibility |

## E2E smoke / extended scenarios

| Сценарий | Тест есть сейчас | Уровень | Файл(ы) тестов | Что не покрыто | Приоритет | Рекомендуемый следующий тест |
|---|---|---|---|---|---|---|
| Login smoke через Keycloak UI | Да | e2e smoke | `web/e2e/auth.smoke.spec.ts` | Browser-сценарий onboarding registration и verify-email | P1 | Добавить e2e-сценарий invite registration + account state resolution |
| Smoke ролевого доступа по 7 ролям | Да | e2e smoke | `web/e2e/roles.smoke.spec.ts` | Проверки actions внутри страниц | P1 | Добавить e2e assertions для критичных кнопок/действий по ролям |
| Smoke requests для economist/contractor/superadmin | Да | e2e smoke | `web/e2e/requests.smoke.spec.ts` | Многошаговый бизнес-флоу (request -> offer -> chat -> status) | P0 | Добавить extended e2e workflow с actor transitions |
| Автоматизация E2E provisioning/cleanup | Да | smoke script + manual workflow | `scripts/e2e-smoke.sh`; `scripts/e2e-smoke.ps1`; `.github/workflows/e2e-smoke.yml` | Отдельный ночной CI schedule для тренда стабильности smoke | P2 | Добавить опциональный scheduled workflow (non-blocking) для видимости тренда |

## Сводка по CI и smoke execution

Текущий автоматический CI gate (`.github/workflows/ci.yml`):
- backend unit
- backend integration/API contract
- frontend lint
- frontend unit
- frontend build

Ручные gate'ы:
- `.github/workflows/e2e-smoke.yml`
- `.github/workflows/release-smoke.yml`

## Приоритетные gap'ы для следующей волны

P0 (первая волна):
1. Integration-покрытие мутаций жизненного цикла requests (`create/update/status`).
2. Integration-покрытие мутаций жизненного цикла offers (`create/manual/edit/status`).
3. Integration-покрытие chat message endpoint'ов.
4. Backend-enforcement matrix tests для admin/users.
6. Устранить gap `requests.contractor_view.read`: текущий реальный contractor-view path завязан на `offers.create`.
7. Реализовать/зафиксировать продуктово правило accept offer для closed/cancelled request.

P1 (вторая волна):
1. Backend-контракты dashboard'ов и UI permission-subsets.
2. Backend-тесты feedback.
3. Тесты normative files.
4. Дополнительные auth happy-path/onboarding тесты.
5. Покрыть auto-reject sibling offers тестом, который учитывает реальный DB trigger `offers_accept_reject_others`.
6. Добавить dev/test mailbox smoke через MailHog/Mailpit (P1, без обязательного внедрения тяжелой infra).

P2 (третья волна):
1. Extended e2e-сценарии (полный workflow между ролями).
2. Route/detail UX-regression и resilience checks.
3. Опциональный scheduled smoke-trend workflow.

## Update 2026-05-12: frontend nav + extended e2e

Added frontend unit/component tests:
- `web/src/features/header/model/buildHeaderConfig.test.ts`:
  role-aware menu/tabs visibility for `superadmin`, `economist`, `operator`, `contractor`;
  dashboard tab visibility depends on `dashboard.*` permissions;
  admin section visibility depends on `users.read`.
- `web/src/app/routes/RoleRoute.test.tsx`:
  explicit negative case for raw claims (`app_roles`/`delegation_roles`) without required permission.
- `web/src/features/requests/ui/RequestsTable.test.tsx`:
  `loading` and `empty` states.
- `web/src/features/requests/ui/RequestsPageView.test.tsx`:
  `error` state rendering.

Added extended e2e specs:
- `web/e2e/roles.access.spec.ts` (`@roles`)
- `web/e2e/registration.extended.spec.ts` (`@registration`)
- `web/e2e/request-offer.extended.spec.ts` (`@request-offer`)
- `web/e2e/dashboard.extended.spec.ts` (`@dashboard`)
- `web/e2e/files-chat.extended.spec.ts` (`@files-chat`)

Smoke policy remains unchanged:
- `@smoke` only for lightweight browser checks;
- extended tags are manual and intentionally excluded from default smoke/CI execution.
