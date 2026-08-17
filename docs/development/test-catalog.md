# Каталог тестов

- `backend/tests/unit` — domain/service/auth unit tests;
- `backend/tests/integration` — FastAPI and cross-service contracts with fakes;
- `iam/tests` — credentials, token/session security, RBAC and grants;
- `web/src/**/*.test.ts(x)` — frontend unit/component tests;
- `web/e2e` — Playwright smoke/extended scenarios;
- `scripts/smoke-infra.*` — live environment connectivity and public perimeter;
- `scripts/check-iam.*` — IAM RBAC seed report and account reconciliation;
- `scripts/test-release.*` — aggregated release gate.

E2E login uses `/api/v1/auth/login` and prepared IAM credentials. Test scripts do not create accounts through a removed identity provider.
