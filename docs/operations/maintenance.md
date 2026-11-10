# Технические работы и fallback gateway

## Scenario: Gateway Maintenance Fallback And Manual Maintenance Mode

### 1. Scope / Trigger
- Trigger: any change to gateway/nginx runtime routing, compose service dependencies, or maintenance-mode behavior.

### 2. Signatures
- Compose files:
  - `docker-compose.yml`
  - `docker-compose.dev.yml`
  - `docker-compose.prod-like.yml`
  - `docker-compose.prod.yml`
  - `docker-compose.test.yml`
  - `docker-compose.maintenance.yml`
- Gateway configs:
  - `backend/nginx.conf`
  - `infra/maintenance/gateway.maintenance.conf`
  - `infra/maintenance/default.conf`
- Public routes:
  - `/`
  - `/api/*`
  - `/iam/*`
  - `/health`

### 3. Contracts
- Runtime service contract:
  - `maintenance` is a dedicated internal nginx service on `project_net`.
  - `maintenance` is never published directly with public `ports`.
  - `gateway` remains the single public entrypoint.
- Automatic fallback contract:
  - `/` falls back to the maintenance page when `web` is unavailable.
  - Browser-facing auth endpoints under `/api/v1/auth/` (`login` and `callback`) also fall back to the maintenance page when `backend` is unavailable.
  - `/api/*` returns controlled JSON `503` when `backend` is unavailable:
    `{"detail":"Система временно недоступна. Ведутся технические работы."}`
  - `/iam/*` keeps routing to the project IAM service while IAM itself is available.
  - `/health` may return `503` when backend health is unavailable in normal mode.
- Manual maintenance contract:
  - enable by adding `docker-compose.maintenance.yml`;
  - `/` and `/iam/*` return the maintenance page;
  - `/api/*` returns maintenance JSON `503`;
  - `/health` returns from the maintenance contour so gateway stays reachable.

### 4. Validation & Error Matrix
- `web` unavailable in normal mode -> `/` returns maintenance HTML, not default nginx `502`
- `backend` unavailable in normal mode -> `/api/*` returns controlled JSON `503`
- `iam` unavailable in normal mode -> `/iam/*` remains unavailable; do not silently reroute IAM to backend/web
- manual maintenance override enabled -> all user-facing web/IAM paths return maintenance HTML, API remains controlled `503`
- adding a new public service port for maintenance -> forbidden

### 5. Good/Base/Bad Cases
- Good: `gateway` starts with `maintenance`; `web` is down; `GET /` still shows the maintenance page.
- Good: `backend` is down; `GET /api/v1/auth/login?next=%2F` still shows the maintenance page instead of raw JSON.
- Base: all upstreams are healthy; routing stays `/ -> web`, `/api/* -> backend`, `/iam/* -> iam`.
- Bad: `gateway` depends on healthy `web`/`backend`, so the entrypoint never starts and users only see edge-level failure.

### 6. Tests Required
- Config: `docker compose ... config` passes for normal and maintenance override stacks.
- Syntax: nginx config test passes for `backend/nginx.conf`, `infra/maintenance/default.conf`, and `infra/maintenance/gateway.maintenance.conf`.
- Smoke:
  - stop `web` -> assert `/` returns maintenance HTML instead of raw `502`
  - stop `backend` -> assert `/api/v1/auth/login?next=%2F` returns maintenance HTML
  - stop `backend` -> assert `/api/health` returns JSON `503`
  - enable `docker-compose.maintenance.yml` -> assert `/` returns maintenance HTML and `/api/health` returns JSON `503`

### 7. Wrong vs Correct
#### Wrong
- Implement maintenance as part of `backend` or `web`, or publish a separate external maintenance port.

#### Correct
- Keep maintenance as a dedicated internal service behind `gateway`, with automatic frontend/API fallback and an explicit compose override for manual full-maintenance mode.
