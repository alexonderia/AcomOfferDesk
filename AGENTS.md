<!-- TRELLIS:START -->
# Trellis Instructions

These instructions are for AI assistants working in this project.

Use the `/trellis:start` command when starting a new session to:
- Initialize your developer identity
- Understand current project context
- Read relevant guidelines

Use `@/.trellis/` to learn:
- Development workflow (`workflow.md`)
- Project structure guidelines (`spec/`)
- Developer workspace (`workspace/`)

If you're using Codex, project-scoped helpers may also live in:
- `.agents/skills/` for reusable Trellis skills
- `.codex/agents/` for optional custom subagents

Keep this managed block so 'trellis update' can refresh the instructions.

<!-- TRELLIS:END -->

## Cursor Cloud specific instructions

### Overview

AcomOfferDesk is a Docker Compose-based platform (FastAPI backend, React/Vite frontend, Keycloak auth, PostgreSQL, RabbitMQ, MinIO). All services run as containers on a shared `project_net` Docker network.

### Running the dev stack

See `docs/environments.md` for full compose commands. The short version:

```bash
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

App is served at `http://localhost:8080` via the `gateway` container.

### Key gotchas discovered during setup

1. **External PostgreSQL required first**: The `order_database` PostgreSQL container must be running on `project_net` before starting the compose stack. It is NOT part of this repo's compose files. Start it manually:
   ```bash
   docker network create project_net 2>/dev/null
   docker run -d --name order-database-postgres --network project_net \
     -e POSTGRES_USER=devuser -e POSTGRES_PASSWORD=devpass -e POSTGRES_DB=order_database \
     -p 5432:5432 postgres:16-alpine
   ```

2. **DATABASE_URL must use `+asyncpg` driver**: The `.env.dev.example` has `postgresql://` but SQLAlchemy async requires `postgresql+asyncpg://`. Always set `DATABASE_URL=postgresql+asyncpg://...` in `.env.dev`.

3. **Keycloak init order matters**: Run `keycloak_db_prepare` BEFORE starting Keycloak for the first time. If Keycloak fails with "schema does not exist", restart it after running db_prepare.

4. **Bootstrap script BOM**: `infra/keycloak/bootstrap.sh` has a UTF-8 BOM which produces a harmless warning on line 1 — ignore it.

5. **Database schema not in this repo**: Tables are managed by Flyway in a separate `order_database` repo. For cloud agent dev, create tables from ORM models in `backend/app/models/`.

6. **ESLint config missing**: `web/.eslintrc.cjs` was removed. `npm run lint` currently fails — this is a pre-existing repo issue.

7. **Keycloak bootstrap binding**: After Keycloak bootstrap, the `superadmin` user exists in Keycloak but you must also create a matching record in the `users` table (id=`superadmin`, id_role=1, status=`active`) for the app to link the identity.

8. **Docker in this VM**: Docker daemon must be started manually (`sudo dockerd`). Socket needs `chmod 666 /var/run/docker.sock`. Uses `fuse-overlayfs` storage driver and `iptables-legacy`.

### Lint / Build / Test

| Service | Command | Notes |
|---------|---------|-------|
| Frontend lint | `cd web && npm run lint` | Currently broken (missing .eslintrc) |
| Frontend build | `cd web && npm run build` | Works (`tsc -b && vite build`) |
| Frontend dev | `cd web && npm run dev` | Vite on port 4173 |
| Backend health | `curl http://localhost:8080/health` | Via gateway |
| Full stack | See `docs/environments.md` | Docker Compose |
