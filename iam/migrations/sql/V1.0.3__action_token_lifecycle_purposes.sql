ALTER TABLE auth_action_tokens
  DROP CONSTRAINT IF EXISTS auth_action_tokens_purpose_chk;

ALTER TABLE auth_action_tokens
  ADD CONSTRAINT auth_action_tokens_purpose_chk
  CHECK (
    purpose IN (
      'password_setup',
      'password_reset',
      'verify_email',
      'first_access',
      'profile_change'
    )
  );

ALTER TABLE auth_action_tokens
  ADD COLUMN IF NOT EXISTS context JSONB NULL;

ALTER TABLE accounts
  ADD COLUMN IF NOT EXISTS required_actions JSONB NOT NULL DEFAULT '[]'::jsonb;
