# Permissions And Roles

This file captures the current permission model in the backend.

## Source Of Truth

- IAM `roles`, `permissions`, and `role_permissions` are the runtime source of role membership and permission grants.
- `backend/app/domain/permissions.py` defines the Acom permission vocabulary and seed matrix contract synchronized into IAM; it is also the strict allowlist used while validating IAM token claims.
- `backend/app/domain/auth_context.py` defines the provider-neutral authenticated-user shape populated from a verified IAM token and an active local IAM binding.
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

These IDs classify Acom business users and support UI/domain behavior; they do not
produce `CurrentUser.permissions`. Effective functional permissions come only from
the verified IAM token.

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

- IAM token permissions are authoritative for coarse application authorization after strict local JWT validation.
- Acom remains authoritative for unit scope, local user/business status, and per-resource action decisions.
- Frontend `role_id` checks are UX hints only.
- Backend `actions` arrays/objects are the real per-resource control surface.
- If a permission changes, update:
  - the backend permission map
  - the backend access checks
  - the frontend guards and menus
- Role/status administration synchronizes IAM before the local transaction is declared successful; it never synchronizes or falls back to another provider.

## Practical Rules

- Prefer `has_permission(...)` or the existing policy helpers instead of string-comparing roles directly.
- Use IAM permissions for functional access and then apply Acom unit/domain/resource scope; never calculate permissions from `users.id_role`.
- `department.*` permissions extend the normal permission matrix and are still constrained by Acom unit/resource policies.
- `delegation.*` strings are legacy Acom API/UI compatibility codes only. Never seed them as IAM roles or treat them as effective permissions.
- Do not add a parallel permission system in the frontend.

## Scenario: Request-Scoped Eligible Owners

The owner-picker is intentionally request-scoped. `GET
/api/v1/requests/{request_id}/eligible-owners` returns only active Lead
Economists and Economists to whom the caller can assign that exact request.
The service applies the same permission, current-owner, hierarchy, and unit
subtree checks used by the owner-change mutation, so an individual
`requests.owner.change` grant does not require the unrelated global
`users.read` permission.

The frontend must request the list separately for every editable request and
must use the returned options only for that request. The old global
`/users/request-economists` endpoint must not be restored: it could reveal
staff outside the request-specific management scope. The owner-change mutation
still performs its own authorization; an options list is never authorization
proof.

## Scenario: IAM Individual Permission Grants

### 1. Scope / Trigger
- Trigger: an account needs additional functional permissions without changing its IAM role or the shared role-permission matrix.

### 2. Signatures
- IAM DB: `account_permission_grants(account_id UUID, permission_id BIGINT, granted_at TIMESTAMPTZ)` with composite primary key `(account_id, permission_id)` and cascading foreign keys to `accounts` and `permissions`.
- IAM API: `GET /internal/accounts/{account_id}/permissions`.
- IAM API: `PUT /internal/accounts/{account_id}/permission-grants` with body `{"permissions": ["requests.update"]}`.
- IAM service result: `permissions_from_role`, `individually_granted_permissions`, and `effective_permissions` are sorted unique permission-name lists.

### 3. Contracts
- Effective permissions are `role_permissions UNION account_permission_grants`; individual grants can only add permissions and never deny or mask role permissions.
- The access JWT `permissions` claim contains the effective set. Login and the existing refresh flow recalculate that set from current IAM data.
- PUT fully replaces only the account's individual grants. It must not update `accounts.role_id` or `role_permissions`.
- IAM is the storage source of truth for individual grants. Acom keeps unit hierarchy and resource/business authorization but does not persist a duplicate grants table.
- A changed grant set writes `account.permissions.updated` to `auth_audit_log` with `details.added` and `details.removed`. Internal service operations may have a null `session_id` because they are not necessarily initiated by an IAM browser session.

### 4. Validation & Error Matrix
- unknown account -> `404 Not Found`.
- inactive account role -> `403 Forbidden` when reading or replacing its permission set.
- unknown or inactive requested permission -> `409 Conflict`; preserve the existing grant set atomically.
- repeated PUT with the same set -> `200 OK`, no duplicate grant rows, and no duplicate change-audit event.
- duplicate names in the request -> normalize to one grant and one effective permission.

### 5. Good/Base/Bad Cases
- Good: an economist keeps `requests.read` and `offers.read` from the role and receives `requests.update` individually; the JWT contains all three values once.
- Base: PUT with an empty list removes individual grants while all role permissions remain effective.
- Bad: removing an individual row for a permission also present in the role removes the effective permission, mutates `role_permissions`, or creates a DENY record.

### 6. Tests Required
- IAM schema test asserts the composite key, `BIGINT` permission ID, and cascading foreign keys.
- IAM service tests assert union/deduplication, role preservation, removal behavior, unknown/inactive atomic rejection, PUT idempotency, and `added`/`removed` audit details.
- IAM auth test asserts login and refresh JWTs contain the current effective set.
- IAM API test asserts service authentication and the three-list GET/PUT response contract.

### 7. Wrong vs Correct
#### Wrong
- Store individual permissions in Acom, copy permissions, introduce delegation roles, or infer that a missing grant denies a role permission.

#### Correct
- Store additive account-to-permission rows only in IAM, calculate a unique union for JWTs, and leave unit/resource enforcement in Acom.

## Scenario: Acom Delegation UI Backed By IAM Grants

### 1. Scope / Trigger
- Trigger: the existing department or contractor delegation UI reads or changes an account's additive functional IAM access.

### 2. Signatures
- Acom API compatibility surface:
  `GET|PUT /api/v1/users/{user_id}/delegations/department`
  `GET|PUT /api/v1/users/{user_id}/delegations/contractors`
- PUT body: `{"access_codes": ["delegation.department.requests.update"]}`.
- Access response fields: `enabled`, `granted_via_role`, and `granted_individually` in addition to the existing code/label fields.
- Account resolution: active `user_auth_accounts(provider='iam')`, where `external_subject_id = IAM accounts.id`.

### 3. Contracts
- GET obtains `permissions_from_role`, `individually_granted_permissions`, and `effective_permissions` from IAM; Acom and the frontend must not recalculate the effective functional set.
- The frontend checkbox reflects and submits only `granted_individually`. `enabled` remains true when the same permission is supplied by the role.
- Acom translates compatibility `delegation.*` access codes to atomic permission names before calling IAM.
- Each PUT replaces only the endpoint's managed subset. It preserves individual IAM grants owned by the other delegation family or another feature.
- PUT never changes IAM `role_permissions`, and Acom never stores grants in its own tables.
- Unit hierarchy, object scope, and domain/business policies remain enforced by existing Acom services after the IAM functional-permission check.

### 4. Validation & Error Matrix
- inactive or missing IAM binding -> GET returns the access catalog with a warning; PUT returns `409 Conflict`.
- unknown compatibility access code -> `409 Conflict`, with no IAM write.
- IAM account absent -> reject the mutation; do not synthesize a functional identity from the Acom role column.
- unchanged managed grant set -> return success without a duplicate IAM PUT.

### 5. Good/Base/Bad Cases
- Good: a role-provided permission is also granted individually; unchecking it removes only the individual row, while `enabled` stays true.
- Base: an individual-only permission is checked, saved through Acom, appears in IAM effective permissions, and disappears after unchecking.
- Bad: submit all effective permissions as individual grants, overwrite unrelated account grants, mutate role permissions, or call another identity provider at runtime.

### 6. Tests Required
- Backend unit: role-only, individual-only, combined, and absent access states map to the response flags.
- Backend unit: managed-subset replacement preserves unrelated grants and repeated saves skip duplicate PUTs.
- Backend unit: department/unit/domain scope decisions remain unchanged and active application imports contain no legacy identity-provider runtime modules.
- IAM client unit: exact GET/PUT paths, internal-service authentication header, and atomic permission payload.
- Frontend unit: checkbox changes only `grantedIndividually`, preserves role-provided `enabled`, and submits only individual access codes.

### 7. Wrong vs Correct
#### Wrong
- Derive effective permissions in React, save effective permissions into Acom, or replace the complete IAM individual-grant set with one UI section's selection.

#### Correct
- Render the three IAM source states, submit only the individual selection, merge the managed subset with existing IAM grants in Acom, and keep scope enforcement in the existing domain services.

## Units Hierarchy Contract

- `units.read` gates both the actual units tree and the recommended hierarchy tree derived from `users.id_parent`.
- `units.create`, `units.update`, and `units.members.manage` apply only to real `units` / `unit_members` mutations.
- The recommended hierarchy is a read-only helper source built from the current user management chain and must not be treated as a second writable unit model.
- Writable unit trees use `department -> nested units` semantics: root nodes are departments, and every deeper node is a regular unit regardless of whether the business calls it a module, project, or team.
- Contractor accounts do not participate in unit-member assignment through the hierarchy editor; their access stays rooted in department/root-unit bindings.

## Scenario: Department Roots, Nested Units, And Unit-Chain Management Scope

### 1. Scope / Trigger
- Trigger: the hierarchy editor switched from a shallow department/module layout to department roots with unlimited nested units and graph-style mutations.

### 2. Signatures
- Backend APIs:
  `GET /api/v1/units/tree`
  `POST /api/v1/units`
  `PATCH /api/v1/units/{unit_id}`
  `DELETE /api/v1/units/{unit_id}?confirm_reassign=<bool>`
  `GET /api/v1/units/available-users`
  `POST /api/v1/units/{unit_id}/members`
  `DELETE /api/v1/units/{unit_id}/members/{user_id}`
- Backend services:
  `UnitService.update_unit(..., name: str | None = None, id_parent: int | None = None)`
  `UnitService.delete_unit(..., confirm_reassign: bool = False)`
  `DepartmentScopeService.resolve_descendant_unit_scope_owner_ids_for_user(...)`
  `StaffAccessScopeService.resolve_unit_management_owner_ids(...)`

### 3. Contracts
- Root `units` rows (`id_parent is null`) are departments. They own staff membership and contractor scope at the department level.
- Any non-root `units` row is a nested unit. Depth is unlimited while the subtree stays under the same root department.
- `PATCH /api/v1/units/{unit_id}` may rename a unit and/or move it by changing `id_parent`, but cross-department moves are forbidden.
- `DELETE /api/v1/units/{unit_id}` soft-deletes the unit. For non-root units:
  - direct members move to the parent unit;
  - child units are reparented to the parent unit;
  - `confirm_reassign=true` is required whenever that delete would change staff placement or child-parent links.
- Root departments can be deleted only when they have no active child units and no direct members.
- Hierarchy member assignment is for internal staff only. `available-users` and `add_member` must exclude/reject contractors so contractors stay attached through department/root-unit bindings instead of nested unit memberships.
- Request visibility, request-owner management, and employee reassignment scope must include both:
  - the classic `users.id_parent` manager chain;
  - the ancestor chain implied by the user's current unit subtree.

### 4. Validation & Error Matrix
- rename/create with duplicate sibling name -> `409 Conflict`
- move nested unit to another root department -> `409 Conflict`
- move unit into itself or its descendant subtree -> `409 Conflict`
- delete non-root unit with direct members or children and `confirm_reassign=false` -> `409 Conflict`
- delete root department with any active structure -> `409 Conflict`
- assign contractor through unit-members endpoints -> `409 Conflict`
- user lacks units mutation rights -> keep `403`; do not rely on frontend hiding alone

### 5. Good/Base/Bad Cases
- Good: an admin opens a department, drills into a second-level unit, creates a child node, and later deletes the parent node with confirmation; staff move to the parent department and child nodes stay connected under the new parent.
- Base: a unit with no members and no children deletes immediately without a reassignment warning.
- Bad: keep a parallel "contractor inside nested unit" rule, or limit manager visibility only to `users.id_parent` while ignoring the unit chain above the employee.

### 6. Tests Required
- Backend unit: moving a unit within the same department updates `id_parent` and blocks cross-department/self-subtree moves.
- Backend unit: deleting a nested unit with confirmation reassigns direct members to the parent and reparents child units.
- Backend unit: descendant unit scope grants management even when the target user is not a direct `users.id_parent` descendant.
- Backend integration: `DELETE /api/v1/units/{id}` with `confirm_reassign=true` returns `204` and persists the reassignment behavior.
- Frontend unit: hierarchy page keeps `canDelete` / delete-preview wiring aligned with backend `can_delete` and `confirm_reassign`.

### 7. Wrong vs Correct
#### Wrong
- Treat the hierarchy page as a shallow department/module tree, allow contractor assignment through unit memberships, and base management scope only on `users.id_parent`.

#### Correct
- Treat root units as departments, allow unlimited nested units under the same root, keep contractors on department/root-unit bindings, and extend management scope through both the user hierarchy and the unit subtree chain.

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
- `ContractorUnitService` is organizational-scope-only: it calculates effective root units and their intersections, but does not inspect Request lifecycle, assignment state, or the request owner's role. `RequestPolicy.is_contractor_request_lifecycle_eligible(...)` denies contractor discovery while the current owner is an Operator; this is a negative lifecycle invariant, not a whitelist of publishable roles.
- Manual contractor creation must check duplicates by full name, INN, company name, or email before creating a new user.
- If a duplicate contractor already exists in another root-unit scope, the system must add the creator's effective root-unit binding instead of creating a second contractor.
- If no duplicate exists, the newly created manual contractor must be bound to the creator's effective root-unit scope immediately.

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
- Backend unit: manual contractor creation reuses an existing contractor and binds it to the creator's effective root-unit scope.
- Backend unit/integration: request-created notification fanout excludes contractors outside the bound root-unit subtree.
- Backend integration: additional email mapped to an economist-created contractor account is still filtered by root-unit scope.
- Backend integration: an Operator-owned request is hidden from a same-root Contractor in the list, detail, create-offer and request-file paths; after the normal owner-assignment action to a non-Operator, normal root-scope and hidden checks decide access.
- Frontend unit: contractor details dialog loads root-unit bindings, toggles checkboxes, and submits `root_unit_ids`.
- Frontend type/DTO checks: contractor actions mapping keeps `manage_contractor_unit_bindings` aligned with backend payloads.

### 7. Wrong vs Correct
#### Wrong
- Treat contractor visibility as global after approval and only hide explicitly blocked contractors, while the root-unit checkbox state affects UI labels only.

#### Correct
- Treat contractor root-unit bindings as an enforcement input across request visibility, file access, and notification fanout, and expose only a thin action-driven checkbox UI on the frontend.
