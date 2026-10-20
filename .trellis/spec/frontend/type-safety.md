# Type Safety

Frontend types should stay aligned with backend DTOs and API contracts.

## Rules

- Treat backend response shapes as the source of truth.
- Prefer explicit API response types over loose `any`-style typing.
- Keep the wire-format shape aligned with what the backend actually returns, even if it uses snake_case field names.
- Map data at the boundary instead of inventing parallel DTOs in the UI.

## Current Patterns

- API response helpers usually live in `web/src/shared/api/<area>/`.
- Feature hooks consume those helpers and turn the raw response into view state.
- Shared domain types live in `web/src/entities/*/model`.

## Do

- Reuse shared request/response types when they already exist.
- Keep role and permission constants in one shared place.
- Keep literal unions for statuses and route values narrow and consistent.

## Don't

- Do not create a second type definition for the same backend payload in another package.
- Do not widen a known status or permission code just to make TypeScript quieter.

## Scenario: Request Details Plan Labels Use `plan_name`

### 1. Scope / Trigger
- Trigger: the request details screen needs to render the assigned plan in read-only mode before or without loading plan selector options.

### 2. Signatures
- Backend API:
  `GET /api/v1/requests/{request_id}`
- Frontend API helper:
  `getRequestDetails(requestId: string): Promise<RequestDetails>`

### 3. Contracts
- Request details response keeps both plan fields:
  `id_plan: number | null`
  `plan_name: string | null`
- `id_plan` is the stable identifier for edit flows and PATCH payloads.
- `plan_name` is the display label for read-only request details when the selected plan option is not yet present in `getPlanOptions()`.
- Frontend boundary mapping in `web/src/shared/api/requests/getRequestDetails.ts` must preserve `plan_name` instead of deriving labels inside the view.

### 4. Validation & Error Matrix
- `id_plan=null` and `plan_name=null` -> UI shows "Без плана".
- `id_plan` present and matching option exists in `getPlanOptions()` -> UI shows option label (`plan_name + user_name`).
- `id_plan` present and options are still empty/unavailable, but response includes `plan_name` -> UI shows `plan_name`, not `План #<id>`.
- `id_plan` present and backend omitted `plan_name` -> treat as contract gap and expect a targeted backend/frontend fix instead of inventing a new parallel label source.

### 5. Good/Base/Bad Cases
- Good: request details returns `id_plan=3`, `plan_name="План закупок"`, and the read-only field shows `План закупок` immediately.
- Base: once plan options load, the same request may render the richer selector label with owner context.
- Bad: rely on `id_plan` alone in the read-only UI and fall back to `План #3`, which leaks an internal identifier instead of the business name.

### 6. Tests Required
- Backend contract/integration: `/api/v1/requests/{id}` response includes `plan_name` when `id_plan` is assigned.
- Frontend unit: `RequestDetailsView` shows `plan_name` when plan options are unavailable.
- Frontend unit: role navigation config for `/requests/:id` keeps the normal sidebar tabs and still exposes `backAction`.

### 7. Wrong vs Correct
#### Wrong
- Treat `id_plan` as enough information for read-only rendering and reconstruct a fallback label like `План #<id>` in the component.

#### Correct
- Keep `id_plan` for mutations and selection state, but pass `plan_name` through the request details API contract and use it as the read-only display source until richer option metadata is available.

## Scenario: Units Hierarchy Uses Department Roots And Graph Editor DTOs

### 1. Scope / Trigger
- Trigger: the hierarchy page now treats root nodes as departments, opens second-level units in a graph editor, and supports move/delete flows that change parent links.

### 2. Signatures
- Backend API:
  `GET /api/v1/units/tree`
  `POST /api/v1/units`
  `PATCH /api/v1/units/{unit_id}`
  `DELETE /api/v1/units/{unit_id}?confirm_reassign=<bool>`
  `GET /api/v1/units/available-users`
- Frontend API helpers:
  `getUnitsTree(): Promise<UnitNode[]>`
  `createUnit(payload)`
  `updateUnit(unitId, payload)`
  `deleteUnit(unitId, confirmReassign)`

### 3. Contracts
- `UnitNode` remains the writable DTO sourced from `/units/tree`; root nodes (`id_parent=null`) are departments and nested children are graph nodes.
- `UnitNode.actions` must normalize backend action flags exactly:
  `can_create_child -> canCreateChild`
  `can_update -> canUpdate`
  `can_delete -> canDelete`
  `can_manage_members -> canManageMembers`
- Update payloads may send:
  `name?: string`
  `id_parent?: number`
- Delete flows use the query contract `confirm_reassign` rather than a request body.
- Frontend delete preview is local UI state only. Do not add preview-only fields to the backend DTO or mutate the server payload shape to support the dialog.
- Available-user results are staff-only candidates for unit assignment; if contractors appear there, treat it as a backend contract bug instead of widening the frontend types.

### 4. Validation & Error Matrix
- Backend starts omitting `can_delete` while the UI still expects it -> default `canDelete` to `false`.
- Backend changes `id_parent` or action field names -> update `web/src/shared/api/units/types.ts` boundary mapping first; do not patch around it in the page hook.
- Delete requires reassignment confirmation -> call `deleteUnit(unitId, true)` and keep the preview local; do not invent a second endpoint.
- Move flow edits parent link -> send `id_parent`; do not create a parallel `parentUnitId` wire contract.

### 5. Good/Base/Bad Cases
- Good: the page loads `/units/tree`, shows department roots, opens a second-level unit graph, and moves a node by PATCHing only `id_parent`.
- Base: a simple rename updates only `name` and keeps the existing parent unchanged.
- Bad: normalize the backend response into a second "graph node" DTO with copied action names and separate parent semantics, then keep that parallel structure drifting away from the API.

### 6. Tests Required
- Frontend unit: `useUnitHierarchyPage` keeps department roots separate from the selected graph-editor subtree.
- Frontend unit: delete dialog computes `willReassign` from members/children and passes `confirm_reassign` through `deleteUnit(...)`.
- Frontend unit/view: action buttons hide or disable from normalized `canDelete` / `canManageMembers`, not from role-only checks.
- Backend integration: `/api/v1/units/{id}` PATCH accepts `id_parent` and DELETE accepts `confirm_reassign`.

### 7. Wrong vs Correct
#### Wrong
- Invent new frontend-only wire fields such as `parentUnitId` or `deleteMode`, or mix local preview data into the API DTO.

#### Correct
- Keep the backend unit payload as the source of truth, map snake_case fields once at the API boundary, and let the page hook layer compose graph-editor state from that normalized DTO.
