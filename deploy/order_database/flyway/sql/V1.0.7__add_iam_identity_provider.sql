ALTER TABLE user_auth_accounts
  DROP CONSTRAINT IF EXISTS user_auth_accounts_provider_chk;

ALTER TABLE user_auth_accounts
  ADD CONSTRAINT user_auth_accounts_provider_chk
  CHECK (provider IN ('iam', 'keycloak', 'telegram', 'max', 'phone', 'email'));

CREATE UNIQUE INDEX IF NOT EXISTS ux_user_auth_accounts_provider_subject
ON user_auth_accounts (provider, external_subject_id);

CREATE UNIQUE INDEX IF NOT EXISTS ux_user_auth_accounts_user_provider
ON user_auth_accounts (id_user, provider);
