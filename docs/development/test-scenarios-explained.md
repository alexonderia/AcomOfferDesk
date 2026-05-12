# Карта тестовых сценариев

Дата актуализации: 2026-05-12.

Документ объясняет, какие проверки есть в проекте, что именно они проверяют и каким способом. Backend unit/integration сценарии перечислены по фактическому `pytest --collect-only`, поэтому параметризованные проверки развернуты как отдельные сценарии.

## Как читать уровни

| Уровень | Что проверяет | Как запускается | Внешние сервисы |
|---|---|---|---|
| Backend unit | Доменные правила, permissions, policies, action builders, расчеты сервисов | `./scripts/test-unit.ps1` или `python -m pytest backend/tests/unit -q` | Не нужны |
| Backend integration/API contract | FastAPI endpoints, dependency overrides, статусы HTTP, payload contracts | `./scripts/test-integration.ps1` или `python -m pytest backend/tests/integration -q` | Не нужны; Keycloak/БД/сервисы подменяются fake/stub зависимостями |
| Frontend unit | React route guards и auth provider | `npm --prefix web run test:unit` | Не нужны; API вызовы мокируются |
| Frontend build/lint | TypeScript, Vite build, ESLint | `npm --prefix web run build`, `npm --prefix web run lint` | Не нужны |
| Infrastructure smoke | Живой gateway, backend health, Keycloak public issuer/JWKS, PostgreSQL, S3/MinIO, RabbitMQ | `./scripts/smoke-infra.ps1 -EnvFile .env.dev` | Нужен поднятый стенд |
| Keycloak permission smoke | Реальная модель Keycloak clients/roles/composites/admin service | `./scripts/check-keycloak.ps1 -EnvFile .env.dev` | Нужен Keycloak Admin API |
| E2E smoke | Браузерные сценарии Playwright через реальный web/backend/Keycloak | `./scripts/e2e-smoke.ps1 -EnvFile .env.dev -ProvisionUsers` | Нужен поднятый стенд |
| Release smoke | Последовательный релизный прогон: unit, integration, infra smoke, Keycloak check, frontend build, optional e2e | `./scripts/test-release.ps1 ...` | Нужен стенд для smoke/e2e |

## Backend unit: 99 сценариев

| # | Тест | Что проверяет | Способ проверки |
|---:|---|---|---|
| 1 | `test_request_action_builder_reflects_permissions_and_status` | Builder actions для заявки выставляет права просмотра деталей, сумм, contractor-view, файлов, email-уведомлений и deleted-alert. | Создает fake `CurrentUser` с набором request permissions и вызывает `RequestActionBuilder.build`. |
| 2 | `test_offer_action_builder_contractor_does_not_get_internal_accept_reject` | Contractor получает workspace/amount/files действия, но не получает internal accept/reject. | Создает contractor user и вызывает `OfferActionBuilder.build` для собственного offer. |
| 3 | `test_chat_action_builder_reflects_chat_permissions` | Chat actions соответствуют permissions на чтение, отправку, вложения и receipts. | Создает пользователя с chat permissions и вызывает `ChatActionBuilder.build`. |
| 4 | `test_user_action_builder_contractor_not_given_internal_controls` | Contractor не получает внутренние controls управления пользователем. | Вызывает `UserActionBuilder.build_list_item` для contractor и проверяет false-флаги. |
| 5 | `test_user_action_builder_internal_manager_can_manage_subordinate` | Internal manager с нужными permissions может управлять subordinate profile/unavailability. | Вызывает `UserActionBuilder.build_subordinate_profile`. |
| 6 | `test_build_current_user_from_keycloak_splits_known_permission_and_role_prefixes` | Keycloak roles разделяются на atomic permissions, `app_roles`, `delegation_roles`; мусор игнорируется. | Вызывает `build_current_user_from_keycloak` с mixed role set. |
| 7 | `test_build_current_user_from_keycloak_empty_api_roles_produces_empty_sets` | Пустой набор ролей Keycloak дает пустые множества. | Строит `CurrentUser` без api roles. |
| 8 | `test_build_current_user_from_keycloak_app_superadmin_without_atomic_permissions_has_no_permissions` | `app.superadmin` сам по себе не дает atomic permissions. | Передает только `app.superadmin` в api roles. |
| 9 | `test_build_current_user_from_keycloak_delegation_roles_do_not_become_permissions` | `delegation.*` роли не становятся permissions. | Передает delegation роли и проверяет отдельное поле. |
| 10 | `test_has_permission_active_user_with_permission_returns_true` | Active user с permission проходит `has_permission`. | Fake user с `users.read`. |
| 11 | `test_has_permission_active_user_without_permission_returns_false` | Active user без нужного permission не проходит. | Fake user с другим permission. |
| 12 | `test_has_permission_review_contractor_allows_only_onboarding_permissions` | Review contractor может только onboarding-safe permissions. | Проверяет own profile/contact permissions против request permission. |
| 13 | `test_has_permission_non_active_blocked_even_if_permission_present[inactive]` | `inactive` блокируется даже с permission. | Параметризованный статус `inactive`. |
| 14 | `test_has_permission_non_active_blocked_even_if_permission_present[blacklist]` | `blacklist` блокируется даже с permission. | Параметризованный статус `blacklist`. |
| 15 | `test_has_permission_review_non_contractor_blocked` | `review` для не-contractor не дает доступ. | Economist в `review` с profile permission. |
| 16 | `test_require_permission_active_with_permission_passes` | `require_permission` пропускает active user с permission. | Вызов без ожидаемой ошибки. |
| 17 | `test_require_permission_raises_for_blocked_status` | Review contractor не проходит protected permission. | Ожидает `Forbidden`. |
| 18 | `test_require_permission_rejects_non_active_statuses[inactive]` | `inactive` получает `Forbidden`. | Параметризованный статус. |
| 19 | `test_require_permission_rejects_non_active_statuses[blacklist]` | `blacklist` получает `Forbidden`. | Параметризованный статус. |
| 20 | `test_require_any_permission_respects_status_filters` | `require_any_permission` учитывает onboarding-safe фильтр. | Один вызов проходит, второй падает `Forbidden`. |
| 21 | `test_require_any_permission_rejects_non_active_statuses[inactive]` | `inactive` не проходит any-permission check. | Ожидает `Forbidden`. |
| 22 | `test_require_any_permission_rejects_non_active_statuses[blacklist]` | `blacklist` не проходит any-permission check. | Ожидает `Forbidden`. |
| 23 | `test_dashboard_savings_calculation_handles_core_edge_cases` | Расчет savings: positive, zero, negative, null amount cases. | Вызывает private расчетную функцию `DashboardService._calculate_savings`. |
| 24 | `test_responsibility_dashboard_contains_status_counters_and_assigned_requests` | Responsibility dashboard содержит counters, assigned requests и savings summary. | Fake repositories возвращают сотрудников, заявки и closed requests. |
| 25 | `test_plan_request_stats_aggregate_by_hierarchy_existing_logic` | Plan request stats агрегируют totals, distributed/unallocated и completion percent. | Fake requests repo и `PlanService._request_stats_from_trees`. |
| 26 | `test_get_known_permissions_contains_atomic_codes_only` | Known permissions содержат atomic codes и не содержат `app.*`/`delegation.*`. | Проверяет результат `get_known_permissions`. |
| 27 | `test_get_known_permissions_is_not_empty` | Known permissions не пустой набор. | Проверяет длину набора. |
| 28 | `test_request_policy_edit_owner_vs_not_owner_for_economist` | Economist редактирует свою заявку, но не чужую. | Вызывает `RequestPolicy.can_edit` с owner/non-owner. |
| 29 | `test_request_policy_requires_permissions` | `requests.read` недостаточно для редактирования. | User без edit permissions. |
| 30 | `test_offer_policy_contractor_can_manage_only_own_offer` | Contractor получает доступ только к своему offer. | Вызывает `OfferPolicy.can_access_contractor_offer`. |
| 31 | `test_offer_policy_manual_offer_files_rejected_for_non_manual_offer` | Manual offer files нельзя менять для non-manual offer. | Вызывает `OfferPolicy.can_manage_manual_offer_files`. |
| 32 | `test_user_policy_manage_requests_forbidden_without_permissions` | Project manager без request-management permissions не управляет заявками. | Вызывает `UserPolicy.can_manage_requests`. |
| 33 | `test_user_policy_manage_requests_forbidden_for_operator_even_with_permissions` | Operator не управляет заявками даже с request update permissions. | Ролевая проверка policy. |
| 34 | `test_user_policy_manage_requests_allowed_for_lead_with_permissions` | Lead economist с полным набором permissions может управлять заявками. | Positive branch `UserPolicy.can_manage_requests`. |
| 35 | `test_role_permissions_map_covers_all_known_permissions` | Каждая permission из source-of-truth backend map назначена хотя бы одной роли. | Flatten `get_role_permissions_map` и сравнение с `get_known_permissions`. |
| 36 | `test_role_permissions_map_has_no_unknown_permissions` | Role map не содержит неизвестных permissions. | Проверяет все permissions role map против known set. |
| 37 | `test_get_role_permissions_map_contains_expected_role_ids` | Role map содержит ровно ожидаемые business role ids. | Сравнивает keys map с settings role ids. |
| 38 | `test_superadmin_has_all_known_permissions` | Superadmin имеет все known permissions. | Сравнивает role map superadmin со всем known set. |
| 39 | `test_role_map_contains_only_atomic_permissions` | Role map не содержит `app.*` и `delegation.*`. | Prefix checks по flattened map. |
| 40 | `test_app_roles_do_not_grant_atomic_permissions_by_themselves` | `app.*` роли не дают atomic permissions без composites в token. | Строит user с `app.superadmin`, `app.admin`. |
| 41 | `test_delegation_roles_do_not_grant_atomic_permissions_by_themselves` | `delegation.*` роли не дают atomic permissions. | Строит user с delegation roles. |
| 42 | `review_contractor[chat.message.attach]` | Review contractor не получает `chat.message.attach`. | Параметризованный `has_permission` по всем known permissions. |
| 43 | `review_contractor[chat.message.send]` | Review contractor не получает `chat.message.send`. | То же. |
| 44 | `review_contractor[chat.read]` | Review contractor не получает `chat.read`. | То же. |
| 45 | `review_contractor[chat.receipts.mark_read]` | Review contractor не получает `chat.receipts.mark_read`. | То же. |
| 46 | `review_contractor[chat.receipts.mark_received]` | Review contractor не получает `chat.receipts.mark_received`. | То же. |
| 47 | `review_contractor[company_contacts.manage_any]` | Review contractor не получает управление чужими company contacts. | То же. |
| 48 | `review_contractor[company_contacts.manage_own]` | Review contractor получает onboarding-safe `company_contacts.manage_own`. | То же. |
| 49 | `review_contractor[contractors.manual.create]` | Review contractor не получает manual contractor create. | То же. |
| 50 | `review_contractor[contractors.manual.manage]` | Review contractor не получает manual contractor manage. | То же. |
| 51 | `review_contractor[dashboard.plans.read]` | Review contractor не читает plans dashboard. | То же. |
| 52 | `review_contractor[dashboard.process.read]` | Review contractor не читает process dashboard. | То же. |
| 53 | `review_contractor[dashboard.savings.read]` | Review contractor не читает savings dashboard. | То же. |
| 54 | `review_contractor[feedback.create]` | Review contractor не создает feedback. | То же. |
| 55 | `review_contractor[feedback.read]` | Review contractor не читает feedback. | То же. |
| 56 | `review_contractor[files.download]` | Review contractor не скачивает файлы. | То же. |
| 57 | `review_contractor[normative_files.create]` | Review contractor не создает normative files. | То же. |
| 58 | `review_contractor[normative_files.manage]` | Review contractor не управляет normative files. | То же. |
| 59 | `review_contractor[normative_files.read]` | Review contractor не читает normative files. | То же. |
| 60 | `review_contractor[offers.amount.update]` | Review contractor не меняет сумму offer. | То же. |
| 61 | `review_contractor[offers.contractor_info.read]` | Review contractor не читает contractor info. | То же. |
| 62 | `review_contractor[offers.create]` | Review contractor не создает offers. | То же. |
| 63 | `review_contractor[offers.details.update]` | Review contractor не меняет details offer. | То же. |
| 64 | `review_contractor[offers.files.delete]` | Review contractor не удаляет offer files. | То же. |
| 65 | `review_contractor[offers.files.upload]` | Review contractor не загружает offer files. | То же. |
| 66 | `review_contractor[offers.manual.create]` | Review contractor не создает manual offers. | То же. |
| 67 | `review_contractor[offers.status.update]` | Review contractor не меняет offer status. | То же. |
| 68 | `review_contractor[offers.update]` | Review contractor не редактирует offers. | То же. |
| 69 | `review_contractor[offers.workspace.read]` | Review contractor не читает offer workspace. | То же. |
| 70 | `review_contractor[profile.manage_any]` | Review contractor не управляет чужим профилем. | То же. |
| 71 | `review_contractor[profile.manage_own]` | Review contractor получает onboarding-safe `profile.manage_own`. | То же. |
| 72 | `review_contractor[requests.amounts.read]` | Review contractor не читает суммы заявок. | То же. |
| 73 | `review_contractor[requests.contractor_view.read]` | Review contractor не читает contractor request view. | То же. |
| 74 | `review_contractor[requests.create]` | Review contractor не создает заявки. | То же. |
| 75 | `review_contractor[requests.deadline.update]` | Review contractor не меняет deadline. | То же. |
| 76 | `review_contractor[requests.deleted_alerts.mark_viewed]` | Review contractor не отмечает deleted alerts. | То же. |
| 77 | `review_contractor[requests.email_notifications.send]` | Review contractor не отправляет email notifications. | То же. |
| 78 | `review_contractor[requests.files.delete]` | Review contractor не удаляет request files. | То же. |
| 79 | `review_contractor[requests.files.upload]` | Review contractor не загружает request files. | То же. |
| 80 | `review_contractor[requests.offered.read]` | Review contractor не читает offered requests. | То же. |
| 81 | `review_contractor[requests.open.read]` | Review contractor не читает open requests. | То же. |
| 82 | `review_contractor[requests.owner.change]` | Review contractor не меняет owner заявки. | То же. |
| 83 | `review_contractor[requests.pricing.update]` | Review contractor не меняет pricing. | То же. |
| 84 | `review_contractor[requests.read]` | Review contractor не читает внутренние заявки. | То же. |
| 85 | `review_contractor[requests.status.update]` | Review contractor не меняет request status. | То же. |
| 86 | `review_contractor[requests.update]` | Review contractor не редактирует заявки. | То же. |
| 87 | `review_contractor[unavailability.manage_all]` | Review contractor не управляет общей недоступностью. | То же. |
| 88 | `review_contractor[unavailability.manage_own]` | Review contractor не управляет own unavailability в текущем onboarding-safe списке. | То же. |
| 89 | `review_contractor[unavailability.manage_subordinate]` | Review contractor не управляет subordinate unavailability. | То же. |
| 90 | `review_contractor[users.create]` | Review contractor не создает пользователей. | То же. |
| 91 | `review_contractor[users.login.update]` | Review contractor не меняет login. | То же. |
| 92 | `review_contractor[users.manager.update]` | Review contractor не меняет manager. | То же. |
| 93 | `review_contractor[users.password.update]` | Review contractor не меняет password. | То же. |
| 94 | `review_contractor[users.read]` | Review contractor не читает users list. | То же. |
| 95 | `review_contractor[users.role.update_any]` | Review contractor не меняет любые роли. | То же. |
| 96 | `review_contractor[users.role.update_economy]` | Review contractor не меняет economy roles. | То же. |
| 97 | `review_contractor[users.status.update]` | Review contractor не меняет user status. | То же. |
| 98 | `test_inactive_and_blacklist_never_pass_protected_checks[inactive]` | `inactive` не проходит protected checks даже с permissions. | Проверяет `requests.read` и `offers.status.update`. |
| 99 | `test_inactive_and_blacklist_never_pass_protected_checks[blacklist]` | `blacklist` не проходит protected checks даже с permissions. | Проверяет `requests.read` и `offers.status.update`. |

## Backend integration/API contract: 54 сценария

| # | Тест | Что проверяет | Способ проверки |
|---:|---|---|---|
| 1 | `test_requests_list_contract_has_item_actions_without_top_level_permissions` | Список заявок возвращает item-level actions и не возвращает top-level permissions. | FastAPI test client, fake service payload. |
| 2 | `test_open_requests_contract_has_item_actions_without_top_level_permissions` | Список open requests для contractor содержит actions на элементах без top-level permissions. | FastAPI endpoint с monkeypatch service. |
| 3 | `test_request_details_contract_contains_actions_and_hides_amounts_without_permission` | Детали заявки содержат actions и скрывают amounts без permission. | Fake current user и fake request details. |
| 4 | `test_offer_workspace_contract_contains_request_offer_chat_actions` | Offer workspace возвращает request/offer/chat actions. | Fake workspace service response. |
| 5 | `test_negative_authorization_file_download_forbidden_without_access` | Download file запрещен без доступа. | HTTP request к file endpoint, ожидается `403`. |
| 6 | `test_negative_authorization_inactive_user_forbidden_even_with_permission` | Inactive user блокируется даже с permission. | Dependency override current user. |
| 7 | `test_negative_authorization_scope_forbidden_on_update` | Scope/ownership запрет на update возвращает `403`. | Fake policy/service branch. |
| 8 | `test_endpoint_without_authorization_returns_401` | Protected endpoint без Authorization возвращает `401`. | Test app без credentials. |
| 9 | `test_endpoint_with_invalid_bearer_token_returns_401` | Невалидный Bearer token возвращает `401`. | Monkeypatch JWKS/token validation. |
| 10 | `test_active_user_with_required_permission_gets_success_on_protected_endpoint` | Active user с permission проходит protected endpoint. | Fake token/current user с нужным permission. |
| 11 | `test_review_inactive_blacklist_are_blocked_for_protected_endpoint[review]` | `review` user блокируется на protected endpoint. | Параметризованный status. |
| 12 | `test_review_inactive_blacklist_are_blocked_for_protected_endpoint[inactive]` | `inactive` user блокируется на protected endpoint. | Параметризованный status. |
| 13 | `test_review_inactive_blacklist_are_blocked_for_protected_endpoint[blacklist]` | `blacklist` user блокируется на protected endpoint. | Параметризованный status. |
| 14 | `test_request_email_verification_allows_review_contractor_only_for_limited_action` | Review contractor может ограниченное email verification действие. | Проверяет специальный onboarding endpoint branch. |
| 15 | `test_request_email_verification_blocks_inactive_user` | Inactive user не проходит email verification action. | Ожидает forbidden response. |
| 16 | `test_callback_without_code_or_state_returns_session_expired_redirect` | OIDC callback без code/state ведет на session-expired redirect. | Test client вызывает callback без параметров. |
| 17 | `test_callback_with_wrong_state_returns_session_expired_redirect` | Неверный OIDC state ведет на session-expired redirect. | Cookie/state mismatch. |
| 18 | `test_callback_with_missing_state_cookie_returns_session_expired_redirect` | Отсутствующий state cookie ведет на session-expired redirect. | Callback со state без cookie. |
| 19 | `test_callback_with_broken_state_cookie_returns_session_expired_redirect` | Поврежденный state cookie ведет на session-expired redirect. | Broken cookie payload. |
| 20 | `test_callback_registration_invite_email_mismatch_redirects_invalid` | Registration invite email mismatch ведет на invalid registration redirect. | Fake invite и fake OIDC profile. |
| 21 | `test_callback_repeated_registration_with_existing_email_redirects_already_registered` | Повторная регистрация existing email ведет на already-registered redirect. | Fake existing user/account. |
| 22 | `test_refresh_without_cookie_returns_401` | Refresh без session cookie возвращает `401`. | Test client без cookie. |
| 23 | `test_refresh_with_invalid_cookie_returns_401_and_clears_cookie` | Invalid refresh cookie возвращает `401` и очищает cookie. | Fake invalid cookie/session service. |
| 24 | `test_logout_clears_cookie_even_if_keycloak_services_fail` | Logout очищает cookie даже если Keycloak services падают. | Monkeypatch Keycloak failure. |
| 25 | `test_refresh_session_contract_contains_permissions_and_roles` | Refresh session payload содержит permissions, app roles, delegation roles. | Fake UoW/session и API response contract. |
| 26 | `test_refresh_session_permissions_do_not_depend_on_role_id` | Session permissions берутся из Keycloak roles, а не из `role_id`. | Fake token roles против business role id. |
| 27 | `test_contractor_can_create_offer_for_open_request` | Contractor создает offer для open request. | FastAPI POST с fake UoW/request visibility. |
| 28 | `test_contractor_cannot_create_offer_when_request_is_not_visible` | Contractor не создает offer, если request недоступна. | Fake service/policy возвращает forbidden. |
| 29 | `test_contractor_can_edit_only_own_offer_amount` | Contractor редактирует только свой offer amount. | Проверяет own offer success и чужой offer denial. |
| 30 | `test_employee_with_manual_offer_permission_can_create_manual_offer` | Internal employee с `offers.manual.create` создает manual offer. | POST manual offer endpoint с permission. |
| 31 | `test_accept_offer_requires_status_update_permission` | Accept offer требует `offers.status.update`. | User без permission получает `403`, с permission проходит. |
| 32 | `test_accepting_offer_changes_only_target_offer_status_in_current_implementation` | В backend service-level fake меняется только целевой offer; в реальной БД `order_database` есть trigger `offers_accept_reject_others`, который должен auto-reject остальные submitted offers. | Fake offers repo не моделирует DB trigger, поэтому это gap тестового контура, а не доказательство отсутствия правила во всей системе. |
| 33 | `test_cannot_accept_offer_for_closed_or_cancelled_request` | Желаемое правило "нельзя accept offer для closed/cancelled request" пока не реализовано. | Тест помечен `xfail`: текущий `OfferService.update_status` не проверяет статус заявки перед accept. |
| 34 | `test_workspace_access_is_restricted_to_allowed_users` | Workspace доступен только разрешенным пользователям. | Проверяет contractor owner/internal allowed и denied user. |
| 35 | `test_allowed_roles_can_create_request[1]` | Role id 1 может создать заявку. | POST `/api/v1/requests`, fake service вызывает `UserPolicy.ensure_can_create_request`. |
| 36 | `test_allowed_roles_can_create_request[5]` | Role id 5 может создать заявку. | То же. |
| 37 | `test_allowed_roles_can_create_request[6]` | Role id 6 может создать заявку. | То же. |
| 38 | `test_allowed_roles_can_create_request[7]` | Role id 7 может создать заявку. | То же. |
| 39 | `test_forbidden_roles_cannot_create_request[2]` | Role id 2 не может создать заявку. | POST ожидает `403`. |
| 40 | `test_forbidden_roles_cannot_create_request[4]` | Role id 4 не может создать заявку. | POST ожидает `403`. |
| 41 | `test_forbidden_roles_cannot_create_request[3]` | Role id 3 не может создать заявку. | POST ожидает `403`. |
| 42 | `test_contractor_cannot_access_internal_request_representation` | Contractor не видит internal request representation. | GET `/api/v1/requests/{id}` ожидает `403`. |
| 43 | `test_contractor_can_access_contractor_view_only_when_permission_allows` | Тест проверяет ожидаемый прямой guard `requests.contractor_view.read` через fake service, но текущий реальный `OfferService.get_request_view` использует видимость заявки + `offers.create`. | Monkeypatch fake service явно бросает `Forbidden` без `requests.contractor_view.read`; это фиксирует gap между ожидаемым контрактом и текущей реализацией. |
| 44 | `test_update_request_deadline_requires_deadline_permission` | Deadline update требует `requests.deadline.update`. | PATCH deadline с одним `requests.update` дает `403`. |
| 45 | `test_update_request_pricing_requires_pricing_and_amounts_permissions` | Pricing update требует pricing permission, не только amounts read. | PATCH `initial_amount` ожидает `403`. |
| 46 | `test_request_owner_change_requires_requests_owner_change_permission` | Owner change требует `requests.owner.change`. | PATCH `owner_user_id` ожидает `403`. |
| 47 | `test_invalid_request_status_transition_returns_409` | Невалидный status transition возвращает `409`. | PATCH status `archived`. |
| 48 | `test_closed_request_requires_consistent_amounts_when_updated` | Closed request с inconsistent amounts не обновляется. | PATCH deadline для closed request ожидает `409`. |
| 49 | `test_cancelled_request_can_be_updated_with_permissions` | Cancelled request можно обновить при permissions. | PATCH deadline ожидает `200`. |
| 50 | `test_request_can_be_closed_without_offers_when_final_matches_initial` | Request можно закрыть без offers, если final равен initial. | PATCH status `closed` ожидает `200`. |
| 51 | `test_request_can_be_closed_with_accepted_offer_amount` | Request можно закрыть с accepted offer amount. | Fake accepted offer и PATCH status `closed`. |
| 52 | `test_deleted_and_rejected_offers_do_not_break_request_stats_payload` | Deleted/rejected offers не ломают stats/details payload. | Fake details с offers deleted/rejected, проверка JSON stats. |
| 53 | `test_forbidden_role_gets_403_on_request_update` | Forbidden role получает `403` на request update. | Contractor PATCH request. |
| 54 | `test_anonymous_gets_401_on_protected_request_endpoint` | Anonymous получает `401` на protected request endpoint. | Override `get_current_user` бросает `Unauthorized`. |

## Frontend unit: 11 сценариев

| # | Тест | Что проверяет | Способ проверки |
|---:|---|---|---|
| 1 | `ProtectedRoute redirects anonymous users to login` | Anonymous user уходит на login. | React Testing Library + mocked `useAuth`. |
| 2 | `ProtectedRoute redirects users without business access to account page` | Authenticated user без business access уходит на account. | MemoryRouter routes и mocked session. |
| 3 | `ProtectedRoute renders child route for authenticated user with business access` | Authenticated user с business access видит protected child route. | Проверяет rendered child text. |
| 4 | `ProtectedRoute shows loading spinner during bootstrapping` | Bootstrapping state показывает spinner. | Проверяет `progressbar`. |
| 5 | `RoleRoute redirects to login when session is absent` | Route guard без session отправляет на login. | Mocked `useAuth`, MemoryRouter. |
| 6 | `RoleRoute redirects to account when business access is disabled` | Session без business access отправляется на account. | Mocked backend session payload. |
| 7 | `RoleRoute allows route access when required permission is present` | Route открывается при наличии required permission. | `allowedPermissions=["users.read"]`. |
| 8 | `RoleRoute redirects to role default path when required permission is missing` | При отсутствии permission route отправляет на default path роли. | Ожидает `/requests` placeholder element. |
| 9 | `AuthProvider bootstraps authenticated session from refresh endpoint` | AuthProvider читает refresh payload, ставит token/runtime и authenticated state. | Mock `refreshWebSession`, `setAuthToken`, `setAuthRuntime`. |
| 10 | `AuthProvider exposes anonymous state when bootstrap refresh fails` | Ошибка refresh переводит frontend в anonymous state и чистит token. | Mock rejected refresh promise. |
| 11 | `AuthProvider keeps business access and onboarding state from backend session payload` | Business access/onboarding state сохраняются из backend payload. | Mock session status `review`, `business_access=false`. |

## E2E smoke: 11 сценариев

| # | Тест | Что проверяет | Способ проверки |
|---:|---|---|---|
| 1 | `login smoke @smoke` | Superadmin может залогиниться через Keycloak, попасть на приложение и выйти. | Playwright browser, реальные `/api/v1/auth/oidc/login`, Keycloak login form, UI logout. |
| 2 | `economist requests smoke @smoke` | Economist логинится и открывает `/requests` без severe console errors. | Playwright, проверка URL, `networkidle`, visible `main`. |
| 3 | `contractor requests smoke @smoke` | Contractor логинится, открывает `/requests`, при наличии contractor link открывает contractor request view. | Playwright, условный переход по ссылке `/requests/{id}/contractor`. |
| 4 | `superadmin admin-page smoke @smoke` | Superadmin логинится и открывает `/admin`. | Playwright, проверка URL `/admin`, visible `main`. |
| 5 | `superadmin role routes smoke @smoke` | Superadmin имеет доступ к `/requests`, `/admin`, `/pm-dashboard`, `/feedback`. | Playwright role matrix scenario. |
| 6 | `admin role routes smoke @smoke` | Admin имеет доступ к `/requests` и `/admin`, но не к dashboard/feedback. | Playwright проверяет redirect при denied routes. |
| 7 | `project_manager role routes smoke @smoke` | Project manager имеет доступ к `/requests`, `/admin`, `/pm-dashboard`, но не к feedback. | Playwright route access matrix. |
| 8 | `lead_economist role routes smoke @smoke` | Lead economist имеет доступ к `/requests`, `/admin`, `/pm-dashboard`, но не к feedback. | Playwright route access matrix. |
| 9 | `economist role routes smoke @smoke` | Economist имеет доступ к `/requests` и `/admin`, но не к dashboard/feedback. | Playwright route access matrix. |
| 10 | `operator role routes smoke @smoke` | Operator имеет доступ к `/requests`, но не к admin/dashboard/feedback. | Playwright route access matrix. |
| 11 | `contractor role routes smoke @smoke` | Contractor имеет доступ к `/requests`, но не к admin/dashboard/feedback. | Playwright route access matrix. |

## Infrastructure smoke checks

| # | Проверка | Что проверяет | Способ проверки |
|---:|---|---|---|
| 1 | Gateway/Web root | Gateway/Web root отвечает `200/3xx`. | HTTP GET на `${BASE_URL}/`. |
| 2 | Backend health | Backend health endpoint отвечает `200`. | HTTP GET на `${BASE_URL}/health`. |
| 3 | API proxy | Gateway проксирует API login endpoint. | HTTP GET на `/api/v1/auth/oidc/login?next_path=%2F`, принимает `200/3xx/401/403`. |
| 4 | Gateway `/iam` | Keycloak realm доступен через gateway path `/iam`. | HTTP GET на `/iam/realms/{realm}`, warning если недоступен. |
| 5 | PostgreSQL connection | База принимает соединение. | `asyncpg.connect` по `SMOKE_DATABASE_URL` или `DATABASE_URL`. |
| 6 | PostgreSQL `SELECT 1` | База выполняет простой запрос. | `SELECT 1`. |
| 7 | PostgreSQL critical tables | Есть критичные таблицы `users`, `roles`, `profiles`, `user_auth_accounts`, `requests`, `offers`. | Query `information_schema.tables`. |
| 8 | Keycloak issuer | Public OIDC discovery доступен и issuer совпадает с env. | GET `.well-known/openid-configuration`. |
| 9 | Keycloak JWKS | JWKS endpoint доступен. | HTTP GET на `jwks_uri`. |
| 10 | S3/MinIO bucket | Bucket существует. | MinIO client `bucket_exists`. |
| 11 | S3/MinIO list objects | Bucket можно прочитать без destructive операций. | MinIO `list_objects`. |
| 12 | RabbitMQ AMQP | RabbitMQ принимает AMQP соединение. | `aio_pika.connect_robust`. |

## Keycloak permission model checks

| # | Проверка | Что проверяет | Способ проверки |
|---:|---|---|---|
| 1 | Admin API authentication | Скрипт может получить admin token. | Password grant через bootstrap admin или client credentials через admin service client. |
| 2 | Realm enabled | Realm существует и включен. | Keycloak Admin API `/admin/realms/{realm}`. |
| 3 | OIDC issuer | Public issuer совпадает с expected env. | OIDC discovery. |
| 4 | JWKS accessible | JWKS endpoint доступен. | HTTP GET на `jwks_uri`. |
| 5 | Web client exists | `KEYCLOAK_WEB_CLIENT_ID` существует. | Admin API clients query. |
| 6 | Web client flags | Web client public, standard flow enabled, implicit/direct grants/service accounts disabled. | Проверка client config. |
| 7 | Redirect URI | Web client содержит backend callback redirect URI. | Проверка `redirectUris`. |
| 8 | Web origins | Web client содержит frontend origin. | Проверка `webOrigins`. |
| 9 | API client exists | `KEYCLOAK_API_CLIENT_ID` существует. | Admin API clients query. |
| 10 | PermissionCodes present | Все backend `PermissionCodes` есть как client roles в API client. | Сравнение roles Keycloak с parsed backend source. |
| 11 | Unknown atomic roles | Неизвестные non-app/non-delegation роли предупреждаются или фейлятся в strict mode. | Role names diff. |
| 12 | Required app roles | `app.superadmin`, `app.admin`, `app.project_manager`, `app.lead_economist`, `app.economist`, `app.operator`, `app.contractor` существуют и composite. | Client role lookup. |
| 13 | Superadmin composite | `app.superadmin` включает все `PermissionCodes`. | Role composites. |
| 14 | Delegation roles | Delegation roles, если есть, проверяются как optional composites/non-composites. | Role prefix scan. |
| 15 | Admin service client exists | `KEYCLOAK_ADMIN_CLIENT_ID` существует. | Admin API clients query. |
| 16 | Admin service confidential | Admin service client confidential. | Проверка `publicClient=false`. |
| 17 | Admin service account | Service account включен. | Проверка `serviceAccountsEnabled=true`. |
| 18 | Admin service token | Если secret не placeholder, client credentials token request успешен. | Token endpoint. |
| 19 | Realm-management roles | Service account имеет `query-users`, `view-users`, `manage-users`. | Role mappings service account user. |
| 20 | Bootstrap superadmin user | Bootstrap user существует, enabled и имеет `app.superadmin`. | Admin API users query и role mappings. |

## CI и workflow checks

| # | Workflow/job | Что проверяет | Когда запускается |
|---:|---|---|---|
| 1 | `CI / Backend Unit Tests` | `python -m pytest backend/tests/unit -q`. | Push/PR в `dev_process`, `dev`, `test`. |
| 2 | `CI / Backend Integration/API Contract Tests` | `python -m pytest backend/tests/integration -q`. | Push/PR в `dev_process`, `dev`, `test`. |
| 3 | `CI / Frontend Lint/Test/Build` | `npm --prefix web run lint`, `npm --prefix web run test:unit`, `npm --prefix web run build`. | Push/PR в `dev_process`, `dev`, `test`. |
| 4 | `E2E Smoke (Manual)` | Устанавливает frontend/backend deps и запускает `./scripts/e2e-smoke.sh`. | Manual `workflow_dispatch`. |
| 5 | `Release Smoke (Manual)` | Запускает infra smoke, Keycloak permission check и optional e2e smoke. | Manual `workflow_dispatch`. |
| 6 | `Deploy to VPS` | Перед deploy проверяет prerequisites external `order_database`, network, migrations и запускает compose/bootstrap. | Push в `test` или manual dispatch. |

## Локальные shell/PowerShell helpers

| Скрипт | Что запускает |
|---|---|
| `scripts/test-unit.ps1` / `.sh` | Backend unit tests с `PYTHONPATH=backend`. |
| `scripts/test-integration.ps1` / `.sh` | Backend integration/API contract tests с `PYTHONPATH=backend`. |
| `scripts/smoke-infra.ps1` / `.sh` | Python module `app.scripts.smoke_services`. |
| `scripts/check-keycloak.ps1` / `.sh` | Python module `app.scripts.check_keycloak_permission_model`. |
| `scripts/check-keycloak-bootstrap.ps1` / `.sh` | Bootstrap-level Keycloak checks через `kcadm`/admin credentials. |
| `scripts/e2e-smoke.ps1` / `.sh` | Optional E2E user provisioning, Playwright `@smoke`, cleanup. |
| `scripts/test-release.ps1` / `.sh` | Full release smoke chain: unit, integration, infra smoke, Keycloak model, frontend build, optional e2e. |
| `scripts/local-smoke-infra.commands.ps1` | Локальные рабочие команды для smoke/release запусков на текущей машине. |
