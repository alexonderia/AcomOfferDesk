DO $$
DECLARE
  existing_constraint_name TEXT;
BEGIN
  SELECT constraint_definition.conname
  INTO existing_constraint_name
  FROM pg_catalog.pg_constraint AS constraint_definition
  WHERE constraint_definition.contype = 'f'
    AND constraint_definition.conrelid = 'auth_audit_log'::regclass
    AND constraint_definition.confrelid = 'auth_sessions'::regclass;

  IF existing_constraint_name IS NULL THEN
    RAISE EXCEPTION
      'Foreign key from auth_audit_log to auth_sessions was not found';
  END IF;

  EXECUTE format(
    'ALTER TABLE auth_audit_log DROP CONSTRAINT %I',
    existing_constraint_name
  );
END
$$;

ALTER TABLE auth_audit_log
  ALTER COLUMN session_id DROP NOT NULL,
  ADD CONSTRAINT auth_audit_log_session_id_fkey
    FOREIGN KEY (session_id)
    REFERENCES auth_sessions(id)
    ON DELETE SET NULL;
