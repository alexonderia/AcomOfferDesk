CREATE TABLE account_permission_grants (
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  permission_id BIGINT NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
  granted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (account_id, permission_id)
);

-- Internal service operations are auditable even when they are not initiated
-- from an IAM browser session.
ALTER TABLE auth_audit_log
  ALTER COLUMN session_id DROP NOT NULL;
