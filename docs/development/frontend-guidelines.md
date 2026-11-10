# Frontend: правила разработки

React + TypeScript + Vite + MUI; рабочий пакет — `web/`. Команды проверок: [стратегия тестирования](testing-strategy.md).

## Quality Guidelines

> Code quality standards for frontend development.

---

### Overview

Frontend work must preserve the thin-client architecture. The React app is responsible for presenting data and ergonomics, not for final business authorization.

---

### Required Patterns

- Inspect affected files before proposing edits.
- Prefer existing feature/shared structure over new ad hoc folders.
- Consume backend `permissions`, backend `actions`, and HATEOAS/action metadata for UX gating.
- Treat `role_id` as UX-only.
- Default missing action flags to disabled/hidden.
- Keep API calls in `web/src/shared/api/*` and feature hooks/models, not scattered through presentational components.
- Employee links in hierarchy views open the shared `EmployeeCardDialog` used by the employee table, including contacts, status, and the unit hierarchy. Switching employees replaces the current card; closing or switching aborts its pending requests. Contact loading requires `users.read`, and each backend endpoint enforces the target user's scope.
- Keep secrets out of frontend code and env examples.
- For background polling + push UX flows, guard against burst loops: single-flight fetches, throttled refresh triggers, and ID-based dedupe for already-shown toasts.

#### Convention: Subtle Hover Emphasis

- When highlighting an info card or details panel on hover/focus, prefer a single 1px border color change and a subtle shadow.
- Avoid stacking a second outline ring on top of the border unless the interaction needs a strong selection state.
- Keep hover emphasis visually lighter for read-only helper content, especially in dense detail layouts.

#### Convention: Viewport-Clamped Floating Panels

- Floating panels that remember size across sessions must clamp their saved and rendered dimensions to the current viewport.
- Let the outer popover/drawer container own the responsive width and height, and keep the inner panel flexible with `width: 100%`, `height: 100%`, `minWidth: 0`, and `minHeight: 0`.
- Re-clamp on window resize so the stored size never renders outside the available screen area.

#### Convention: Mobile Notification Center Sheet

- On mobile, the notification center opens as a centered full-width fullscreen sheet instead of a corner-anchored popover.
- Hide desktop resize affordances on the mobile sheet; let the viewport define the panel width and height.
- Keep the overlay/modal container responsible for centering and backdrop behavior, not the inner panel.

#### Convention: HTML Email Source Preview

- When showing a generated email preview for users, render the HTML as an actual visual preview rather than a code block.
- Keep the preview aligned with the backend template structure so the rendered content mirrors the sent email body.
- Use placeholder tokens for environment-specific values that the frontend cannot know, instead of inventing fake runtime data.

#### Convention: Mobile Breadcrumb Actions

- Breadcrumb actions may collapse to icon-only controls on narrow viewports when text would waste space.
- Keep the action accessible with an `aria-label` that matches the removed text.
- Preserve the desktop text label on larger viewports when there is room for it.

#### Convention: Mobile Bottom Navigation Slot Budget

- Keep the bottom navigation within its intended slot budget so the `more` entry remains visible on mobile.
- When a new primary destination is needed, prefer placing it inside `more` rather than pushing `more` off-screen.
- If a new item must become top-level, update the slot budget and responsive layout together with tests so the change is intentional.

#### Convention: Scoped Admin Create Dialog Roles

- When one admin create dialog is reused across employee and contractor tabs, scope the available create-role options to the active tab instead of exposing cross-tab creation paths.
- On employee tabs, contractor creation must stay out of the employee role dropdown when there is a dedicated contractor entry point elsewhere in the UI.
- If the active tab has no available create roles after scoping, hide the add action instead of opening a dialog with unrelated options.
- Superadmin is the exception to tab scoping: keep the full role list available, but move the current tab's role to the first position when it is present.

#### Convention: Recommended Hierarchy Uses Org Chart Layout

- When a read-only recommendation tree is derived from current user hierarchy, render it as an org chart with explicit parent-child connectors instead of a plain indented card list.
- Keep the recommendation chart visually separate from the editable units tree so users do not confuse guidance with the source-of-truth structure.
- Prefer a horizontally scrollable chart container over wrapping children to the next line, because wrapped branches break connector readability on dense hierarchies.
- Keep editing actions out of the recommendation chart cards; CRUD stays attached only to the real units tree.
- When the chart follows a visual reference similar to a corporate org diagram, prefer a neutral light canvas, white node cards, and thin blue connectors over saturated gradients or oversized chips.
- Prefer a restrained system-style surface: flat light canvas, white cards, standard-radius corners, and low-contrast borders over decorative gradients or showcase-style depth.
- When recommendation data has multiple roots, render each root as its own centered subtree instead of merging all roots into one shared top row with a single connector band.
- Do not show unlabeled numeric legends inside recommendation cards; if hierarchy metadata is useful, present it with explicit captions such as `Подчинённые` or `Логин`.
- For MUI connector boxes, never use numeric `width: 1` or `height: 1` when you mean a 1px line: sizing props treat `1` as percentage-based sizing, so use string pixel values such as `width: '1px'` and `height: '1px'`.

#### Convention: Combined Hierarchy Shows Per-Assignment Cards

- In the combined hierarchy, show unit affiliation directly on each duplicated employee mini-card instead of wrapping several cards into one shared unit container.
- Within one role level, place duplicated cards in module-oriented clusters so each copy stays visually near the relevant unit area.
- Highlight module-oriented clusters with subtle dashed module frames behind the cards so cross-department duplicates still read as hanging from the target module area.
- If one employee belongs to multiple units, duplicate the employee mini-card for each assignment while keeping the employee at the same role level in the reporting tree.
- If a recommended-hierarchy member has no unit assignment but still belongs to a reporting chain, keep that card inside the nearest department chain inferred from the hierarchy instead of moving it into a separate fallback column.
- Cards without a real unit assignment should stay outside module frames and show an explicit no-unit badge such as `Не определено`; placeholder vacancies may keep the empty-slot label.
- Keep visual hierarchy subtle: department containers may be slightly heavier than employee cards, but all surfaces should still feel like standard application cards rather than custom marketing panels.
- Empty combined-hierarchy slots should stay interactive: use a visible placeholder card that opens the existing assignment flow instead of introducing a new ad hoc edit path.

#### Convention: Unit Hierarchy Uses Department Overview Plus Graph Editor

- Keep root departments as the landing layer of the page. Show department-level staff/contractor summary first, then list second-level units as entry cards into deeper editing.
- Keep the overview compact and scan-friendly: prefer a searchable stack of department cards with one expanded details area over rendering every department in a fully expanded wide layout.
- Place filter/search controls in the main page toolbar and let them match department names, nested unit names, and visible member identity fields instead of adding a second frontend-only hierarchy index.
- If `canUpdate` is granted, allow unit and department renaming directly in the visible field on the page/editor surface; do not force a separate rename dialog for name-only edits.
- Keep create/manage actions attached to the relevant toolbar or card header. Do not leave standalone floating add tiles or detached action buttons between hierarchy blocks.
- Opening a second-level unit should switch into a dedicated graph-editor view for that subtree instead of expanding an arbitrarily deep accordion on the overview page.
- Keep a single hierarchy source backed by `/units/tree`; do not maintain a second frontend-only org structure that can diverge from backend membership and parent links.
- When showing a read-only hierarchy list for a unit subtree, preserve the visible nesting of child units from `/units/tree`; do not flatten the whole subtree into one people list, and do not use legacy `users.id_parent` or `id_parent_user` links to stitch that tree.
- The shared `buildPeopleTree` helper must not infer manager-subordinate links from role priority or `id_parent_user`; when a screen needs hierarchy, it should come from unit nesting, and same-unit members without unit-based structure stay peer rows.
- In unit-based staff trees, the business order is Project Manager → Lead Economist → Economist → Operator. Administrator, Superadmin, and other non-business roles remain separate peer rows and neither own business subtrees nor become their subordinates. A parent unit without a Project Manager, Lead Economist, or Economist must not attach child-unit staff to an administrative role or an Operator. This is a display rule; IAM permissions and backend access checks remain authoritative.
- If the same employee is present on a parent unit and again inside a descendant unit of that same subtree, keep only the deepest occurrence in read-only hierarchy and workload lists; do not render a second duplicate card at the parent level.
- When the admin user details page renders `Иерархия по объединениям`, fetch the real `/units/tree` and build the visible cards from that unit subtree instead of reconstructing a synthetic tree from `getUserHierarchy` relations alone; the panel should follow the same unit-driven nesting rules and root-department display shape as the main hierarchy page.
- When the responsibility dashboard offers a department filter for `Занятость штата`, keep that filter scoped to the workload block only; it must not change request tabs, request counts, or employee assignment options in neighboring dashboard sections.
- When the responsibility dashboard renders the workload hierarchy for a selected department, reuse the same unit-driven member tree shape as the hierarchy page and then decorate it with workload data; do not maintain a second independently-stitched employee tree for that panel, and do not fall back to `users.id_parent` / `id_parent_user` when the unit nesting already defines the structure.
- For employee reassignment dialogs inside the graph editor, build destination options from the root that owns the member's current unit, not from whatever overview department is currently selected elsewhere on the page.
- Each graph node should expose a local create-child affordance so users can extend the structure from the place they are editing, not through a separate global wizard.
- Keep employee assignment in the same-page details panel for the selected unit, and make unit creation the first step before assigning staff.
- Deleting a unit that affects structure should use a confirmation dialog with a preview of the post-delete hierarchy rather than a blind destructive confirm.
- Keep helper copy terse and operational: short labels, short warnings, and focused empty states instead of long explanatory text blocks.

---

### Forbidden Patterns

- Final permission decisions in frontend.
- Copying backend policy rules into React components.
- New role-only checks for protected business actions.
- Hardcoded production URLs, tokens, credentials, or environment-specific secrets.
- Temporary stubs, fake production data, or TODO-gated behavior.
- UI changes that assume DB/schema changes without an explicit backend/DB patch.

---

### Permissions Review Checklist

- [ ] Does the UI use backend-provided permissions/actions for protected controls?
- [ ] Is any `roleId` usage limited to UX routing/menu/visibility?
- [ ] Does a backend endpoint enforce the same action?
- [ ] Are disabled/hidden states safe when action metadata is missing?
- [ ] If the contract changed, were backend schemas/mappers/UI consumers reviewed together?

---

### Testing Requirements

Run the narrowest meaningful checks and report them. Typical frontend checks:

```powershell
npm --prefix web run build
```

If checks cannot be run, state why and list the residual risk.

---

### Code Review Checklist

- [ ] Thin-client boundary is preserved.
- [ ] No frontend-only authorization was introduced.
- [ ] Backend action metadata is consumed consistently.
- [ ] Components remain reusable and scoped to existing feature/shared structure.
- [ ] No secrets or temporary stubs were introduced.


## Type Safety

Frontend types should stay aligned with backend DTOs and API contracts.

### Rules

- Treat backend response shapes as the source of truth.
- Prefer explicit API response types over loose `any`-style typing.
- Keep the wire-format shape aligned with what the backend actually returns, even if it uses snake_case field names.
- Map data at the boundary instead of inventing parallel DTOs in the UI.

### Current Patterns

- API response helpers usually live in `web/src/shared/api/<area>/`.
- Feature hooks consume those helpers and turn the raw response into view state.
- Shared domain types live in `web/src/entities/*/model`.

### Do

- Reuse shared request/response types when they already exist.
- Keep role and permission constants in one shared place.
- Keep literal unions for statuses and route values narrow and consistent.

### Don't

- Do not create a second type definition for the same backend payload in another package.
- Do not widen a known status or permission code just to make TypeScript quieter.

### Scenario: Request Details Plan Labels Use `plan_name`

#### 1. Scope / Trigger
- Trigger: the request details screen needs to render the assigned plan in read-only mode before or without loading plan selector options.

#### 2. Signatures
- Backend API:
  `GET /api/v1/requests/{request_id}`
- Frontend API helper:
  `getRequestDetails(requestId: string): Promise<RequestDetails>`

#### 3. Contracts
- Request details response keeps both plan fields:
  `id_plan: number | null`
  `plan_name: string | null`
- `id_plan` is the stable identifier for edit flows and PATCH payloads.
- `plan_name` is the display label for read-only request details when the selected plan option is not yet present in `getPlanOptions()`.
- Frontend boundary mapping in `web/src/shared/api/requests/getRequestDetails.ts` must preserve `plan_name` instead of deriving labels inside the view.

#### 4. Validation & Error Matrix
- `id_plan=null` and `plan_name=null` -> UI shows "Без плана".
- `id_plan` present and matching option exists in `getPlanOptions()` -> UI shows option label (`plan_name + user_name`).
- `id_plan` present and options are still empty/unavailable, but response includes `plan_name` -> UI shows `plan_name`, not `План #<id>`.
- `id_plan` present and backend omitted `plan_name` -> treat as contract gap and expect a targeted backend/frontend fix instead of inventing a new parallel label source.

#### 5. Good/Base/Bad Cases
- Good: request details returns `id_plan=3`, `plan_name="План закупок"`, and the read-only field shows `План закупок` immediately.
- Base: once plan options load, the same request may render the richer selector label with owner context.
- Bad: rely on `id_plan` alone in the read-only UI and fall back to `План #3`, which leaks an internal identifier instead of the business name.

#### 6. Tests Required
- Backend contract/integration: `/api/v1/requests/{id}` response includes `plan_name` when `id_plan` is assigned.
- Frontend unit: `RequestDetailsView` shows `plan_name` when plan options are unavailable.
- Frontend unit: role navigation config for `/requests/:id` keeps the normal sidebar tabs and still exposes `backAction`.

#### 7. Wrong vs Correct
##### Wrong
- Treat `id_plan` as enough information for read-only rendering and reconstruct a fallback label like `План #<id>` in the component.

##### Correct
- Keep `id_plan` for mutations and selection state, but pass `plan_name` through the request details API contract and use it as the read-only display source until richer option metadata is available.

### Scenario: Units Hierarchy Uses Department Roots And Graph Editor DTOs

#### 1. Scope / Trigger
- Trigger: the hierarchy page now treats root nodes as departments, opens second-level units in a graph editor, and supports move/delete flows that change parent links.

#### 2. Signatures
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

#### 3. Contracts
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

#### 4. Validation & Error Matrix
- Backend starts omitting `can_delete` while the UI still expects it -> default `canDelete` to `false`.
- Backend changes `id_parent` or action field names -> update `web/src/shared/api/units/types.ts` boundary mapping first; do not patch around it in the page hook.
- Delete requires reassignment confirmation -> call `deleteUnit(unitId, true)` and keep the preview local; do not invent a second endpoint.
- Move flow edits parent link -> send `id_parent`; do not create a parallel `parentUnitId` wire contract.

#### 5. Good/Base/Bad Cases
- Good: the page loads `/units/tree`, shows department roots, opens a second-level unit graph, and moves a node by PATCHing only `id_parent`.
- Base: a simple rename updates only `name` and keeps the existing parent unchanged.
- Bad: normalize the backend response into a second "graph node" DTO with copied action names and separate parent semantics, then keep that parallel structure drifting away from the API.

#### 6. Tests Required
- Frontend unit: `useUnitHierarchyPage` keeps department roots separate from the selected graph-editor subtree.
- Frontend unit: delete dialog computes `willReassign` from members/children and passes `confirm_reassign` through `deleteUnit(...)`.
- Frontend unit/view: action buttons hide or disable from normalized `canDelete` / `canManageMembers`, not from role-only checks.
- Backend integration: `/api/v1/units/{id}` PATCH accepts `id_parent` and DELETE accepts `confirm_reassign`.

#### 7. Wrong vs Correct
##### Wrong
- Invent new frontend-only wire fields such as `parentUnitId` or `deleteMode`, or mix local preview data into the API DTO.

##### Correct
- Keep the backend unit payload as the source of truth, map snake_case fields once at the API boundary, and let the page hook layer compose graph-editor state from that normalized DTO.


## Directory Structure

This file documents where frontend code lives in the current repository.

### Actual Layout

```text
web/src/
  app/            App shell, providers, routes, layouts
  pages/          Page-level route components
  features/       Feature-level hooks and view blocks
  entities/       Domain entities shared across features
  shared/         API clients, UI primitives, lib helpers, auth, theme, constants
```

### Placement Rules

- `app/` owns providers, route wiring, and top-level layouts.
- `pages/` contains route-level screens and page composition.
- `features/` contains reusable use-case logic and UI blocks.
- `entities/` contains domain shapes shared by multiple features.
- `shared/api` contains endpoint groups and request helpers.
- `shared/components` and `shared/ui` contain reusable presentation components.
- `shared/lib` contains pure helpers.
- `shared/auth` and `shared/constants` contain auth and role/permission helpers.

### Concrete Patterns

- Feature logic usually lives in `features/*/model/*`.
- Feature presentation usually lives in `features/*/ui/*`.
- Route registration lives in `web/src/app/routes/AppRoutes.tsx`.
- Session bootstrap lives in `web/src/app/providers/AuthProvider.tsx`.
- Realtime support lives in `web/src/app/providers/RealtimeProvider.tsx` and `ChatRealtimeProvider.tsx`.

### Do

- Reuse the existing feature or shared component if one already covers the use case.
- Keep route pages thin and push behavior into feature hooks.
- Keep API callers in `shared/api`.

### Don't

- Do not create a duplicate API client for an existing backend endpoint.
- Do not move backend permission logic into UI components.
- Do not put large business logic directly inside page components.


## Component Guidelines

Frontend components should be presentational first and use the existing MUI-based design system.

### Rules

- Keep view components focused on rendering and user interaction.
- Move data loading and business decisions into feature hooks.
- Prefer shared components from `web/src/shared/components` or `web/src/shared/ui` before creating a new one.
- Use the current MUI theme/tokens instead of inline one-off styles when possible.
- Keep user-facing text in Russian.

### Good Fits For Components

- Form fields
- Tables
- Dialogs
- Panels
- Buttons
- Status chips and badges
- Layout wrappers

### Do

- Reuse `ValidatedTextField`, `DatePickerField`, `ActionButton`, `StatusPill`, and similar shared components when they already fit the need.
- Keep props explicit and small.
- Prefer composition over making one huge screen component do everything.

### Don't

- Do not add a new page just to render a slightly different state if the existing page can be extended.
- Do not duplicate an existing control from `shared/components` with a new name and the same behavior.
- Do not embed API mutation logic in a reusable visual component unless that component is actually the feature owner.


## Hook Guidelines

Hooks in this frontend usually orchestrate data loading, UI state, and side effects.

### Placement

- Put feature-specific hooks in `features/*/model`.
- Put app-wide runtime hooks in `app/providers`.
- Put pure reusable helpers in `shared/lib` if they do not depend on React state.

### Rules

- Keep data fetching in hooks, not in presentational components.
- Use `useAuth()` for session-aware decisions instead of reading storage directly.
- Use `useNavigate`, `useSearchParams`, and route params in the hook that owns the page behavior.
- Use refs for stable signatures or polling state when you need to avoid unnecessary rerenders.
- Keep websocket/subscription lifecycle cleanup in the same hook that creates the subscription.
- Do not duplicate polling or subscription logic across multiple hooks if the same entity can own it.

### Examples Of Current Patterns

- `useRequestsPage` owns request polling, owner selection, and edit actions.
- `useOfferWorkspace` owns workspace loading, selected offer state, file changes, and chat integration.
- `useRequestDetails` keeps route-state resolution in one place.

### Anti-Pattern

- Do not let a UI component fetch data directly when the page already has a dedicated model hook.


## State Management

The frontend uses local state and backend-owned contracts rather than a large global store.

### Current Contract

- `AuthProvider` owns `authenticating`, `authenticated`, `unauthenticated`, and `unavailable` states. It bootstraps only from the Acom BFF cookie session and performs refresh/logout through BFF endpoints.
- `RoleRoute` and `ProtectedRoute` gate navigation, but they are not the final source of authorization truth.
- Backend `permissions` determine actual access.
- Backend `actions` determine resource-level UI controls.
- `roleId` is a hint for default navigation and menu visibility.

### Runtime State Areas

- Cookie-backed session metadata lives in `app/providers/AuthProvider.tsx`; raw access and refresh tokens never enter React state.
- Realtime state lives in `RealtimeProvider` and `ChatRealtimeProvider`.
- Page-specific state lives in `features/*/model` hooks.
- UI-only local state lives in the component or hook that owns the interaction.

### Rules

- Do not introduce a duplicate global store for state that is already owned by a feature hook or provider.
- Do not compute authorization in the UI when the backend already provides the decision.
- Use backend data as the source of truth for `permissions`, `actions`, statuses, and default routes.
- Keep subscriptions and polling in the owner hook so cleanup stays local and predictable.
- Do not add a frontend token, fake session, trusted identity header, direct IAM token/refresh/logout/password call, or alternate identity-provider fallback.

### Good Practice

- Use local optimistic UI only when the feature already has a reliable refresh path.
- Reconcile optimistic updates with the backend response before declaring success.
- Prefer derived values over storing duplicate copies of the same state.


## Forms

Forms in this frontend should stay close to the page or feature that owns the interaction.

### Rules

- Use the existing shared field components when possible.
- Keep form validation close to the form logic.
- Show user-facing error text in Russian.
- Keep file inputs and other one-shot browser controls reset after use.
- Keep submit handlers in the feature hook or owning page hook.

### Shared Form Building Blocks

- `ValidatedTextField`
- `RequiredFieldLabel`
- `DatePickerField`
- `AdditionalEmailsField`
- `ActionButton`

### Good Practice

- Validate before submit.
- Mirror backend constraints where the user can reasonably be blocked earlier.
- Prefer explicit form state over implicit DOM-only behavior for complex forms.

### Don't

- Do not duplicate the same validation rules in multiple forms if one shared helper already exists.
- Do not let the form component own unrelated page state.


## Roles UI

The frontend role UI is a user-experience helper, not the source of authorization truth.

### Actual Role Constants

- `1` - `SUPERADMIN`
- `2` - `ADMIN`
- `3` - `CONTRACTOR`
- `4` - `PROJECT_MANAGER`
- `5` - `LEAD_ECONOMIST`
- `6` - `ECONOMIST`
- `7` - `OPERATOR`
- `8` - `SECURITY_OFFICER`

### UI Rules

- Use the shared role constants from `web/src/shared/constants/roles.ts`.
- Keep default path resolution in `getDefaultPathByRole`.
- Keep role guides and menu visibility aligned with backend permissions.
- Treat `RoleRoute` role checks as fallback UX only.
- `units.read` is enough to open `/admin/hierarchy` and view the hierarchy structure.
- `units.members.manage` is required for hierarchy member-management UI such as unassigned employees and reassignment actions.

### Existing Role UX

- `ECONOMIST_MANAGEMENT_ROLES` defines the set of roles that can manage economy-related areas in the current UI.
- Role guide content is rendered as Russian copy and should stay consistent with the current product language policy.

### Do

- Use permissions for actual access.
- Use role only to choose default navigation or visibility hints.

### Don't

- Do not expose a role as a secure access boundary when the backend permission model already exists.


## Notifications UI

This file documents the current notification surfaces in the frontend.

### Current Surfaces

- `NotificationBadge`
- `useSystemToasts`
- `toastFacade`
- Shared components that surface warnings or status changes inside the page

### Rules

- Display backend-generated notifications as the source of truth for in-app message state.
- Use toast-style feedback for ephemeral UI confirmations and failures.
- Keep page-level warnings local to the feature that owns them.
- Do not create a separate notification system in the UI when the backend already provides a notification model.

### Language

- Notification text shown to the user should stay fully Russian.
- Technical IDs and internal payloads should remain hidden from the user-facing layer.


## Маршруты

Каноническая регистрация маршрутов — `web/src/app/routes/AppRoutes.tsx`; не поддерживайте отдельную копию полного списка путей.
`ProtectedRoute` ждёт bootstrap сессии; анонимный/недоступный вход направляется на `/login`, отсутствие business access — на `/account`.
Вход начинается через `/api/v1/auth/login`; SPA не обменивает code и не читает JWT.
`next` разрешает только локальный путь с одним начальным `/`; внешние URL, `//` и обходы через encoded slash/backslash запрещены.
При выделении вкладки `/admin/hierarchy` проверяйте точный путь раньше общего `/admin`.
`getDefaultPathByRole` сначала учитывает permissions, затем роль как UX fallback.
Создание заявки может открываться background route поверх текущей страницы.
