-- V1.0.5: requests.id BIGINT -> TEXT (and dependent FKs, economy views/triggers).
-- Completes order_database V1.0.4 when deploy used the truncated V1.0.4 snapshot
-- (normative_files.document_status only). Canonical full script:
-- order_database/flyway/sql/V1.0.4__normative_files_status_and_request_id_text.sql

-- Views depend on requests.id / id_request column types.
DROP VIEW IF EXISTS v_request_economy_by_responsible;
DROP VIEW IF EXISTS v_request_economy;

-- Economy sync trigger/function reference request id type and advisory lock.
DROP TRIGGER IF EXISTS requests_sync_economy_plan_facts ON requests;
DROP FUNCTION IF EXISTS trg_requests_sync_economy_plan_facts();
DROP FUNCTION IF EXISTS fn_calc_request_economy(BIGINT);

-- Chat participant sync takes request id as function argument.
DROP FUNCTION IF EXISTS sync_chat_participants(BIGINT, BIGINT, TEXT, TIMESTAMP);

-- Drop all FK constraints pointing at requests(id) (names differ per environment).
DO $$
DECLARE
  r RECORD;
BEGIN
  FOR r IN
    SELECT
      c.conname,
      format('%I.%I', n.nspname, t.relname) AS tbl
    FROM pg_constraint c
    JOIN pg_class t ON t.oid = c.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE c.confrelid = 'public.requests'::regclass
      AND c.contype = 'f'
  LOOP
    EXECUTE format(
      'ALTER TABLE %s DROP CONSTRAINT IF EXISTS %I',
      r.tbl,
      r.conname
    );
  END LOOP;
END $$;

-- Child FK columns first (still BIGINT), then PK — all use ::text to preserve values.
ALTER TABLE request_hidden_contractors
  ALTER COLUMN id_request TYPE TEXT USING id_request::text;

ALTER TABLE offers
  ALTER COLUMN id_request TYPE TEXT USING id_request::text;

ALTER TABLE request_offer_stats
  ALTER COLUMN request_id TYPE TEXT USING request_id::text;

ALTER TABLE request_files
  ALTER COLUMN id_request TYPE TEXT USING id_request::text;

ALTER TABLE economy_plan_request_facts
  ALTER COLUMN id_request TYPE TEXT USING id_request::text;

ALTER TABLE requests
  ALTER COLUMN id DROP DEFAULT;

ALTER TABLE requests
  ALTER COLUMN id TYPE TEXT USING id::text;

-- Keep serial sequence for new rows: default becomes nextval(...)::text
DO $$
DECLARE
  v_seq regclass;
BEGIN
  v_seq := pg_get_serial_sequence('requests', 'id')::regclass;
  IF v_seq IS NOT NULL THEN
    EXECUTE format(
      'ALTER TABLE requests ALTER COLUMN id SET DEFAULT (nextval(%L::regclass)::text)',
      v_seq::text
    );
  END IF;
END $$;

COMMENT ON COLUMN requests.id IS
  'Request identifier (TEXT). Legacy BIGINT values migrated via id::text; new ids from serial sequence as text.';

-- Restore FK constraints (idempotent per constraint name).
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'request_hidden_contractors_request_fk'
  ) THEN
    ALTER TABLE request_hidden_contractors
      ADD CONSTRAINT request_hidden_contractors_request_fk
      FOREIGN KEY (id_request) REFERENCES requests(id) ON DELETE CASCADE;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'offers_id_request_fkey'
  ) AND NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'offers_id_request_requests_id_fk'
  ) THEN
    ALTER TABLE offers
      ADD CONSTRAINT offers_id_request_fkey
      FOREIGN KEY (id_request) REFERENCES requests(id) ON DELETE CASCADE;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'request_offer_stats_request_id_fkey'
  ) THEN
    ALTER TABLE request_offer_stats
      ADD CONSTRAINT request_offer_stats_request_id_fkey
      FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'request_files_id_request_fkey'
  ) THEN
    ALTER TABLE request_files
      ADD CONSTRAINT request_files_id_request_fkey
      FOREIGN KEY (id_request) REFERENCES requests(id) ON DELETE CASCADE;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'economy_plan_request_facts_request_fk'
  ) THEN
    ALTER TABLE economy_plan_request_facts
      ADD CONSTRAINT economy_plan_request_facts_request_fk
      FOREIGN KEY (id_request) REFERENCES requests(id) ON DELETE CASCADE;
  END IF;
END $$;

CREATE OR REPLACE FUNCTION fn_calc_request_economy(
  p_request_id TEXT
)
RETURNS NUMERIC(14,2) AS $$
DECLARE
  v_economy NUMERIC(14,2);
BEGIN
  SELECT
    CASE
      WHEN r.final_amount IS NULL OR r.initial_amount IS NULL OR o.offer_amount IS NULL THEN NULL
      WHEN r.final_amount = r.initial_amount THEN GREATEST(o.offer_amount - r.initial_amount, 0)::NUMERIC(14,2)
      WHEN r.final_amount = o.offer_amount THEN GREATEST(r.initial_amount - o.offer_amount, 0)::NUMERIC(14,2)
      ELSE NULL
    END
  INTO v_economy
  FROM requests r
  LEFT JOIN offers o
    ON o.id = r.id_offer
   AND o.id_request = r.id
  WHERE r.id = p_request_id;

  RETURN v_economy;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sync_chat_participants(
  p_chat_id BIGINT,
  p_request_id TEXT,
  p_contractor_user_id TEXT,
  p_joined_at TIMESTAMP
)
RETURNS void AS $$
DECLARE
  v_responsible_user_id TEXT;
  v_responsible_role_id SMALLINT;
BEGIN
  SELECT r.id_user
  INTO v_responsible_user_id
  FROM requests r
  WHERE r.id = p_request_id;

  SELECT u.id_role
  INTO v_responsible_role_id
  FROM users u
  WHERE u.id = v_responsible_user_id;

  WITH RECURSIVE management_chain AS (
    SELECT
      u.id,
      u.id_parent,
      u.id_role,
      0 AS depth
    FROM users u
    WHERE u.id = v_responsible_user_id
      AND v_responsible_role_id IS DISTINCT FROM 7

    UNION ALL

    SELECT
      parent.id,
      parent.id_parent,
      parent.id_role,
      child.depth + 1
    FROM management_chain child
    JOIN users parent
      ON parent.id = child.id_parent
    WHERE child.id_role <> 5
  ),
  desired_participants AS (
    SELECT
      p_contractor_user_id AS id_user,
      FALSE AS is_muted
    WHERE p_contractor_user_id IS NOT NULL

    UNION

    SELECT
      mc.id AS id_user,
      CASE
        WHEN mc.depth = 0 THEN FALSE
        ELSE TRUE
      END AS is_muted
    FROM management_chain mc
  )
  INSERT INTO chat_participants (
    id_chat,
    id_user,
    joined_at,
    left_at,
    last_read_at,
    is_muted,
    is_archived
  )
  SELECT
    p_chat_id,
    dp.id_user,
    p_joined_at,
    NULL,
    p_joined_at,
    dp.is_muted,
    FALSE
  FROM desired_participants dp
  ON CONFLICT (id_chat, id_user) DO UPDATE
  SET is_muted = EXCLUDED.is_muted,
      left_at = NULL;

  WITH RECURSIVE management_chain AS (
    SELECT
      u.id,
      u.id_parent,
      u.id_role,
      0 AS depth
    FROM users u
    WHERE u.id = v_responsible_user_id
      AND v_responsible_role_id IS DISTINCT FROM 7

    UNION ALL

    SELECT
      parent.id,
      parent.id_parent,
      parent.id_role,
      child.depth + 1
    FROM management_chain child
    JOIN users parent
      ON parent.id = child.id_parent
    WHERE child.id_role <> 5
  ),
  desired_participants AS (
    SELECT p_contractor_user_id AS id_user
    WHERE p_contractor_user_id IS NOT NULL

    UNION

    SELECT mc.id AS id_user
    FROM management_chain mc
  )
  UPDATE chat_participants cp
  SET left_at = now()
  WHERE cp.id_chat = p_chat_id
    AND cp.left_at IS NULL
    AND NOT EXISTS (
      SELECT 1
      FROM desired_participants dp
      WHERE dp.id_user = cp.id_user
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION trg_requests_sync_economy_plan_facts()
RETURNS trigger AS $$
DECLARE
  v_fact NUMERIC(14,2);
BEGIN
  PERFORM pg_advisory_xact_lock(hashtextextended(NEW.id, 0));

  IF NEW.status = 'closed' AND NEW.id_plan IS NOT NULL THEN
    v_fact := COALESCE(fn_calc_request_economy(NEW.id), 0);

    INSERT INTO economy_plan_request_facts (
      id_request,
      id_plan,
      fact_amount,
      is_active,
      updated_at
    )
    VALUES (
      NEW.id,
      NEW.id_plan,
      v_fact,
      TRUE,
      now()
    )
    ON CONFLICT (id_request) DO UPDATE
    SET id_plan = EXCLUDED.id_plan,
        fact_amount = EXCLUDED.fact_amount,
        is_active = TRUE,
        updated_at = now();
  ELSE
    UPDATE economy_plan_request_facts
    SET is_active = FALSE,
        updated_at = now()
    WHERE id_request = NEW.id
      AND is_active = TRUE;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER requests_sync_economy_plan_facts
AFTER INSERT OR UPDATE OF status, id_plan, initial_amount, final_amount, id_offer ON requests
FOR EACH ROW
EXECUTE FUNCTION trg_requests_sync_economy_plan_facts();

CREATE OR REPLACE VIEW v_request_economy AS
SELECT
  r.id AS request_id,
  r.id_user AS responsible_user_id,
  r.initial_amount,
  r.final_amount,
  r.id_offer,
  o.offer_amount,
  CASE
    WHEN r.final_amount = r.initial_amount THEN o.offer_amount - r.initial_amount
    WHEN r.final_amount = o.offer_amount THEN r.final_amount - o.offer_amount
    ELSE NULL
  END AS economy
FROM requests r
LEFT JOIN offers o
  ON o.id = r.id_offer
 AND o.id_request = r.id;

CREATE OR REPLACE VIEW v_request_economy_by_responsible AS
SELECT
  responsible_user_id,
  COUNT(*) AS request_count_with_economy,
  SUM(economy) AS total_economy,
  AVG(economy) AS avg_economy,
  MIN(economy) AS min_economy,
  MAX(economy) AS max_economy
FROM v_request_economy
WHERE economy IS NOT NULL
GROUP BY responsible_user_id;
