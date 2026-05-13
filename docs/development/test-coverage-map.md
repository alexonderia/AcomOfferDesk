# Карта покрытия тестами

_Последнее обновление: 2026-05-13 (ветка `dev_process`)._

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
| OIDC callback: невалидный `state` / отсутствует `code` / отсутствует cookie / positive callback | Да | integration | `backend/tests/integration/test_auth_oidc_flows.py` | Browser-level callback/onboarding UX через реальный Keycloak UI | Closed (P0) | Поддерживать regression coverage для state/code/cookie ошибок и успешного callback (`sync/link`, refresh cookie, redirect) |
| Контракт refresh возвращает `permissions/app_roles/delegation_roles` и корректно обрабатывает rotation/stale cookie | Да | integration, frontend unit | `backend/tests/integration/test_auth_session_contract.py`; `web/src/app/providers/AuthProvider.test.tsx` | Browser-level retry/backoff и token-expiry UX | Closed (P0) | Поддерживать regression coverage rotation/repeated refresh/stale cookie (`401` + cookie clear) |
| Logout очищает сессию при сбоях провайдера и остаётся идемпотентным | Да | integration, e2e smoke | `backend/tests/integration/test_auth_oidc_flows.py`; `web/e2e/auth.smoke.spec.ts` | Browser-level post-logout UX/redirect matrix | Closed (P1) | Поддерживать regression coverage: logout без cookie, повторный logout, битый bearer, provider/admin API failures |
| Обработка invite registration: mismatch / already registered / successful onboarding link | Да | integration | `backend/tests/integration/test_auth_oidc_flows.py` | Полный browser/e2e onboarding путь регистрации по invite через Keycloak UI | Частично (P0) | Сохранить API/service integration coverage; browser-path оставить manual/extended e2e до стабилизации стендового сценария |
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
| Прямой backend-enforcement `requests.contractor_view.read` для contractor-view | Да | integration | `backend/tests/integration/test_request_lifecycle_integration.py` | Дополнительный DB-backed контракт для связки с production данными не требуется: service-level guard покрыт | Closed (P0) | Поддерживать regression coverage при изменении contractor-view |

## Жизненный цикл офферов

| Сценарий | Тест есть сейчас | Уровень | Файл(ы) тестов | Что не покрыто | Приоритет | Рекомендуемый следующий тест |
|---|---|---|---|---|---|---|
| Контракт workspace оффера (`request.actions`, `offer.actions`, `chat_actions`) | Да | integration | `backend/tests/integration/test_api_contracts.py` | Переходы create/edit/status для офферов по ролям | P0 | Добавить integration-тесты create/edit/status endpoint'ов офферов |
| Ограничения ownership для доступа contractor к офферу | Да | unit | `backend/tests/unit/test_policies_unit.py` | Endpoint-enforcement для non-owner contractor при мутациях оффера | P0 | Добавить integration forbidden-тесты редактирования чужого оффера contractor'ом |
| Ветка manual offer | Частично | unit | `backend/tests/unit/test_policies_unit.py` | API-поведение manual offer create/file operations | P1 | Добавить integration-тесты `/requests/{id}/offers/manual` и ограничений на manual files |
| Accept offer для closed/cancelled request | Да | integration | `backend/tests/integration/test_offer_lifecycle_integration.py` | Проверка закрывает service-level guard; DB-поведение не требуется для этого правила | Closed (P0) | Поддерживать regression coverage при изменении `OfferService.update_status` |
| Auto-reject остальных submitted offers при accept одного | Частично | integration strict xfail + DB trigger reference | `order_database/init/02-triggers.sql`; `backend/tests/integration/test_offer_lifecycle_integration.py` | Production-правило реализовано триггером `offers_accept_reject_others` в `order_database`; in-memory integration контур не моделирует trigger и не должен давать ложный green. Service-level allow/deny coverage остается отдельным non-xfail тестом (`test_accept_offer_requires_status_update_permission`). | P1 | Оставить `strict xfail` как explicit gap; при появлении DB-backed контура добавить contract test и вынести его в отдельный marker (`db_contract`) вне обычного CI |

## Email notifications

| Сценарий | Тест есть сейчас | Уровень | Файл(ы) тестов | Что не покрыто | Приоритет | Рекомендуемый следующий тест |
|---|---|---|---|---|---|---|
| Payload builders для request/invite/verification/status писем | Да | unit | `backend/tests/unit/test_email_payload_builders_unit.py` | End-to-end rendering в реальном mailbox | P1 | Добавить mailbox smoke на MailHog/Mailpit (если появится в dev/test) |
| Постановка email-событий для request/invite flow (fake outbox) | Да | integration | `backend/tests/integration/test_email_notifications_integration.py`; `backend/tests/integration/test_p1_backend_contract_gaps_integration.py` | Browser/e2e mailbox delivery outside integration contour | Closed (P1) | Поддерживать regression coverage manual endpoint (`POST /requests/{id}/email-notifications`) с fake outbox/transport и dedup |
| Dedup дополнительных email и безопасная обработка пустых/hidden получателей | Да | integration | `backend/tests/integration/test_email_notifications_integration.py` | Защитный сценарий при гонках нескольких одновременных отправок | P2 | Добавить concurrency stress-тест dedup |
| notifications_worker: valid/invalid payload, mandatory fields, SMTP error handling | Да | unit | `backend/tests/unit/test_notifications_worker_unit.py` | Dead-letter queue контракт (в текущей реализации не внедрен) | P2 | Добавить тесты DLQ после внедрения retry/DLQ механизма |
| Доступ к запросу email verification и жизненный цикл `/auth/verify-email` | Да | integration | `backend/tests/integration/test_auth_enforcement_contract.py` | Browser/e2e onboarding verify-email flow | Closed (P1) | Поддерживать regression coverage для valid/repeat/invalid/expired/wrong-flow/conflict token paths и request-email-verification fake transport |

## Файлы

| Сценарий | Тест есть сейчас | Уровень | Файл(ы) тестов | Что не покрыто | Приоритет | Рекомендуемый следующий тест |
|---|---|---|---|---|---|---|
| Авторизация скачивания файлов (allow/deny) | Да | integration | `backend/tests/integration/test_auth_enforcement_contract.py`; `backend/tests/integration/test_api_contracts.py`; `backend/tests/integration/test_p1_backend_contract_gaps_integration.py` | Stress/concurrency для file access matrix | Closed (P1) | Поддерживать regression coverage `401/403/404` и contractor linkage paths |
| Upload/delete request/offer files permission matrix | Да | integration | `backend/tests/integration/test_p1_backend_contract_gaps_integration.py` | Дополнительный DB-backed контур не требуется для текущего API enforcement | Closed (P1) | Поддерживать regression coverage owner/non-owner/anonymous/unsupported/empty/oversize/missing-attachment |
| Ограничения видимости связанных файлов для contractor | Да | integration | `backend/tests/integration/test_auth_enforcement_contract.py`; `backend/tests/integration/test_p1_backend_contract_gaps_integration.py` | Cross-entity linkage matrix для chat/message attachments в отдельном расширенном наборе | Closed (P1) | При изменении linkage логики обновлять contractor allow/deny integration cases |

## Chat/workspace

| Сценарий | Тест есть сейчас | Уровень | Файл(ы) тестов | Что не покрыто | Приоритет | Рекомендуемый следующий тест |
|---|---|---|---|---|---|---|
| Chat action flags в payload workspace | Да | unit, integration | `backend/tests/unit/test_action_builders_unit.py`; `backend/tests/integration/test_api_contracts.py`; `backend/tests/integration/test_chat_endpoints_integration.py` | Глубокий DB-backed path для realtime/event transport остается вне текущего in-memory integration контура | P1 | Для полной end-to-end валидации добавить стендовый workflow test c реальными realtime зависимостями |
| Навигация по workspace route в UI | Частично | e2e smoke | `web/e2e/requests.smoke.spec.ts` | Глубокие workspace-сценарии (chat + files + status updates) | P1 | Добавить extended e2e-сценарий совместной работы contractor/economist |

## Dashboards

| Сценарий | Тест есть сейчас | Уровень | Файл(ы) тестов | Что не покрыто | Приоритет | Рекомендуемый следующий тест |
|---|---|---|---|---|---|---|
| Backend enforcement для `/dashboard/responsibility` и `/plans*` | Да | integration | `backend/tests/integration/test_p1_backend_contract_gaps_integration.py` | Отдельный savings-only endpoint отсутствует в текущем API surface | Closed (P1) | Поддерживать regression coverage по permissions/status/anonymous + period/date/hierarchy filters |
| Dashboard tabs по split-permissions | Да | frontend unit | `web/src/features/header/model/buildHeaderConfig.test.ts`; `web/src/app/routes/RoleRoute.test.tsx` | Browser-level cross-page smoke matrix по всем ролям | Closed (P2) | Поддерживать regression coverage для `dashboard.process.read` / `dashboard.savings.read` / `dashboard.plans.read` |
| Dashboard widgets: loading / empty / error / safe numeric rendering | Да | frontend unit | `web/src/features/dashboard/components/ProjectManagerDashboard.test.tsx`; `web/src/features/dashboard/components/ProjectManagerSavingsDashboard.test.tsx`; `web/src/features/dashboard/components/ProjectManagerPlanDashboard.test.tsx` | Отдельный API-контракт savings endpoint не тестируется, т.к. endpoint отсутствует | Closed (P2) | Поддерживать текущие state-tests без добавления несуществующих API routes |
| Отдельный dashboard savings endpoint (`/dashboard/savings`) | Нет | N/A | N/A | В текущем backend API нет отдельного savings route: savings входит в `GET /dashboard/responsibility`; отдельный endpoint не добавлялся без бизнес-требования | Gap (documented) | Если продукт потребует отдельный savings endpoint, сначала зафиксировать API/PRD и только затем добавлять тесты |

## Admin/users

| Сценарий | Тест есть сейчас | Уровень | Файл(ы) тестов | Что не покрыто | Приоритет | Рекомендуемый следующий тест |
|---|---|---|---|---|---|---|
| Гейт `/admin` по разрешениям маршрута | Да | frontend unit, e2e smoke, backend integration | `web/src/app/routes/RoleRoute.test.tsx`; `web/e2e/roles.smoke.spec.ts`; `web/e2e/requests.smoke.spec.ts`; `backend/tests/integration/test_admin_users_enforcement_integration.py` | Полный CRUD/edge-case matrix по всем ролям и по всем `/users` read endpoints еще можно расширять | P1 | Расширить таблицу сценариев `/users` для всех комбинаций hierarchy + role transitions |
| User action flags для управления подчиненными | Да | unit | `backend/tests/unit/test_action_builders_unit.py`; `backend/tests/unit/test_policies_unit.py` | End-to-end флоу обновления подчиненных и conflict handling | P1 | Добавить integration-тесты endpoint'ов subordinate profile и unavailability |

## Feedback

| Сценарий | Тест есть сейчас | Уровень | Файл(ы) тестов | Что не покрыто | Приоритет | Рекомендуемый следующий тест |
|---|---|---|---|---|---|---|
| Доступ к feedback route по ролям и валидация payload | Да | integration | `backend/tests/integration/test_p1_backend_contract_gaps_integration.py` | Расширенный e2e UX coverage feedback page | Closed (P1) | Поддерживать regression coverage create/list + anonymous/forbidden + empty/too-long payload |

## Normative files

| Сценарий | Тест есть сейчас | Уровень | Файл(ы) тестов | Что не покрыто | Приоритет | Рекомендуемый следующий тест |
|---|---|---|---|---|---|---|
| Upload normative file (`normative_files.create`) | Да | integration | `backend/tests/integration/test_p1_backend_contract_gaps_integration.py` | Read/manage endpoints отсутствуют в текущем API surface | Частично | Поддерживать regression coverage create/duplicate/forbidden/anonymous paths |
| Read/manage normative files (`normative_files.read/manage`) | Нет | N/A | N/A | В `backend/app/api/v1/normative_files.py` отсутствуют list/read/update/delete endpoint'ы; покрывать нечего без нового бизнес-требования | Gap (documented) | При появлении endpoint'ов добавить integration coverage для read/create/manage matrix |

## Frontend route/page access

| Сценарий | Тест есть сейчас | Уровень | Файл(ы) тестов | Что не покрыто | Приоритет | Рекомендуемый следующий тест |
|---|---|---|---|---|---|---|
| Защита anonymous vs authenticated (`ProtectedRoute`) | Да | frontend unit | `web/src/app/routes/ProtectedRoute.test.tsx` | Deep-link preservation в guard redirect (`/login?next=...`) пока не реализован и остается documented UX gap | Gap (documented) | Когда будет принято продуктовое решение по `next`-redirect, добавить unit + e2e проверку возврата на исходный route |
| Permission-gated pages (`RoleRoute`) | Да | frontend unit | `web/src/app/routes/RoleRoute.test.tsx`; `web/src/pages/offers/OfferWorkspacePage.test.tsx`; `web/src/pages/requests/ContractorRequestDetailsPage.test.tsx` | Browser-level regression матрица по всем route transitions | Closed (P1) | Поддерживать table-driven coverage для `/admin`, `/feedback`, `/pm-dashboard*`, `/requests`, contractor-view и workspace routes |
| Bootstrap сессии и UX flags в Auth provider | Да | frontend unit | `web/src/app/providers/AuthProvider.test.tsx` | Retry/backoff по сетевым ошибкам (кроме stale/401) | P1 | Добавить отдельный сценарий client-side backoff/retry при изменении политики refresh |
| Page-level регрессии requests/offers | Да | frontend unit, e2e smoke | `web/src/features/request-details/ui/RequestDetailsView.test.tsx`; `web/src/features/offer-workspace/ui/OfferWorkspaceView.test.tsx`; `web/src/pages/requests/ContractorRequestDetailsPage.test.tsx`; `web/e2e/requests.smoke.spec.ts` | Полный multi-actor workflow (request -> offer -> chat -> accept/reject) остается extended e2e/manual | P2 | Поддерживать unit coverage action-driven CTA и запускать extended e2e на stage перед релизом |

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
- frontend unit/component tests
- frontend build

Ручные gate'ы:
- `.github/workflows/e2e-smoke.yml`
- `.github/workflows/release-smoke.yml`

## Приоритетные gap'ы для следующей волны

P0 (первая волна):
1. Integration-покрытие мутаций жизненного цикла requests (`create/update/status`) — закрыто.
2. Integration-покрытие мутаций жизненного цикла offers (`create/manual/edit/status`) — закрыто по service-level guard'ам.
3. Integration-покрытие chat message endpoint'ов — закрыто на in-memory integration контуре.
4. Backend-enforcement matrix tests для admin/users — закрыто для ключевых мутаций (`register/status/role/manager`) и scope-listing.
6. Gap `requests.contractor_view.read` — закрыт (service-level enforcement + regression test).
7. Правило accept offer для closed/cancelled request — закрыто (guard реализован, `xfail` снят).

P1 (вторая волна):
1. Backend dashboard contracts — закрыто для существующих `/dashboard/responsibility` и `/plans*`; отдельный `/dashboard/savings` endpoint остается documented gap (endpoint отсутствует).
2. Backend feedback contracts — закрыто.
3. Backend files upload/delete/download contracts — закрыто.
4. Backend normative files — частично: create/upload закрыто, read/manage остаются documented gap (endpoint'ы отсутствуют).
5. Дополнительные auth happy-path/onboarding tests (browser/e2e уровень) — integration gap закрыт, остаётся manual/extended e2e часть.
6. Покрыть auto-reject sibling offers DB-backed контрактом, который учитывает реальный trigger `offers_accept_reject_others` (в текущем наборе оставлен explicit `strict xfail`).
7. Добавить dev/test mailbox smoke через MailHog/Mailpit (P1, без обязательного внедрения тяжелой infra).

P2 (третья волна):
1. Extended e2e-сценарии (полный workflow между ролями).
2. Route/detail UX-regression и resilience checks.
3. Опциональный scheduled smoke-trend workflow.

## Обновление 2026-05-13: закрытие frontend coverage gaps

Добавлены frontend unit/component tests:
- `web/src/app/providers/AuthProvider.test.tsx`:
  refresh failure -> anonymous, stale token cleanup, repeated refresh consistency, logout cleanup, explicit deep-link target в `beginLogin`.
- `web/src/app/routes/ProtectedRoute.test.tsx`:
  table-driven anonymous/account redirects для `/requests`, `/requests/:id/contractor`, `/offers/:id/workspace`.
- `web/src/app/routes/RoleRoute.test.tsx`:
  table-driven guard matrix для `/admin`, `/feedback`, `/pm-dashboard`, `/pm-dashboard/savings`, `/pm-dashboard/plan`;
  negative cases для raw `app_roles`/`delegation_roles` без atomic permissions.
- `web/src/pages/requests/ContractorRequestDetailsPage.test.tsx` и `web/src/pages/offers/OfferWorkspacePage.test.tsx`:
  route-level permissions и запрет доступа без нужного backend permission.
- `web/src/features/request-details/ui/RequestDetailsView.test.tsx` и `web/src/features/offer-workspace/ui/OfferWorkspaceView.test.tsx`:
  action-driven CTA visibility (`create/edit/change-owner/upload/delete/send-email`, offer edit/accept/reject/chat/file actions).
- `web/src/features/dashboard/components/ProjectManagerDashboard.test.tsx`;
  `web/src/features/dashboard/components/ProjectManagerSavingsDashboard.test.tsx`;
  `web/src/features/dashboard/components/ProjectManagerPlanDashboard.test.tsx`:
  widget states `loading/empty/error` и safe rendering без `NaN/Infinity/undefined`.

Documented UX gap:
- deep-link preservation в route guard redirect (`/login?next=...`) пока не реализован в `ProtectedRoute`; текущий coverage фиксирует это как explicit gap без добавления новой frontend business logic.

## Обновление 2026-05-12: frontend navigation и extended e2e

Добавлены frontend unit/component tests:
- `web/src/features/header/model/buildHeaderConfig.test.ts`:
  проверяет ролевую видимость меню/табов для `superadmin`, `economist`, `operator`, `contractor`;
  проверяет, что dashboard tabs зависят от `dashboard.*` permissions;
  проверяет, что admin section зависит от `users.read`.
- `web/src/app/routes/RoleRoute.test.tsx`:
  добавлен явный негативный кейс для raw claims (`app_roles`/`delegation_roles`) без нужного permission.
- `web/src/features/requests/ui/RequestsTable.test.tsx`:
  покрыты состояния `loading` и `empty`.
- `web/src/features/requests/ui/RequestsPageView.test.tsx`:
  покрыт рендеринг `error` state.

Добавлены backend unit tests:
- `backend/tests/unit/test_dashboard_calculations_unit.py`:
  проверяет dashboard calculations, пустые входные данные и защиту от некорректных числовых состояний.
- `backend/tests/unit/test_role_access_matrix_unit.py`:
  сверяет role/access matrix и гарантирует, что `app.*`/`delegation.*` не дают доступ без atomic permissions.
- `backend/tests/unit/test_email_payload_builders_unit.py` и `backend/tests/unit/test_notifications_worker_unit.py`:
  покрывают email payload, обязательные поля, dedup/cooldown и SMTP error handling без реальной отправки.

Добавлены/актуализированы backend integration tests:
- `backend/tests/integration/test_email_notifications_integration.py`:
  проверяет постановку email events в fake outbox/transport для request/invite flow, валидацию email и dedup получателей.
- `backend/tests/integration/test_auth_oidc_flows.py`:
  покрывает OIDC callback edge/positive cases, registration invite mismatch/already-registered/successful callback path,
  refresh negative path и idempotent logout при недоступном Keycloak API.
- `backend/tests/integration/test_auth_session_contract.py`:
  покрывает refresh session contract, rotation/repeated refresh consistency и stale-cookie cleanup (`401` + clear cookie).
- `backend/tests/integration/test_auth_enforcement_contract.py`:
  фиксирует backend enforcement для `401/403`, статусов `review/inactive/blacklist`, защищенных действий,
  request-email-verification fake transport/dedup и жизненный цикл `/auth/verify-email`.

Добавлены extended e2e specs:
- `web/e2e/roles.access.spec.ts` (`@roles`)
- `web/e2e/registration.extended.spec.ts` (`@registration`)
- `web/e2e/request-offer.extended.spec.ts` (`@request-offer`)
- `web/e2e/dashboard.extended.spec.ts` (`@dashboard`)
- `web/e2e/files-chat.extended.spec.ts` (`@files-chat`)

Политика smoke остается прежней:
- `@smoke` только для легких browser checks;
- extended tags запускаются вручную и намеренно исключены из default smoke/CI execution;
- release-smoke workflow запускает `smoke-infra` и `check-keycloak`, а e2e включает только по `include_e2e=true`.
