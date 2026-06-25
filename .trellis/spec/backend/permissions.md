# Permissions And Roles

This file captures the current permission model in the backend.

## Source Of Truth

- `backend/app/domain/permissions.py` defines the canonical permission codes.
- `backend/app/services/keycloak_app_roles.py` maps local role IDs to Keycloak app roles.
- `backend/app/domain/auth_context.py` combines local role ceilings, token roles, and delegation scopes.
- `backend/app/api/action_flags.py` turns backend permission decisions into response `actions`.

## Roles

Current local role IDs:

- `1` - `superadmin`
- `2` - `admin`
- `3` - `contractor`
- `4` - `project_manager`
- `5` - `lead_economist`
- `6` - `economist`
- `7` - `operator`
- `8` - `security_officer`

Keycloak app roles:

- `app.superadmin`
- `app.admin`
- `app.project_manager`
- `app.lead_economist`
- `app.economist`
- `app.operator`
- `app.security_officer`
- `app.contractor`

## Permission Families

The backend permission codes are grouped by domain:

- users and user management
- profile and company contacts
- requests
- offers
- chat and message receipts
- feedback
- dashboards and plans
- normative files
- file downloads
- unavailability
- contractors
- units hierarchy
- department-scoped request/offer/chat/dashboard actions

## Contract Rules

- Backend permissions are authoritative.
- Frontend `role_id` checks are UX hints only.
- Backend `actions` arrays/objects are the real per-resource control surface.
- If a permission changes, update:
  - the backend permission map
  - the Keycloak role mapping/bootstrap
  - the backend access checks
  - the frontend guards and menus

## Practical Rules

- Prefer `has_permission(...)` or the existing policy helpers instead of string-comparing roles directly.
- Use role ceilings for access control, not just for display decisions.
- `department.*` and `delegation.*` scopes are extensions, not replacements, for the normal permission matrix.
- Do not add a parallel permission system in the frontend.

## Units Hierarchy Contract

- `units.read` gates both the actual units tree and the recommended hierarchy tree derived from `users.id_parent`.
- `units.create`, `units.update`, and `units.members.manage` apply only to real `units` / `unit_members` mutations.
- The recommended hierarchy is a read-only helper source built from the current user management chain and must not be treated as a second writable unit model.

## Scenario: Contractor Root-Unit Scope And Bindings

### 1. Scope / Trigger
- Trigger: contractor access moved from global visibility to root-unit-scoped visibility with new backend APIs, action flags, and duplicate-handling behavior during manual contractor creation.

### 2. Signatures
- Backend APIs:
  `GET /api/v1/contractors/{contractor_id}/root-units`
  `PUT /api/v1/contractors/{contractor_id}/root-units`
  `POST /api/v1/users/manual-contractors`
  manual contractor creation inside manual-offer flow
- Backend services:
  `ContractorUnitService.get_contractor_root_unit_bindings(...)`
  `ContractorUnitService.bind_user_to_root_units(...)`
  `ContractorUnitService.filter_contractor_user_ids_for_request_owner(...)`
  `ContractorUnitService.can_contractor_access_request_owner(...)`
- Frontend contract surface:
  contractor/user actions include `can_manage_contractor_unit_bindings`

### 3. Contracts
- Root-unit bindings use real `units` / `unit_members` data only. Scope means the selected root unit plus its full subtree.
- `GET /api/v1/contractors/{id}/root-units` response includes:
  `contractor_user_id: string`
  `can_manage: boolean`
  `items: [{ unit_id, unit_name, is_bound, can_manage }]`
- `PUT /api/v1/contractors/{id}/root-units` request body includes:
  `root_unit_ids: number[]`
- Backend action flags must expose `can_manage_contractor_unit_bindings` for contractor rows/cards so the frontend can render the checkbox section without inventing its own permission logic.
- Contractor-visible request lists, contractor request view/file access, outbound notifications, and offer-related contractor fanout must filter recipients by the contractor's bound root-unit scope.
- Manual contractor creation must check duplicates by full name, INN, company name, or email before creating a new user.
- If a duplicate contractor already exists in another root-unit scope, the system must add the creator's current root-unit binding instead of creating a second contractor.
- If no duplicate exists, the newly created manual contractor must be bound to the creator's current root unit immediately.

### 4. Validation & Error Matrix
- Caller lacks contractor-management rights -> root-unit binding endpoints stay forbidden.
- Caller is `admin` / `superadmin` -> binding endpoints allowed even without explicit contractor delegation token role.
- Reading bindings (`GET /root-units`) is allowed for callers who can read the contractor profile (`contractors.profile.read`) OR manage bindings (`can_manage_contractor_unit_bindings`); admins manage status without `contractors.profile.read`, so the read gate must not require profile-read alone.
- Contractor is not bound to the request owner's root-unit subtree -> request list entry, request details, file access, email/TG/MAX fanout, and status-event notifications must exclude that contractor.
- Additional email maps to an existing contractor account outside visible root-unit scope -> skip recipient.
- Additional email maps to an existing contractor account inside visible root-unit scope -> allow invited-contractor email content.
- Duplicate lookup returns more than one contractor -> reject creation with a conflict instead of guessing which record to reuse.

### 5. Good/Base/Bad Cases
- Good: a contractor bound to root unit `Finance` sees only requests created inside `Finance` and its descendants, and receives only matching notifications.
- Base: an admin opens contractor details, toggles root-unit checkboxes, saves bindings, and the same contractor's visibility updates without any frontend-only permission override.
- Bad: a contractor with no binding to the request owner's subtree still receives `request.created` email/TG/MAX notifications because the service reused a global contractor list.

### 6. Tests Required
- Backend unit: manual contractor creation reuses an existing contractor and binds it to the creator's root unit.
- Backend unit/integration: request-created notification fanout excludes contractors outside the bound root-unit subtree.
- Backend integration: additional email mapped to an economist-created contractor account is still filtered by root-unit scope.
- Frontend unit: contractor details dialog loads root-unit bindings, toggles checkboxes, and submits `root_unit_ids`.
- Frontend type/DTO checks: contractor actions mapping keeps `manage_contractor_unit_bindings` aligned with backend payloads.

### 7. Wrong vs Correct
#### Wrong
- Treat contractor visibility as global after approval and only hide explicitly blocked contractors, while the root-unit checkbox state affects UI labels only.

#### Correct
- Treat contractor root-unit bindings as an enforcement input across request visibility, file access, and notification fanout, and expose only a thin action-driven checkbox UI on the frontend.
