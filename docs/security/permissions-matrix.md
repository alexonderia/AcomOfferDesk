# Permissions Matrix

Source of truth: `backend/app/domain/permissions.py`.

Legend: `Y` = granted, `N` = not granted.

## Access Matrix

| Permission | SA | AD | PM | LE | EC | OP | CT |
|---|---|---|---|---|---|---|---|
| `users.read` | Y | Y | Y | Y | Y | N | N |
| `users.create` | Y | Y | N | Y | N | N | N |
| `users.status.update` | Y | Y | Y | Y | Y | N | N |
| `users.role.update_any` | Y | Y | N | N | N | N | N |
| `users.role.update_economy` | Y | N | Y | Y | N | N | N |
| `users.login.update` | Y | Y | N | N | N | N | N |
| `users.password.update` | Y | Y | N | N | N | N | N |
| `users.manager.update` | Y | N | Y | Y | Y | N | N |
| `profile.manage_own` | Y | Y | Y | Y | Y | Y | Y |
| `profile.manage_any` | Y | Y | N | Y | N | N | N |
| `company_contacts.manage_own` | Y | N | N | N | N | N | Y |
| `company_contacts.manage_any` | Y | Y | N | Y | N | N | N |
| `requests.read` | Y | N | Y | Y | Y | Y | N |
| `requests.amounts.read` | Y | N | Y | Y | Y | Y | N |
| `requests.create` | Y | N | N | Y | Y | Y | N |
| `requests.update` | Y | N | N | Y | Y | Y | N |
| `requests.pricing.update` | Y | N | N | Y | Y | Y | N |
| `requests.deadline.update` | Y | N | N | Y | Y | Y | N |
| `requests.status.update` | Y | N | N | Y | Y | Y | N |
| `requests.owner.change` | Y | N | Y | Y | N | N | N |
| `requests.files.upload` | Y | N | N | Y | Y | N | N |
| `requests.files.delete` | Y | N | N | Y | Y | N | N |
| `requests.open.read` | Y | N | N | N | N | N | Y |
| `requests.offered.read` | Y | N | N | N | N | N | Y |
| `requests.contractor_view.read` | Y | N | N | N | N | N | Y |
| `requests.email_notifications.send` | Y | N | N | Y | Y | N | N |
| `requests.deleted_alerts.mark_viewed` | Y | N | N | Y | Y | N | N |
| `offers.create` | Y | N | N | N | N | N | Y |
| `offers.manual.create` | Y | N | N | Y | Y | N | N |
| `offers.workspace.read` | Y | N | Y | Y | Y | N | Y |
| `offers.update` | Y | N | N | Y | Y | N | Y |
| `offers.amount.update` | Y | N | N | Y | Y | N | Y |
| `offers.details.update` | Y | N | N | Y | Y | N | Y |
| `offers.status.update` | Y | N | N | Y | Y | N | Y |
| `offers.files.upload` | Y | N | N | N | N | N | Y |
| `offers.files.delete` | Y | N | N | N | N | N | Y |
| `offers.contractor_info.read` | Y | N | Y | Y | Y | N | Y |
| `chat.read` | Y | N | Y | Y | Y | N | Y |
| `chat.message.send` | Y | N | N | Y | Y | N | Y |
| `chat.message.attach` | Y | N | N | Y | Y | N | Y |
| `chat.receipts.mark_received` | Y | N | N | Y | Y | N | Y |
| `chat.receipts.mark_read` | Y | N | N | Y | Y | N | Y |
| `feedback.read` | Y | N | N | N | N | N | N |
| `feedback.create` | Y | Y | Y | Y | Y | Y | Y |
| `dashboard.process.read` | Y | N | Y | Y | N | N | N |
| `dashboard.savings.read` | Y | N | Y | Y | N | N | N |
| `dashboard.plans.read` | Y | N | Y | Y | N | N | N |
| `normative_files.read` | Y | N | Y | Y | Y | Y | N |
| `normative_files.create` | Y | N | N | Y | N | N | N |
| `normative_files.manage` | Y | N | N | Y | N | N | N |
| `files.download` | Y | N | Y | Y | Y | N | Y |
| `unavailability.manage_all` | Y | N | N | N | N | N | N |
| `unavailability.manage_own` | Y | N | Y | Y | Y | N | N |
| `unavailability.manage_subordinate` | Y | N | Y | Y | Y | N | N |
| `contractors.manual.create` | Y | Y | Y | Y | Y | N | N |
| `contractors.manual.manage` | Y | Y | Y | Y | Y | N | N |

## Web App Behavior by Role

| Role | Main sections in web app | Typical allowed actions |
|---|---|---|
| `superadmin` | `/admin`, `/requests`, `/pm-dashboard`, `/pm-dashboard/savings`, `/pm-dashboard/plan`, `/feedback` | Full management across users, requests, offers, contractors, dashboards, normative files and statuses |
| `admin` | `/admin` | User administration (`users.*` incl. login/password), manual contractors create/manage, no request/offer workflow operations |
| `project_manager` | `/pm-dashboard`, `/pm-dashboard/savings`, `/pm-dashboard/plan`, `/requests`, `/admin` | Manage hierarchy assignments, change request owner, manage manual contractors, set subordinate unavailability, economy-role changes for subordinates |
| `lead_economist` | `/pm-dashboard`, `/pm-dashboard/savings`, `/pm-dashboard/plan`, `/requests`, `/admin` | Full request/offer workflow, create manual offers, manage normative files, manage contractor data (`profile.manage_any`, `company_contacts.manage_any`), economy-role changes for subordinates |
| `economist` | `/requests`, `/admin` | Request/offers processing in scope, manual offers, subordinate unavailability, manual contractors create/manage (no dashboard sections by permission) |
| `operator` | `/requests` | Create/read/update requests (pricing/deadline/status), view normative files, no offer/chat/admin/dashboard features |
| `contractor` | `/requests` (tabs: open/my), `/requests/:id/contractor`, `/offers/:id/workspace` | Create offers, work in workspace, manage own company contacts, chat and files within own offer scope |

## Special Rules

1. `users.role.update_economy` is allowed only for subordinate users and only inside economy contour roles: `project_manager`, `lead_economist`, `economist`, `operator`.
2. `requests.contractor_view.read` gives access to contractor-specific request representation (`/requests/:id/contractor`) with limited data visibility.
3. Dashboard permissions are split by intent: `dashboard.process.read`, `dashboard.savings.read`, `dashboard.plans.read`. UI navigation should hide tabs that are not granted.
4. `app.*` и `delegation.*` роли из Keycloak не считаются atomic permissions сами по себе: доступ дают только известные permission-коды из `PermissionCodes`.
5. Для `status=review` разрешены только onboarding-safe contractor действия (`profile.manage_own`, `company_contacts.manage_own`); `inactive`/`blacklist` не проходят protected проверки.
6. Frontend использует permissions/actions только для UX. Финальное enforcement-решение всегда принимает backend endpoint/policy/service слой.
