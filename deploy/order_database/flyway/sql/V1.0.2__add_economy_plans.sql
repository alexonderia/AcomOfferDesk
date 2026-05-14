-- Recreate economy plans model from scratch (table is empty by business decision).

-- 1) Drop dependent triggers/functions to avoid dependency conflicts.
DROP TRIGGER IF EXISTS requests_sync_economy_plan_facts ON requests;
DROP FUNCTION IF EXISTS trg_requests_sync_economy_plan_facts();

DROP TRIGGER IF EXISTS economy_plan_request_facts_apply_delta ON economy_plan_request_facts;
DROP FUNCTION IF EXISTS trg_economy_plan_request_facts_apply_delta();

DROP FUNCTION IF EXISTS fn_economy_plan_apply_delta_to_ancestors(BIGINT, NUMERIC(14,2));
DROP FUNCTION IF EXISTS fn_calc_request_economy(BIGINT);

DROP TRIGGER IF EXISTS economy_plans_validate_hierarchy ON economy_plans;
DROP FUNCTION IF EXISTS trg_economy_plans_validate_hierarchy();

DROP TRIGGER IF EXISTS economy_plans_timestamps ON economy_plans;
DROP FUNCTION IF EXISTS trg_economy_plans_timestamps();

-- 2) Drop FKs/columns/tables and recreate economy_plans from scratch.
ALTER TABLE requests
  DROP CONSTRAINT IF EXISTS requests_id_plan_fk;

ALTER TABLE requests
  DROP COLUMN IF EXISTS id_plan;

DROP TABLE IF EXISTS economy_plan_request_facts;
DROP TABLE IF EXISTS economy_plans;

CREATE TABLE economy_plans (
  id                        BIGSERIAL PRIMARY KEY,
  id_parent_plan            BIGINT NULL,
  name                      TEXT NOT NULL,
  id_user                   TEXT NOT NULL,
  id_parent_user_snapshot   TEXT NULL,
  period_start              DATE NOT NULL,
  period_end                DATE NULL,
  plan_amount               NUMERIC(14,2) NOT NULL,
  fact_amount               NUMERIC(14,2) NULL,
  created_at                TIMESTAMP NOT NULL DEFAULT now(),
  updated_at                TIMESTAMP NOT NULL DEFAULT now(),
  CONSTRAINT economy_plans_user_fk
    FOREIGN KEY (id_user) REFERENCES users(id) ON DELETE RESTRICT,
  CONSTRAINT economy_plans_parent_plan_fk
    FOREIGN KEY (id_parent_plan) REFERENCES economy_plans(id) ON DELETE RESTRICT,
  CONSTRAINT economy_plans_parent_user_snapshot_fk
    FOREIGN KEY (id_parent_user_snapshot) REFERENCES users(id) ON DELETE SET NULL,
  CONSTRAINT economy_plans_period_chk
    CHECK (period_end >= period_start),
  CONSTRAINT economy_plans_plan_amount_chk
    CHECK (plan_amount >= 0),
  CONSTRAINT economy_plans_fact_amount_chk
    CHECK (fact_amount IS NULL OR fact_amount >= 0),
  CONSTRAINT economy_plans_name_not_blank
    CHECK (btrim(name) <> ''),
  CONSTRAINT economy_plans_parent_self_chk
    CHECK (id_parent_plan IS NULL OR id_parent_plan <> id)
);

ALTER TABLE requests
  ADD COLUMN IF NOT EXISTS id_plan BIGINT;

ALTER TABLE requests
  ADD CONSTRAINT requests_id_plan_fk
  FOREIGN KEY (id_plan) REFERENCES economy_plans(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_requests_id_plan_status
ON requests (id_plan, status, updated_at DESC, id DESC);

CREATE INDEX IF NOT EXISTS idx_economy_plans_parent_plan
ON economy_plans (id_parent_plan);

CREATE INDEX IF NOT EXISTS idx_economy_plans_parent_user_period
ON economy_plans (id_parent_user_snapshot, period_start, period_end);

CREATE INDEX IF NOT EXISTS idx_economy_plans_user_period
ON economy_plans (id_user, period_start, period_end);

CREATE TABLE economy_plan_request_facts (
  id_request    BIGINT PRIMARY KEY,
  id_plan  BIGINT NOT NULL,
  fact_amount   NUMERIC(14,2) NOT NULL,
  is_active     BOOLEAN NOT NULL DEFAULT TRUE,
  updated_at    TIMESTAMP NOT NULL DEFAULT now(),
  CONSTRAINT economy_plan_request_facts_request_fk
    FOREIGN KEY (id_request) REFERENCES requests(id) ON DELETE CASCADE,
  CONSTRAINT economy_plan_request_facts_plan_fk
    FOREIGN KEY (id_plan) REFERENCES economy_plans(id) ON DELETE RESTRICT,
  CONSTRAINT economy_plan_request_facts_amount_chk
    CHECK (fact_amount >= 0)
);

CREATE INDEX IF NOT EXISTS idx_economy_plan_request_facts_plan_active
ON economy_plan_request_facts (id_plan, is_active);

CREATE OR REPLACE VIEW v_economy_plan_distribution AS
SELECT
  ep.id AS plan_id,
  ep.id_parent_plan,
  ep.id_user,
  ep.name,
  ep.period_start,
  ep.period_end,
  ep.plan_amount,
  COALESCE(child_agg.child_plan_amount, 0)::NUMERIC(14,2) AS allocated_to_children_amount,
  (ep.plan_amount - COALESCE(child_agg.child_plan_amount, 0))::NUMERIC(14,2) AS unallocated_amount
FROM economy_plans ep
LEFT JOIN (
  SELECT
    c.id_parent_plan,
    SUM(c.plan_amount)::NUMERIC(14,2) AS child_plan_amount
  FROM economy_plans c
  WHERE c.id_parent_plan IS NOT NULL
  GROUP BY c.id_parent_plan
) child_agg
  ON child_agg.id_parent_plan = ep.id;

-- 3) Recreate functions/triggers for hierarchy validation and fact aggregation.
CREATE OR REPLACE FUNCTION trg_economy_plans_timestamps()
RETURNS trigger AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    NEW.created_at := COALESCE(NEW.created_at, now());
    NEW.updated_at := COALESCE(NEW.updated_at, NEW.created_at);
  ELSE
    NEW.updated_at := now();
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER economy_plans_timestamps
BEFORE INSERT OR UPDATE ON economy_plans
FOR EACH ROW
EXECUTE FUNCTION trg_economy_plans_timestamps();

CREATE OR REPLACE FUNCTION trg_economy_plans_validate_hierarchy()
RETURNS trigger AS $$
DECLARE
  v_parent_period_start DATE;
  v_parent_period_end DATE;
BEGIN
  IF NEW.id_parent_plan IS NULL THEN
    RETURN NEW;
  END IF;

  IF NEW.id_parent_plan = NEW.id THEN
    RAISE EXCEPTION 'economy_plans.id_parent_plan cannot reference self for plan %', NEW.id;
  END IF;

  SELECT ep.period_start, ep.period_end
  INTO v_parent_period_start, v_parent_period_end
  FROM economy_plans ep
  WHERE ep.id = NEW.id_parent_plan;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Parent economy plan % not found', NEW.id_parent_plan;
  END IF;

  IF NEW.period_start < v_parent_period_start OR NEW.period_end > v_parent_period_end THEN
    RAISE EXCEPTION
      'Child plan period [% - %] must be within parent period [% - %]',
      NEW.period_start, NEW.period_end, v_parent_period_start, v_parent_period_end;
  END IF;

  IF NEW.id IS NOT NULL THEN
    IF EXISTS (
      WITH RECURSIVE parent_chain AS (
        SELECT ep.id, ep.id_parent_plan
        FROM economy_plans ep
        WHERE ep.id = NEW.id_parent_plan

        UNION ALL

        SELECT p.id, p.id_parent_plan
        FROM economy_plans p
        JOIN parent_chain c
          ON p.id = c.id_parent_plan
      )
      SELECT 1
      FROM parent_chain
      WHERE id = NEW.id
    ) THEN
      RAISE EXCEPTION 'Cycle detected in economy_plans hierarchy for plan %', NEW.id;
    END IF;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER economy_plans_validate_hierarchy
BEFORE INSERT OR UPDATE OF id_parent_plan, period_start, period_end ON economy_plans
FOR EACH ROW
EXECUTE FUNCTION trg_economy_plans_validate_hierarchy();

CREATE OR REPLACE FUNCTION fn_calc_request_economy(
  p_request_id BIGINT
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

CREATE OR REPLACE FUNCTION fn_economy_plan_apply_delta_to_ancestors(
  p_plan_id BIGINT,
  p_delta NUMERIC(14,2)
)
RETURNS void AS $$
BEGIN
  IF p_plan_id IS NULL OR p_delta IS NULL OR p_delta = 0 THEN
    RETURN;
  END IF;

  WITH RECURSIVE plan_chain AS (
    SELECT ep.id, ep.id_parent_plan
    FROM economy_plans ep
    WHERE ep.id = p_plan_id

    UNION ALL

    SELECT p.id, p.id_parent_plan
    FROM economy_plans p
    JOIN plan_chain c
      ON p.id = c.id_parent_plan
  )
  UPDATE economy_plans ep
  SET fact_amount = COALESCE(ep.fact_amount, 0) + p_delta,
      updated_at = now()
  WHERE ep.id IN (SELECT id FROM plan_chain);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_user_can_manage_economy_plan(
  p_actor_user_id TEXT,
  p_plan_id BIGINT
)
RETURNS BOOLEAN AS $$
DECLARE
  v_allowed BOOLEAN;
BEGIN
  WITH RECURSIVE owner_chain AS (
    SELECT u.id, u.id_parent
    FROM economy_plans ep
    JOIN users u
      ON u.id = ep.id_user
    WHERE ep.id = p_plan_id

    UNION ALL

    SELECT p.id, p.id_parent
    FROM owner_chain c
    JOIN users p
      ON p.id = c.id_parent
  )
  SELECT EXISTS (
    SELECT 1
    FROM owner_chain oc
    WHERE oc.id = p_actor_user_id
  )
  INTO v_allowed;

  RETURN COALESCE(v_allowed, FALSE);
END;
$$ LANGUAGE plpgsql STABLE;
CREATE OR REPLACE FUNCTION fn_economy_plan_rebuild_fact_amounts()
RETURNS void AS $$
BEGIN
  WITH RECURSIVE descendants AS (
    SELECT
      ep.id AS ancestor_id,
      ep.id AS descendant_id
    FROM economy_plans ep

    UNION ALL

    SELECT
      d.ancestor_id,
      ch.id AS descendant_id
    FROM descendants d
    JOIN economy_plans ch
      ON ch.id_parent_plan = d.descendant_id
  ),
  leaf_facts AS (
    SELECT
      eprf.id_plan,
      SUM(eprf.fact_amount)::NUMERIC(14,2) AS leaf_fact_amount
    FROM economy_plan_request_facts eprf
    WHERE eprf.is_active = TRUE
    GROUP BY eprf.id_plan
  ),
  agg AS (
    SELECT
      d.ancestor_id AS plan_id,
      COALESCE(SUM(lf.leaf_fact_amount), 0)::NUMERIC(14,2) AS fact_amount
    FROM descendants d
    LEFT JOIN leaf_facts lf
      ON lf.id_plan = d.descendant_id
    GROUP BY d.ancestor_id
  )
  UPDATE economy_plans ep
  SET fact_amount = a.fact_amount,
      updated_at = now()
  FROM agg a
  WHERE ep.id = a.plan_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION trg_economy_plan_request_facts_apply_delta()
RETURNS trigger AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF NEW.is_active THEN
      PERFORM fn_economy_plan_apply_delta_to_ancestors(NEW.id_plan, NEW.fact_amount);
    END IF;
    RETURN NEW;
  END IF;

  IF TG_OP = 'UPDATE' THEN
    IF OLD.is_active THEN
      PERFORM fn_economy_plan_apply_delta_to_ancestors(OLD.id_plan, -OLD.fact_amount);
    END IF;

    IF NEW.is_active THEN
      PERFORM fn_economy_plan_apply_delta_to_ancestors(NEW.id_plan, NEW.fact_amount);
    END IF;

    RETURN NEW;
  END IF;

  IF TG_OP = 'DELETE' THEN
    IF OLD.is_active THEN
      PERFORM fn_economy_plan_apply_delta_to_ancestors(OLD.id_plan, -OLD.fact_amount);
    END IF;
    RETURN OLD;
  END IF;

  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER economy_plan_request_facts_apply_delta
AFTER INSERT OR UPDATE OR DELETE ON economy_plan_request_facts
FOR EACH ROW
EXECUTE FUNCTION trg_economy_plan_request_facts_apply_delta();

CREATE OR REPLACE FUNCTION trg_economy_plans_rebuild_facts_on_change()
RETURNS trigger AS $$
BEGIN
  IF TG_OP = 'UPDATE' AND (
       NEW.id_parent_plan IS DISTINCT FROM OLD.id_parent_plan
    OR NEW.plan_amount IS DISTINCT FROM OLD.plan_amount
    OR NEW.period_start IS DISTINCT FROM OLD.period_start
    OR NEW.period_end IS DISTINCT FROM OLD.period_end
  ) THEN
    PERFORM fn_economy_plan_rebuild_fact_amounts();
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS economy_plans_rebuild_facts_on_change ON economy_plans;
CREATE TRIGGER economy_plans_rebuild_facts_on_change
AFTER UPDATE OF id_parent_plan, plan_amount, period_start, period_end ON economy_plans
FOR EACH ROW
EXECUTE FUNCTION trg_economy_plans_rebuild_facts_on_change();

CREATE OR REPLACE FUNCTION trg_requests_sync_economy_plan_facts()
RETURNS trigger AS $$
DECLARE
  v_fact NUMERIC(14,2);
BEGIN
  PERFORM pg_advisory_xact_lock(NEW.id);

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


