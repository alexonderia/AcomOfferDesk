# Permissions Matrix

Source of truth: `backend/app/domain/permissions.py`.

Legend: `Y` = granted, `N` = not granted.

Footnotes:

1. `users.login.update` остаётся в bootstrap ролей `superadmin`/`admin`, но **смена логина не реализована**: `users.id` неизменяем после создания. В UI логин только для чтения (`/admin`, `/contractors`, карточка контрагента); `PATCH /api/v1/users/{id}/manual-contractor` не принимает `login`.
2. `users.password.update` — пароль управляется Keycloak; смена через приложение отключена.

## Access Matrix

Legend: `SA`=superadmin, `AD`=admin, `SO`=security_officer, `PM`=project_manager, `LE`=lead_economist, `EC`=economist, `OP`=operator, `CT`=contractor.

| Permission | SA | AD | SO | PM | LE | EC | OP | CT |
|---|---|---|---|---|---|---|---|---|
| `users.read` | Y | Y | N | Y | Y | Y | N | N |
| `users.create` | Y | Y | N | N | Y | N | N | N |
| `users.status.update` | Y | Y | N | Y | Y | Y | N | N |
| `users.role.update_any` | Y | Y | N | N | N | N | N | N |
| `users.role.update_economy` | Y | N | N | Y | Y | N | N | N |
| `users.login.update` | Y¹ | Y¹ | N | N | N | N | N | N |
| `users.password.update` | Y² | Y² | N | N | N | N | N | N |
| `users.manager.update` | Y | N | N | Y | Y | Y | N | N |
| `profile.manage_own` | Y | Y | Y | Y | Y | Y | Y | Y |
| `profile.manage_any` | Y | Y | N | N | Y | N | N | N |
| `company_contacts.manage_own` | Y | N | N | N | N | N | N | Y |
| `company_contacts.manage_any` | Y | Y | N | N | Y | N | N | N |
| `requests.read` | Y | N | N | Y | Y | Y | Y | N |
| `requests.amounts.read` | Y | N | N | Y | Y | Y | Y | N |
| `requests.create` | Y | N | N | N | Y | Y | Y | N |
| `requests.update` | Y | N | N | N | Y | Y | Y | N |
| `requests.pricing.update` | Y | N | N | N | Y | Y | Y | N |
| `requests.deadline.update` | Y | N | N | N | Y | Y | Y | N |
| `requests.status.update` | Y | N | N | N | Y | Y | Y | N |
| `requests.owner.change` | Y | N | N | Y | Y | N | N | N |
| `requests.files.upload` | Y | N | N | N | Y | Y | N | N |
| `requests.files.delete` | Y | N | N | N | Y | Y | N | N |
| `requests.open.read` | Y | N | N | N | N | N | N | Y |
| `requests.offered.read` | Y | N | N | N | N | N | N | Y |
| `requests.contractor_view.read` | Y | N | N | N | N | N | N | Y |
| `requests.email_notifications.send` | Y | N | N | N | Y | Y | N | N |
| `requests.deleted_alerts.mark_viewed` | Y | N | N | N | Y | Y | N | N |
| `offers.create` | Y | N | N | N | N | N | N | Y |
| `offers.manual.create` | Y | N | N | N | Y | Y | N | N |
| `offers.workspace.read` | Y | N | N | Y | Y | Y | N | Y |
| `offers.update` | Y | N | N | N | Y | Y | N | Y |
| `offers.amount.update` | Y | N | N | N | Y | Y | N | Y |
| `offers.details.update` | Y | N | N | N | Y | Y | N | Y |
| `offers.status.update` | Y | N | N | N | Y | Y | N | Y |
| `offers.files.upload` | Y | N | N | N | N | N | N | Y |
| `offers.files.delete` | Y | N | N | N | N | N | N | Y |
| `offers.contractor_info.read` | Y | N | N | Y | Y | Y | Y | Y |
| `chat.read` | Y | N | N | Y | Y | Y | N | Y |
| `chat.message.send` | Y | N | N | N | Y | Y | N | Y |
| `chat.message.attach` | Y | N | N | N | Y | Y | N | Y |
| `chat.receipts.mark_received` | Y | N | N | N | Y | Y | N | Y |
| `chat.receipts.mark_read` | Y | N | N | N | Y | Y | N | Y |
| `feedback.read` | Y | N | N | N | N | N | N | N |
| `feedback.create` | Y | Y | Y | Y | Y | Y | Y | Y |
| `dashboard.process.read` | Y | N | N | Y | Y | Y | N | N |
| `dashboard.savings.read` | Y | N | N | Y | Y | Y | N | N |
| `dashboard.plans.read` | Y | N | N | Y | Y | Y | N | N |
| `normative_files.read` | Y | N | N | Y | Y | Y | Y | N |
| `normative_files.create` | Y | N | N | N | Y | N | N | N |
| `normative_files.manage` | Y | N | N | N | Y | N | N | N |
| `normative_files.status.update` | Y | N | N | N | Y | N | N | N |
| `files.download` | Y | N | N | Y | Y | Y | N | Y |
| `unavailability.manage_all` | Y | N | N | N | N | N | N | N |
| `unavailability.manage_own` | Y | N | N | Y | Y | Y | N | N |
| `unavailability.manage_subordinate` | Y | N | N | Y | Y | Y | N | N |
| `contractors.read` | Y | N | Y | Y | Y | Y | N | N |
| `contractors.profile.read` | Y | N | Y | Y | Y | Y | N | N |
| `contractors.profile.status.update` | Y | N | Y | N | N | N | N | N |
| `contractors.manual.create` | Y | Y | N | Y | Y | Y | N | N |
| `contractors.manual.manage` | Y | Y | N | Y | Y | Y | N | N |

## Web App Behavior by Role

| Role | Main sections in web app | Typical allowed actions |
|---|---|---|
| `superadmin` | `/admin`, `/requests`, `/pm-dashboard`, `/pm-dashboard/savings`, `/pm-dashboard/plan`, `/feedback` | Full management across users, requests, offers, contractors, dashboards, normative files and statuses |
| `admin` | `/admin` | User administration (без смены логина/пароля), manual contractors create/manage, no request/offer workflow operations |
| `security_officer` | `/contractors` | Read contractor list/profile, update contractor status, use own profile and feedback, no `/admin`, requests, offers, chats, dashboards or normative files |
| `project_manager` | `/pm-dashboard`, `/pm-dashboard/savings`, `/pm-dashboard/plan`, `/requests`, `/admin`, `/contractors` | Read requests/offers/chats across department; change request owner; read contractors and manage users hierarchy/manual contractors/subordinate unavailability/economy-role changes for subordinates |
| `lead_economist` | `/pm-dashboard`, `/pm-dashboard/savings`, `/pm-dashboard/plan`, `/requests`, `/admin`, `/contractors` | Full request/offer workflow, create manual offers, manage normative files, read contractors, manage contractor data (`profile.manage_any`, `company_contacts.manage_any`), economy-role changes for subordinates |
| `economist` | `/pm-dashboard/plan`, `/requests`, `/admin`, `/contractors` | Request/offers processing in scope, manual offers, subordinate unavailability, read contractors, manual contractors create/manage, plan dashboard (only delegated branch and below) |
| `operator` | `/requests` | Own unassigned requests (owner still operator): create/read/update (pricing/deadline/status), view offer list on request details without workspace/chat, view normative files, no admin/dashboard |
| `contractor` | `/requests` (tabs: open/my), `/requests/:id/contractor`, `/offers/:id/workspace` | Create offers, work in workspace, manage own company contacts, chat and files within own offer scope |

## Special Rules

1. `users.role.update_economy` is allowed only for subordinate users and only inside economy contour roles: `project_manager`, `lead_economist`, `economist`, `operator`.
2. `requests.contractor_view.read` gives access to contractor-specific request representation (`/requests/:id/contractor`) with limited data visibility.
3. Dashboard permissions are split by intent: `dashboard.process.read`, `dashboard.savings.read`, `dashboard.plans.read`. UI navigation should hide tabs that are not granted.
4. `app.*` и `delegation.*` роли из Keycloak не считаются atomic permissions сами по себе: доступ дают только известные permission-коды из `PermissionCodes`.
5. Для `status=review` разрешены только onboarding-safe contractor действия (`profile.manage_own`, `company_contacts.manage_own`); `inactive`/`blacklist` не проходят protected проверки.
6. Frontend использует permissions/actions только для UX. Финальное enforcement-решение всегда принимает backend endpoint/policy/service слой.
7. Backend contractor-view path (`GET /api/v1/requests/{id}/contractor-view`) должен проверять `requests.contractor_view.read` на service-level.
8. Backend offer lifecycle path (`PATCH /api/v1/offers/{id}/status`) должен отклонять `accepted`, если связанная заявка уже `closed` или `cancelled`.
9. Логин пользователя (`users.id`) **неизменяем** после создания. Для manual-контрагентов логин генерируется при `contractors.manual.create`; `contractors.manual.manage` меняет профиль и контакты компании, но не логин. В таблице контрагентов и админке поле «Логин» read-only.

## Test Policy

- Backend role/access matrix: `backend/tests/unit/test_role_access_matrix_unit.py`.
- Backend auth context и filtering: `backend/tests/unit/test_auth_context_unit.py`, `backend/tests/unit/test_authorization_unit.py`.
- Backend enforcement contracts: `backend/tests/integration/test_auth_enforcement_contract.py`.
- Frontend route/navigation UX: `web/src/app/routes/RoleRoute.test.tsx`, `web/src/features/header/model/buildHeaderConfig.test.ts`.
- Browser role matrix: `web/e2e/roles.access.spec.ts` (`@roles`, manual extended e2e).
- Dashboard permission/calculation coverage: `backend/tests/unit/test_dashboard_calculations_unit.py`, `web/e2e/dashboard.extended.spec.ts` (`@dashboard`).
- При изменении этой матрицы обновлять `backend/app/domain/permissions.py`, Keycloak bootstrap docs/scripts при необходимости, backend/frontend tests и `docs/development/test-coverage-map.md`.

## Department Delegation Model (2026-05)

`department.*` permissions are separate atomic access codes used only for department-scope expansion. They are not aliases of regular `requests.*`, `offers.*`, `chat.*`, `files.*`, `dashboard.*`, `plans.*` permissions.

Atomic `department.*` permissions:

- `department.requests.read`
- `department.requests.update`
- `department.requests.status_update`
- `department.requests.assign`
- `department.offers.update`
- `department.offers.accept`
- `department.offers.reject`
- `department.chats.read`
- `department.files.read`
- `department.files.upload`
- `department.files.delete`
- `department.dashboard.read`
- `department.plans.read`
- `department.plans.manage`

Keycloak composite delegation roles in client `acom-api`:

- `delegation.department.requests.read` -> `department.requests.read`
- `delegation.department.requests.update` -> `department.requests.update`
- `delegation.department.requests.status_update` -> `department.requests.status_update`
- `delegation.department.requests.assign` -> `department.requests.assign`
- `delegation.department.offers.update` -> `department.offers.update`
- `delegation.department.offers.accept` -> `department.offers.accept`
- `delegation.department.offers.reject` -> `department.offers.reject`
- `delegation.department.chats.read` -> `department.chats.read`
- `delegation.department.files.read` -> `department.files.read`
- `delegation.department.files.upload` -> `department.files.upload`
- `delegation.department.files.delete` -> `department.files.delete`
- `delegation.department.dashboard.read` -> `department.dashboard.read`
- `delegation.department.plans.read` -> `department.plans.read`
- `delegation.department.plans.manage` -> `department.plans.manage`

Rules:

1. `delegation.department.*` are not included in any `app.*` role by default.
2. `keycloak_user_role_sync` updates only `app.*` alignment by `users.id_role` and must not remove manually assigned `delegation.department.*`.
3. No new business role is introduced (`lead_economist + delegation.department.*` is not a new role).
4. No DB table is used as source of truth for delegation checklist state; source of truth is Keycloak client role mappings for `acom-api`.
5. Frontend remains UX-only and uses backend-provided `permissions`/`actions`; backend remains enforcement layer.
6. `department.requests.status_update` must be enforced independently for foreign department requests; `department.requests.update` is not a substitute for status transitions.

## Contractor Delegation Model (2026-05)

Atomic `contractors.*` permissions:

- `contractors.read`
- `contractors.profile.read`
- `contractors.profile.status.update`

Keycloak composite delegation role in client `acom-api`:

- `delegation.contractors.profile.status.update` -> `contractors.read`, `contractors.profile.read`, `contractors.profile.status.update`

Rules:

1. `delegation.contractors.profile.status.update` is not included in any `app.*` role by default.
2. Only `superadmin` can assign or revoke this delegation for users with role `lead_economist` (ВЭ).
3. `contractors.*` permissions are granted only via `delegation.contractors.profile.status.update`, not via bare atomic codes in token claims.
4. Frontend section `/contractors` is shown only when `contractors.read` is present; status changes require `contractors.profile.status.update`.
5. `PATCH /api/v1/contractors/{id}/status` changes status only for users with role `contractor`.

## Business Scope Rules (2026-05)

1. Department visibility: PM/LE/EC users in the same PM subtree can read requests, offers, and chats for each other; edit/chat-send remains limited to hierarchy chain or `department.*` delegation.
2. Module statistics: LE and EC dashboard scope is the LE module subtree; PM dashboard scope is the whole department.
3. Plan dashboard: EC sees the module plan tree via their LE root; plan edit/delegate remains hierarchy-only (subordinates required for delegation).
