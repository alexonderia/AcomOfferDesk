-- User notifications center (personal inbox).
-- This table is a user-facing event projection and does not replace business source tables.

CREATE TABLE IF NOT EXISTS user_notifications (
  id           BIGSERIAL PRIMARY KEY,
  user_id      TEXT NOT NULL,
  type         TEXT NOT NULL,
  severity     TEXT NOT NULL DEFAULT 'info',
  title        TEXT NOT NULL,
  body         TEXT NULL,
  entity_type  TEXT NULL,
  entity_id    TEXT NULL,
  link_url     TEXT NULL,
  payload      JSONB NOT NULL DEFAULT '{}'::jsonb,
  read_at      TIMESTAMP NULL,
  created_at   TIMESTAMP NOT NULL DEFAULT now(),
  CONSTRAINT user_notifications_user_fk
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT user_notifications_type_not_blank
    CHECK (btrim(type) <> ''),
  CONSTRAINT user_notifications_severity_chk
    CHECK (severity IN ('info', 'success', 'warning', 'error')),
  CONSTRAINT user_notifications_title_not_blank
    CHECK (btrim(title) <> '')
);

-- Personal feed ordered by creation date.
CREATE INDEX IF NOT EXISTS idx_user_notifications_user_created_at
ON user_notifications (user_id, created_at DESC);

-- Fast unread lookup for a user.
CREATE INDEX IF NOT EXISTS idx_user_notifications_unread_user_created_at
ON user_notifications (user_id, created_at DESC)
WHERE read_at IS NULL;

-- Optional reverse lookup from notification to business entity.
CREATE INDEX IF NOT EXISTS idx_user_notifications_entity_type_entity_id
ON user_notifications (entity_type, entity_id)
WHERE entity_type IS NOT NULL
  AND entity_id IS NOT NULL;
