# Release checklist

- [ ] Backend tests passed.
- [ ] IAM tests passed.
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
