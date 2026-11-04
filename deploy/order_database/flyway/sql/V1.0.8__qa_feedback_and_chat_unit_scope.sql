-- Complete the IAM provider contract for schema sources predating the IAM patch.
ALTER TABLE user_auth_accounts DROP CONSTRAINT IF EXISTS user_auth_accounts_provider_chk;
ALTER TABLE user_auth_accounts ADD CONSTRAINT user_auth_accounts_provider_chk
  CHECK (provider IN ('iam', 'keycloak', 'telegram', 'max', 'phone', 'email'));
CREATE UNIQUE INDEX IF NOT EXISTS ux_user_auth_accounts_user_provider ON user_auth_accounts (id_user, provider);

-- Preserve unknown historical author/time; defaults apply only to future rows.
ALTER TABLE feed_back ADD COLUMN IF NOT EXISTS author_user_id TEXT REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE feed_back ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ;
ALTER TABLE feed_back ALTER COLUMN created_at SET DEFAULT now();
CREATE INDEX IF NOT EXISTS idx_feedback_created ON feed_back (created_at DESC NULLS LAST, id DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_author_created ON feed_back (author_user_id, created_at DESC NULLS LAST, id DESC);

-- Match UnitHierarchyService._can_manage; legacy users.id_parent is not business scope.
CREATE OR REPLACE FUNCTION sync_chat_participants(
  p_chat_id BIGINT, p_request_id TEXT, p_contractor_user_id TEXT, p_joined_at TIMESTAMP
) RETURNS void AS $$
DECLARE
  v_owner TEXT;
  v_owner_role SMALLINT;
  v_desired TEXT[];
BEGIN
  SELECT r.id_user, u.id_role INTO v_owner, v_owner_role
    FROM requests r JOIN users u ON u.id = r.id_user WHERE r.id = p_request_id;
  IF v_owner IS NULL THEN RETURN; END IF;

  WITH RECURSIVE unit_path(unit_id, depth, visited) AS (
    SELECT um.id_unit::BIGINT, 0, ARRAY[um.id_unit::BIGINT]
      FROM unit_members um JOIN units u ON u.id = um.id_unit AND u.is_active
      WHERE um.id_user = v_owner AND um.is_active
    UNION ALL
    SELECT parent.id::BIGINT, p.depth + 1, p.visited || parent.id::BIGINT
      FROM unit_path p JOIN units child ON child.id = p.unit_id
      JOIN units parent ON parent.id = child.id_parent AND parent.is_active
      WHERE NOT (parent.id::BIGINT = ANY(p.visited))
  ), managers AS (
    SELECT manager.id FROM unit_path p
      JOIN unit_members um ON um.id_unit = p.unit_id AND um.is_active
      JOIN users manager ON manager.id = um.id_user AND manager.status = 'active'
      WHERE manager.id <> v_owner
        AND (manager.id_role = 1
          OR (manager.id_role = 4 AND v_owner_role IN (4,5,6,7))
          OR (manager.id_role IN (5,6) AND v_owner_role IN (6,7)))
        AND (p.depth > 0 OR
          CASE manager.id_role WHEN 4 THEN 4 WHEN 5 THEN 3 WHEN 6 THEN 2 WHEN 7 THEN 1 ELSE 0 END >
          CASE v_owner_role WHEN 4 THEN 4 WHEN 5 THEN 3 WHEN 6 THEN 2 WHEN 7 THEN 1 ELSE 0 END)
  ), desired AS (
    SELECT v_owner AS id_user
    UNION SELECT p_contractor_user_id WHERE p_contractor_user_id IS NOT NULL
    UNION SELECT id FROM managers
  ) SELECT array_agg(id_user) INTO v_desired FROM desired;

  INSERT INTO chat_participants (id_chat, id_user, joined_at, left_at, last_read_at, is_muted, is_archived)
    SELECT p_chat_id, id_user, p_joined_at, NULL, p_joined_at,
      id_user <> v_owner AND id_user IS DISTINCT FROM p_contractor_user_id, FALSE
      FROM unnest(v_desired) AS desired_user(id_user)
      WHERE id_user IS NOT NULL
    ON CONFLICT (id_chat, id_user) DO UPDATE SET left_at = NULL;
  UPDATE chat_participants SET left_at = p_joined_at
    WHERE id_chat = p_chat_id AND left_at IS NULL AND NOT (id_user = ANY(v_desired));
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE item RECORD;
BEGIN
  FOR item IN SELECT c.id, o.id_request, o.id_user FROM chats c JOIN offers o ON o.id = c.id
  LOOP
    PERFORM sync_chat_participants(item.id, item.id_request, item.id_user, LOCALTIMESTAMP);
  END LOOP;
END;
$$;
