# Локальная миграция IAM-аккаунтов

Только локальная разработка; не инструкция для production.

## Scenario: Local-development IAM account migration

### 1. Scope / Trigger

- Trigger: a local/dev database must permit immediate IAM login for every existing
  Acom user without changing Acom business records.
- This is a development-only bootstrap path; it is not an onboarding or production
  password workflow.

### 2. Signatures

- Command: `python -m app.scripts.provision_local_dev_iam_users --dry-run|--apply`
- Internal IAM API: `POST /internal/local-dev/accounts/{account_id}/provision`
- Acom binding: `user_auth_accounts(provider='iam', external_subject_id=<account UUID>)`.

### 3. Contracts

- The command reads existing `users` and derives IAM roles through the shared local
  role mapping. It must not write `users`, profiles, units, memberships, requests,
  offers, or historical provider bindings.
- It uses an existing IAM binding's UUID, or a deterministic UUID for a new binding,
  so retries converge on one account per Acom user.
- The internal endpoint accepts `login`, `role`, and `auth_status='active'` only; it
  derives the development password from its own account login. Acom never sends or
  stores that plaintext.
- IAM stores the credential exclusively as an Argon2id hash in
  `account_credentials`; repeated provisioning verifies the expected password before
  replacing a hash.
- The command and endpoint both require `APP_ENV` to be `development`, `dev`, or
  `local`. Any other environment must reject the operation before a write.

### 4. Validation & Error Matrix

- Unsupported local role -> user is reported as not migrated; no binding is written.
- Existing IAM binding with a non-UUID subject -> user is reported as not migrated.
- IAM subject already bound to another Acom user -> user is reported as not migrated.
- IAM/client or local binding persistence failure -> user is reported as not migrated;
  a retry reuses the deterministic account ID.
- Non-local environment -> command fails and IAM returns `403`; no development
  credentials are provisioned.

### 5. Good / Base / Bad Cases

- Good: a local user receives an active IAM account, active IAM binding, mapped role,
  and only an Argon2id password hash.
- Base: a second `--apply` reports zero created accounts and bindings, while reusing
  every account.
- Bad: run this command in production, persist `password = login` in Acom or IAM,
  delete a historical provider binding, or repair business data as a side effect.

### 6. Tests Required

- IAM: local provisioning creates an active account and verifiable Argon2id credential;
  a second call does not duplicate it; non-local environment is forbidden.
- Acom: a new binding is created once, then reused; the client payload contains no
  password; production guard rejects the command.
- Local smoke: run `--apply` twice and authenticate one migrated user through
  `/iam/authorize` and `/iam/login`.

### 7. Wrong vs Correct

#### Wrong

```python
await iam_client.provision_account(login=login, password=login, role=role)
```

#### Correct

```python
await iam_client.provision_local_development_account(
    account_id=account_id,
    login=login,
    role=role,
)
```
