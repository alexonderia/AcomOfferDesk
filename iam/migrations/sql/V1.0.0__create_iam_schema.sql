CREATE TABLE roles (
  id SMALLSERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE permissions (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE role_permissions (
  role_id SMALLINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  permission_id BIGINT NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE accounts (
  id UUID PRIMARY KEY,
  login TEXT NOT NULL UNIQUE,
  role_id SMALLINT NOT NULL REFERENCES roles(id),
  auth_status TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT accounts_auth_status_chk
    CHECK (auth_status IN ('pending', 'active', 'blocked', 'disabled'))
);

CREATE TABLE account_credentials (
  account_id UUID PRIMARY KEY REFERENCES accounts(id) ON DELETE CASCADE,
  password_hash TEXT NULL,
  password_algo TEXT NULL,
  password_changed_at TIMESTAMPTZ NULL,
  failed_login_count INTEGER NOT NULL DEFAULT 0,
  locked_until TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE auth_sessions (
  id UUID PRIMARY KEY,
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  refresh_token_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_used_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL,
  revoked_at TIMESTAMPTZ NULL,
  revoke_reason TEXT NULL,
  ip_address INET NULL,
  user_agent TEXT NULL
);

CREATE INDEX idx_auth_sessions_account_active
ON auth_sessions (account_id, revoked_at);

CREATE TABLE authorization_codes (
  id UUID PRIMARY KEY,
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  code_hash TEXT NOT NULL UNIQUE,
  pkce_challenge TEXT NOT NULL,
  pkce_method TEXT NOT NULL,
  redirect_uri TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL,
  consumed_at TIMESTAMPTZ NULL,
  CONSTRAINT authorization_codes_pkce_method_chk CHECK (pkce_method = 'S256')
);

CREATE TABLE auth_action_tokens (
  id UUID PRIMARY KEY,
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  purpose TEXT NOT NULL,
  token_hash TEXT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL,
  consumed_at TIMESTAMPTZ NULL,
  CONSTRAINT auth_action_tokens_purpose_chk
    CHECK (purpose IN ('password_setup', 'password_reset'))
);

CREATE TABLE auth_audit_log (
  id UUID PRIMARY KEY,
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE RESTRICT,
  session_id UUID NOT NULL REFERENCES auth_sessions(id) ON DELETE RESTRICT,
  event_type TEXT NOT NULL,
  success BOOLEAN NOT NULL,
  details JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_auth_audit_log_account_created
ON auth_audit_log (account_id, created_at DESC);

CREATE INDEX idx_auth_audit_log_session_created
ON auth_audit_log (session_id, created_at DESC);
