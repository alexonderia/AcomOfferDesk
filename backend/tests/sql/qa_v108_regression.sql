-- Execute with psql -v ON_ERROR_STOP=1 on a migrated PostgreSQL copy.
-- All fixtures are rolled back. Existing business records are never edited.
BEGIN;
DO $$
DECLARE
  root_a BIGINT; root_b BIGINT; team_a BIGINT; team_b BIGINT;
  offer_id BIGINT; feedback_id BIGINT;
  actual TEXT[];
BEGIN
  INSERT INTO users (id, id_role, status) VALUES
    ('qa_v108_owner', 6, 'active'), ('qa_v108_contractor', 3, 'active'),
    ('qa_v108_lead_a', 5, 'active'), ('qa_v108_pm_a', 4, 'active'),
    ('qa_v108_lead_b', 5, 'active'), ('qa_v108_blocked', 5, 'inactive'),
    ('qa_v108_peer', 6, 'active'), ('qa_v108_ancestor', 6, 'active'),
    ('qa_v108_writer', 6, 'active');
  UPDATE users SET id_parent = 'qa_v108_lead_b' WHERE id = 'qa_v108_owner';
  INSERT INTO units (name) VALUES ('qa_v108_root_a') RETURNING id INTO root_a;
  INSERT INTO units (name) VALUES ('qa_v108_root_b') RETURNING id INTO root_b;
  INSERT INTO units (name, id_parent) VALUES ('qa_v108_team_a', root_a) RETURNING id INTO team_a;
  INSERT INTO units (name, id_parent) VALUES ('qa_v108_team_b', root_b) RETURNING id INTO team_b;
  INSERT INTO unit_members (id_user, id_unit) VALUES
    ('qa_v108_owner', team_a), ('qa_v108_lead_a', team_a),
    ('qa_v108_pm_a', root_a), ('qa_v108_lead_b', root_b),
    ('qa_v108_blocked', root_a), ('qa_v108_peer', team_a),
    ('qa_v108_ancestor', root_a);
  INSERT INTO requests (id, id_user, deadline_at, initial_amount)
    VALUES ('qa_v108_request', 'qa_v108_owner', LOCALTIMESTAMP + interval '1 day', 100);
  INSERT INTO offers (id_request, id_user) VALUES ('qa_v108_request', 'qa_v108_contractor') RETURNING id INTO offer_id;
  SELECT array_agg(id_user ORDER BY id_user) INTO actual FROM chat_participants
    WHERE id_chat = offer_id AND left_at IS NULL;
  IF actual IS DISTINCT FROM ARRAY['qa_v108_ancestor','qa_v108_contractor','qa_v108_lead_a','qa_v108_owner','qa_v108_pm_a'] THEN
    RAISE EXCEPTION 'Wrong participants after offer trigger: %', actual;
  END IF;
  UPDATE chat_participants SET last_read_at = '2026-01-01', is_muted = FALSE, is_archived = TRUE
    WHERE id_chat = offer_id AND id_user = 'qa_v108_lead_a';
  UPDATE unit_members SET id_unit = team_b WHERE id_user = 'qa_v108_owner';
  PERFORM sync_chat_participants(offer_id, 'qa_v108_request', 'qa_v108_contractor', LOCALTIMESTAMP);
  SELECT array_agg(id_user ORDER BY id_user) INTO actual FROM chat_participants
    WHERE id_chat = offer_id AND left_at IS NULL;
  IF actual IS DISTINCT FROM ARRAY['qa_v108_contractor','qa_v108_lead_b','qa_v108_owner'] THEN
    RAISE EXCEPTION 'Wrong participants after unit transfer: %', actual;
  END IF;
  UPDATE unit_members SET id_unit = team_a WHERE id_user = 'qa_v108_owner';
  PERFORM sync_chat_participants(offer_id, 'qa_v108_request', 'qa_v108_contractor', LOCALTIMESTAMP);
  IF NOT EXISTS (SELECT 1 FROM chat_participants WHERE id_chat = offer_id AND id_user = 'qa_v108_lead_a'
      AND left_at IS NULL AND last_read_at = '2026-01-01' AND NOT is_muted AND is_archived) THEN
    RAISE EXCEPTION 'Participant read/mute/archive state was lost';
  END IF;
  RAISE NOTICE 'PASS: chat trigger, hierarchy scope, inactive/peer exclusion, transfer and preferences';

  INSERT INTO feed_back (text, author_user_id) VALUES ('qa_v108_feedback', 'qa_v108_writer') RETURNING id INTO feedback_id;
  IF NOT EXISTS (SELECT 1 FROM feed_back WHERE id = feedback_id AND created_at IS NOT NULL) THEN
    RAISE EXCEPTION 'Feedback default timestamp missing';
  END IF;
  DELETE FROM users WHERE id = 'qa_v108_writer';
  IF NOT EXISTS (SELECT 1 FROM feed_back WHERE id = feedback_id AND author_user_id IS NULL) THEN
    RAISE EXCEPTION 'Feedback author ON DELETE SET NULL failed';
  END IF;
  RAISE NOTICE 'PASS: feedback timestamp and author foreign key';

  INSERT INTO user_auth_accounts (id_user, provider, external_subject_id)
    VALUES ('qa_v108_owner', 'iam', 'qa-v108-subject-one');
  BEGIN
    INSERT INTO user_auth_accounts (id_user, provider, external_subject_id)
      VALUES ('qa_v108_owner', 'iam', 'qa-v108-subject-two');
    RAISE EXCEPTION 'Duplicate user/provider binding accepted';
  EXCEPTION WHEN unique_violation THEN
    NULL;
  END;
  RAISE NOTICE 'PASS: IAM provider and unique binding';
END;
$$;
ROLLBACK;
