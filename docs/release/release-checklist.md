# Release checklist

- [ ] Backend tests passed.
- [ ] IAM tests passed.
- [ ] File guard tests passed, including malformed XML/archive rejection.
- [ ] Frontend lint, unit tests and build passed.
- [ ] Compose config resolves for target overlay.
- [ ] `scripts/check-iam.*` passed without unexpected drift.
- [ ] `scripts/smoke-infra.*` passed on the target stand.
- [ ] Login, refresh, logout and CSRF scenarios verified.
- [ ] Invalid token/issuer/audience/kid and IAM outage fail closed.
- [ ] Role and individual grant changes take effect after session refresh.
- [ ] Unit hierarchy and request/offer visibility are preserved.
- [ ] Gateway is the only public entrypoint; internal IAM API and service ports are closed.
- [ ] No secrets or environment-local files are included in the release diff.
- [ ] Dependency advisories reviewed for production packages and build tools; remaining findings have a documented applicability assessment.
- [ ] PostgreSQL migrations validated on an isolated copy; rollout and rollback procedure checked for the target version.
- [ ] Target stand E2E verified, including no-mail accounts, concurrent request/offer mutations and WebSocket access revocation/expiry.
