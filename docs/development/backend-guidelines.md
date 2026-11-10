# Backend: правила разработки

Актуальные правила слоёв, данных и ошибок. Контракты доступа описаны в [матрице прав](../security/permissions-matrix.md), входа — в [IAM](../security/auth-and-onboarding.md).

## Required Patterns

- Inspect affected files before proposing edits.
- Keep API routes thin: validate input, collect dependencies, call services, serialize output.
- Keep business rules in `backend/app/domain/*` or `backend/app/services/*`.
- Keep repositories limited to CRUD/query persistence work.
- Use `UnitOfWork` for transaction boundaries.
- When a service receives runtime URLs or adapters through its constructor, keep helper branches aligned with those injected values instead of re-reading equivalent global settings only. This preserves direct service tests and non-HTTP entrypoints.
- Use backend permissions/action flags as the source of truth for allowed actions.
- Keep E2E IAM users and credentials explicit in environment secrets; smoke tests must use the same BFF login entrypoint as a browser.
- Review-stage contractor onboarding must use dedicated registration-only self-profile endpoints. Do not weaken the normal `/users/me*` permission gates for already-authenticated pages.
- Keep in-memory integration fixtures aligned with current dataclass constructors and service factory signatures; when request/offer schemas gain or lose fields, update the test factories in the same change.
- Keep removed external messenger integrations out of runtime, API, frontend, compose, and worker delivery paths.
- For DB changes, include SQL/migration patch and rollout notes.
- For infra changes, preserve `gateway`, `project_net`, and tunnel routing.

---

## Forbidden Patterns

- Business logic in API routes.
- Permission enforcement only on the frontend.
- Repository methods that decide business policy.
- Direct public exposure of backend, IAM internal APIs, RabbitMQ, MinIO, PostgreSQL, or admin ports in `test`/`prod`.
- Hardcoded secrets, tokens, passwords, or production hostnames.
- Temporary placeholder implementations, mock-only production paths, or TODO-dependent behavior.
- Reintroducing external messenger runtime or UI through legacy database compatibility values.
- Changing DB schema because it is convenient rather than required by the task.

---

## Permissions Checklist

When a backend change affects permissions/actions:

- [ ] Permission codes are defined/updated centrally in `backend/app/domain/permissions.py`.
- [ ] Domain policies or service rules enforce the behavior.
- [ ] Internal staff visibility uses the shared scope services consistently:
  `StaffAccessScopeService` for module scope and `DepartmentScopeService` for subdivision/department scope.
- [ ] User/staff list endpoints do not fall back to ad hoc direct-subordinate-only filtering when module/department scope already exists elsewhere in requests/plans.
- [ ] Internal staff list scope remains aligned with the current contract:
  project manager -> department/subdivision scope;
  lead economist / economist -> module scope by default;
  department delegation permissions -> broaden to department/subdivision scope.
- [ ] `department.requests.status_update` is enforced independently for foreign department requests; `department.requests.update` must not implicitly grant status transitions.
- [ ] Department offer status actions remain independent: `department.requests.update` must not implicitly grant `department.offers.accept` or `department.offers.reject`.
- [ ] Department offer content actions remain independent: `department.requests.update` must not implicitly grant amount/file edits; use `department.offers.update`.
- [ ] Contractor-specific request view checks `requests.contractor_view.read` explicitly at backend service/policy level.
- [ ] Offer acceptance flow rejects `accepted` transition when parent request is already `closed` or `cancelled`.
- [ ] API responses expose backend-owned permissions/actions/links for frontend UX.
- [ ] Frontend does not become the final decision maker.
- [ ] Tests or targeted validation cover denied and allowed paths when feasible.

---

## Testing Requirements

Run the narrowest meaningful checks for the task and report them. Команды и настройка окружения: [стратегия тестирования](testing-strategy.md).

If checks cannot be run, state why and list the residual risk.

## Directory Structure

This file documents where backend code lives in the current repository.

### Actual Layout

```text
backend/app/
  api/v1/               HTTP route modules
  domain/               Policies, permission logic, authorization helpers, exceptions
  services/             Application use cases and orchestration
  repositories/         Persistence and query code
  schemas/              Pydantic request/response DTOs
  models/               SQLAlchemy ORM models
  infrastructure/       External adapters: DB, email, MinIO, file guard, queue consumers
  core/                 Config, security, tokens, utilities, unit of work
  realtime/             WebSocket/realtime runtime helpers
  scripts/              Maintenance and synchronization scripts
  main.py               FastAPI app wiring
```

### Placement Rules

- `api/v1` routes should parse HTTP input, call services, and serialize DTOs.
- `services` should own use cases and cross-repository orchestration.
- `domain` should own policies, permission decisions, and pure business logic.
- `repositories` should not decide whether an action is allowed.
- `schemas` should mirror the API contract, not invent frontend-only fields.
- `models` should match the database schema.
- `infrastructure` should hold adapters to SMTP, MinIO, RabbitMQ, file guard, or other external systems.
- `scripts` should be for one-off or maintenance behavior, not user-facing flows.

### Concrete Modules

- `backend/app/api/v1/auth.py`, `backend/app/core/iam_flow.py`, and `backend/app/infrastructure/iam_client.py` cover the Acom side of the IAM auth/session flow.
- `backend/app/api/v1/requests.py`, `offers.py`, `users.py`, `plans.py`, `contractors.py`, `normative_files.py`, `notifications.py`, `dashboard.py`, `feedback.py`, and `ws.py` are the current route groups.
- `backend/app/api/action_flags.py` computes backend-owned action flags for response payloads.
- `backend/app/domain/permissions.py` is the canonical permission matrix.

### Do

- Extend the existing module that already owns the use case.
- Keep route handlers small.
- Keep data access in repositories.
- Keep permission decisions in domain/service code.

### Don't

- Do not create a parallel service layer for an existing use case.
- Do not move business rules into route handlers.
- Do not duplicate schema or DTO definitions just to satisfy one page.


## Database Guidelines

These rules describe the actual persisted schema used by the backend.

### Main Table Groups

#### Identity And Access

- `roles`
- `users`
- `profiles`
- `company_contacts`
- `user_auth_accounts`
- `user_contact_channels`
- `user_notification_preferences`

#### Requests, Offers, And Chat

- `requests`
- `request_hidden_contractors`
- `offers`
- `request_offer_stats`
- `chats`
- `messages`
- `chat_participants`
- `message_receipts`
- `user_notifications`

#### Files And Storage

- `storage_objects`
- `files`
- `request_files`
- `offer_files`
- `message_files`
- `normative_files`

#### Other Domain Tables

- `feed_back`
- `user_status_periods`
- `economy_plans`

### Important Constraints

- `users.status` is constrained to `active`, `inactive`, `review`, or `blacklist`.
- `requests.status` is constrained to `open`, `review`, `closed`, or `cancelled`.
- `offers.status` is constrained to `submitted`, `deleted`, `accepted`, or `rejected`.
- `messages.type` is constrained to `text`, `system`, `file`, `mixed`, or `email`.
- `normative_files.document_status` is constrained to `actual` or `outdated`.
- `user_status_periods.status` is constrained to the allowed absence states used by the product.
- `user_auth_accounts.provider` is constrained to `iam`, `keycloak`, `telegram`, `max`, `phone`, or `email`; only `provider='iam'` participates in runtime authentication, while the other values are historical compatibility data.
- `user_contact_channels.channel_type` is constrained to `email`, `phone`, `telegram`, or `max`.
- The `telegram` and `max` values above are storage compatibility only; do not remove or rename them without a schema migration, and do not expose them as active runtime channels.
- `user_notification_preferences.notification_type` is constrained to `chat`, `request`, `offer`, or `system`.
- `economy_plans.period_end` must be greater than or equal to `period_start`.

### File Storage Contract

- `storage_objects` is the canonical record for blob metadata.
- `files` stores the original file name and points to `storage_objects`.
- Domain-specific attachment tables (`request_files`, `offer_files`, `message_files`) link a file to a business object.
- Do not bypass `storage_objects` by storing opaque file paths directly on request/offer/message rows.

### Schema Rules

- Do not add a new table or column unless the task explicitly requires it.
- If a field is needed in the UI, confirm the backend schema first.
- If a backend DTO changes, confirm the database and API contract together.
- If the change affects file ownership or notification delivery, check the join tables and the worker contract as well.


## Error Handling

Use the project exceptions that already exist in the backend domain layer.

### Core Exceptions

- `NotFound`
- `Conflict`
- `Unauthorized`
- `Forbidden`

### Rules

- Raise a domain exception when the business rule is violated or a resource is missing.
- Let FastAPI/Pydantic handle validation errors for malformed input.
- Preserve the original exception context when wrapping a lower-level failure.
- Do not turn every error into a generic 500 if a more specific domain error exists.
- Do not leak secrets, tokens, or raw internal stack traces to users.

### API Behavior

- API handlers should translate domain failures into consistent HTTP responses.
- Validation failures should remain validation failures.
- Authorization failures should be handled close to the access check, not far downstream.
- If an error message is user-facing, make it actionable and consistent with the project language policy.

### Good Practice

- Check existence before trying to mutate a dependent object.
- Distinguish "not found" from "not allowed" when the user experience depends on it.
- Use specific exception types in services and policies so route handlers stay small.


## Logging Guidelines

Logging should help operators understand what happened without exposing secrets.

### What To Log

- Auth/session failures with enough context to troubleshoot safely
- Permission denials when the business outcome matters
- IAM provisioning, synchronization, and reconciliation results
- Notification delivery failures and queue consumption problems
- File upload guard rejections
- Unexpected repository or external-service failures

### What Not To Log

- Passwords
- Access tokens
- Refresh tokens
- Client secrets
- SMTP passwords
- Raw private file contents
- Full request payloads when they may contain sensitive data

### Style

- Prefer structured, searchable log messages.
- Include identifiers such as `user_id`, `request_id`, `offer_id`, or queue names when they help debugging.
- Log the cause once near the failing boundary instead of repeating the same error in every layer.
- Keep debug-only noise out of production paths.
