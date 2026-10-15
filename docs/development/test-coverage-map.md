# Test coverage map

| Контур | Основное покрытие |
|---|---|
| IAM credentials, sessions, refresh/revoke | `iam/tests/test_authentication_flow.py`, `iam/tests/test_api_security.py` |
| Role permissions и individual grants | `iam/tests/test_permission_grants.py`, backend delegation tests |
| JWT issuer/audience/kid/expiry/unknown claims | `backend/tests/unit/test_iam_authentication_unit.py` |
| BFF callback/refresh/logout/cookies/CSRF | backend auth integration/unit tests |
| IAM binding only | `backend/tests/unit/test_iam_authentication_unit.py` |
| Unit scope и domain policies | backend service/policy/integration tests |
| Frontend session/permission guards | `web/src/**/*.test.ts(x)` |
| Browser login/logout | `web/e2e/auth.smoke.spec.ts` |
| Compose/runtime smoke | `backend/app/scripts/smoke_services.py`, `scripts/smoke-infra.*` |

Security regression должна оставаться fail-closed для invalid/expired JWT, неверных issuer/audience/kid, отсутствующего IAM binding, blocked account, revoked refresh, CSRF failures и IAM unavailability.
