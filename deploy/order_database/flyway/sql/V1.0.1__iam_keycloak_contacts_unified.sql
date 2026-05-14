-- Unified IAM/contact migration.
-- Target: schema after migrations must match current init schema.

-- ---------------------------------------------------------------------------
-- A) Safe schema extension
-- ---------------------------------------------------------------------------
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT now();

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT now();

INSERT INTO roles (id, role)
VALUES (8, 'СБ')
ON CONFLICT (id) DO UPDATE
SET role = EXCLUDED.role;

CREATE TABLE IF NOT EXISTS user_auth_accounts (
  id                    BIGSERIAL PRIMARY KEY,
  id_user               TEXT NOT NULL,
  provider              TEXT NOT NULL,
  external_subject_id   TEXT NOT NULL,
  external_username     TEXT NULL,
  external_email        TEXT NULL,
  is_active             BOOLEAN NOT NULL DEFAULT TRUE,
  linked_at             TIMESTAMP NOT NULL DEFAULT now(),
  last_login_at         TIMESTAMP NULL,
  CONSTRAINT user_auth_accounts_user_fk
    FOREIGN KEY (id_user) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT user_auth_accounts_provider_chk
    CHECK (provider IN ('keycloak', 'telegram', 'max', 'phone', 'email')),
  CONSTRAINT user_auth_accounts_subject_not_blank
    CHECK (btrim(external_subject_id) <> '')
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_user_auth_accounts_provider_subject
ON user_auth_accounts (provider, external_subject_id);

CREATE INDEX IF NOT EXISTS idx_user_auth_accounts_id_user
ON user_auth_accounts (id_user, provider);

CREATE TABLE IF NOT EXISTS user_contact_channels (
  id                        BIGSERIAL PRIMARY KEY,
  id_user                   TEXT NOT NULL,
  channel_type              TEXT NOT NULL,
  channel_value             TEXT NOT NULL,
  is_verified               BOOLEAN NOT NULL DEFAULT FALSE,
  verified_at               TIMESTAMP NULL,
  is_primary                BOOLEAN NOT NULL DEFAULT FALSE,
  is_active                 BOOLEAN NOT NULL DEFAULT TRUE,
  created_at                TIMESTAMP NOT NULL DEFAULT now(),
  updated_at                TIMESTAMP NOT NULL DEFAULT now(),
  CONSTRAINT user_contact_channels_user_fk
    FOREIGN KEY (id_user) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT user_contact_channels_type_chk
    CHECK (channel_type IN ('email', 'phone', 'telegram', 'max')),
  CONSTRAINT user_contact_channels_value_not_blank
    CHECK (btrim(channel_value) <> '')
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_user_contact_channels_type_value
ON user_contact_channels (channel_type, channel_value);

CREATE INDEX IF NOT EXISTS idx_user_contact_channels_user_type
ON user_contact_channels (id_user, channel_type);

CREATE UNIQUE INDEX IF NOT EXISTS ux_user_contact_channels_primary_per_type
ON user_contact_channels (id_user, channel_type)
WHERE is_primary = TRUE;

CREATE TABLE IF NOT EXISTS user_notification_preferences (
  id                  BIGSERIAL PRIMARY KEY,
  id_contact_channel  BIGINT NOT NULL,
  notification_type   TEXT NOT NULL,
  is_enabled          BOOLEAN NOT NULL DEFAULT TRUE,
  created_at          TIMESTAMP NOT NULL DEFAULT now(),
  updated_at          TIMESTAMP NOT NULL DEFAULT now(),
  CONSTRAINT user_notification_preferences_channel_fk
    FOREIGN KEY (id_contact_channel) REFERENCES user_contact_channels(id) ON DELETE CASCADE,
  CONSTRAINT user_notification_preferences_type_chk
    CHECK (notification_type IN ('chat', 'request', 'offer', 'system'))
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_user_notification_preferences_channel_type
ON user_notification_preferences (id_contact_channel, notification_type);

-- ---------------------------------------------------------------------------
-- B) Idempotent backfill
-- ---------------------------------------------------------------------------
DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'users'
      AND column_name = 'tg_user_id'
  ) THEN
    IF EXISTS (
      SELECT 1
      FROM information_schema.tables
      WHERE table_schema = 'public'
        AND table_name = 'tg_users'
    ) THEN
      EXECUTE $sql$
        WITH telegram_source AS (
          SELECT
            u.id AS id_user,
            btrim(u.tg_user_id::text) AS tg_value,
            COALESCE(t.status = 'approved', FALSE) AS is_verified,
            CASE
              WHEN t.status = 'approved' THEN now()
              ELSE NULL
            END AS verified_at,
            CASE
              WHEN t.status = 'disapproved' THEN FALSE
              ELSE TRUE
            END AS is_active
          FROM users u
          LEFT JOIN tg_users t
            ON t.id = u.tg_user_id
          WHERE u.tg_user_id IS NOT NULL
        )
        INSERT INTO user_contact_channels (
          id_user,
          channel_type,
          channel_value,
          is_verified,
          verified_at,
          is_primary,
          is_active,
          created_at,
          updated_at
        )
        SELECT
          s.id_user,
          'telegram',
          s.tg_value,
          s.is_verified,
          s.verified_at,
          NOT EXISTS (
            SELECT 1
            FROM user_contact_channels c
            WHERE c.id_user = s.id_user
              AND c.channel_type = 'telegram'
              AND c.is_primary = TRUE
          ) AS is_primary,
          s.is_active,
          now(),
          now()
        FROM telegram_source s
        ON CONFLICT (channel_type, channel_value) DO UPDATE
        SET
          channel_value = EXCLUDED.channel_value,
          is_verified = user_contact_channels.is_verified OR EXCLUDED.is_verified,
          verified_at = COALESCE(user_contact_channels.verified_at, EXCLUDED.verified_at),
          is_active = EXCLUDED.is_active,
          updated_at = now()
        WHERE user_contact_channels.id_user = EXCLUDED.id_user
      $sql$;

      EXECUTE $sql$
        WITH telegram_auth_source AS (
          SELECT
            u.id AS id_user,
            btrim(u.tg_user_id::text) AS external_subject_id,
            CASE
              WHEN t.status = 'disapproved' THEN FALSE
              ELSE TRUE
            END AS is_active
          FROM users u
          LEFT JOIN tg_users t
            ON t.id = u.tg_user_id
          WHERE u.tg_user_id IS NOT NULL
        )
        INSERT INTO user_auth_accounts (
          id_user,
          provider,
          external_subject_id,
          external_username,
          external_email,
          is_active,
          linked_at
        )
        SELECT
          s.id_user,
          'telegram',
          s.external_subject_id,
          NULL,
          NULL,
          s.is_active,
          now()
        FROM telegram_auth_source s
        ON CONFLICT (provider, external_subject_id) DO UPDATE
        SET
          is_active = EXCLUDED.is_active
        WHERE user_auth_accounts.id_user = EXCLUDED.id_user
      $sql$;
    ELSE
      EXECUTE $sql$
        INSERT INTO user_contact_channels (
          id_user,
          channel_type,
          channel_value,
          is_verified,
          verified_at,
          is_primary,
          is_active,
          created_at,
          updated_at
        )
        SELECT
          u.id,
          'telegram',
          btrim(u.tg_user_id::text),
          FALSE,
          NULL,
          NOT EXISTS (
            SELECT 1
            FROM user_contact_channels c
            WHERE c.id_user = u.id
              AND c.channel_type = 'telegram'
              AND c.is_primary = TRUE
          ) AS is_primary,
          TRUE,
          now(),
          now()
        FROM users u
        WHERE u.tg_user_id IS NOT NULL
        ON CONFLICT (channel_type, channel_value) DO NOTHING
      $sql$;

      EXECUTE $sql$
        INSERT INTO user_auth_accounts (
          id_user,
          provider,
          external_subject_id,
          external_username,
          external_email,
          is_active,
          linked_at
        )
        SELECT
          u.id,
          'telegram',
          btrim(u.tg_user_id::text),
          NULL,
          NULL,
          TRUE,
          now()
        FROM users u
        WHERE u.tg_user_id IS NOT NULL
        ON CONFLICT (provider, external_subject_id) DO NOTHING
      $sql$;
    END IF;
  END IF;
END $$;

-- Assumption: contractor role is id_role = 3 (see bootstrap roles).
WITH contractor_email_source AS (
  SELECT
    p.id AS id_user,
    btrim(p.mail) AS channel_value
  FROM profiles p
  JOIN users u
    ON u.id = p.id
  WHERE u.id_role = 3
    AND p.mail IS NOT NULL
    AND btrim(p.mail) <> ''
    AND btrim(p.mail) ~* '^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,63}$'
)
INSERT INTO user_contact_channels (
  id_user,
  channel_type,
  channel_value,
  is_verified,
  verified_at,
  is_primary,
  is_active,
  created_at,
  updated_at
)
SELECT
  s.id_user,
  'email',
  s.channel_value,
  FALSE,
  NULL,
  NOT EXISTS (
    SELECT 1
    FROM user_contact_channels c
    WHERE c.id_user = s.id_user
      AND c.channel_type = 'email'
      AND c.is_primary = TRUE
  ) AS is_primary,
  TRUE,
  now(),
  now()
FROM contractor_email_source s
ON CONFLICT (channel_type, channel_value) DO NOTHING;

INSERT INTO user_notification_preferences (
  id_contact_channel,
  notification_type,
  is_enabled,
  created_at,
  updated_at
)
SELECT
  c.id,
  t.notification_type,
  TRUE,
  now(),
  now()
FROM user_contact_channels c
CROSS JOIN (
  VALUES
    ('chat'::TEXT),
    ('request'::TEXT),
    ('offer'::TEXT),
    ('system'::TEXT)
) AS t(notification_type)
ON CONFLICT (id_contact_channel, notification_type) DO NOTHING;

-- ---------------------------------------------------------------------------
-- C) Trigger setup (created_at / updated_at consistency)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trg_users_timestamps()
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

DROP TRIGGER IF EXISTS users_timestamps ON users;
CREATE TRIGGER users_timestamps
BEFORE INSERT OR UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION trg_users_timestamps();

CREATE OR REPLACE FUNCTION trg_user_contact_channels_timestamps()
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

DROP TRIGGER IF EXISTS user_contact_channels_timestamps ON user_contact_channels;
CREATE TRIGGER user_contact_channels_timestamps
BEFORE INSERT OR UPDATE ON user_contact_channels
FOR EACH ROW
EXECUTE FUNCTION trg_user_contact_channels_timestamps();

CREATE OR REPLACE FUNCTION trg_user_notification_preferences_timestamps()
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

DROP TRIGGER IF EXISTS user_notification_preferences_timestamps ON user_notification_preferences;
CREATE TRIGGER user_notification_preferences_timestamps
BEFORE INSERT OR UPDATE ON user_notification_preferences
FOR EACH ROW
EXECUTE FUNCTION trg_user_notification_preferences_timestamps();

-- ---------------------------------------------------------------------------
-- D) Legacy cleanup (enabled): final schema after migration = init schema.
-- ---------------------------------------------------------------------------
DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'users_tg_user_fk'
      AND conrelid = 'users'::regclass
  ) THEN
    ALTER TABLE users
      DROP CONSTRAINT users_tg_user_fk;
  END IF;
END $$;

ALTER TABLE users
  DROP COLUMN IF EXISTS tg_user_id;

ALTER TABLE users
  DROP COLUMN IF EXISTS password_hash;

DROP TABLE IF EXISTS tg_users;

ALTER TABLE profiles
  ALTER COLUMN phone DROP NOT NULL;

ALTER TABLE profiles
  ALTER COLUMN mail DROP NOT NULL;

ALTER TABLE profiles
  ALTER COLUMN mail DROP DEFAULT;

ALTER TABLE company_contacts
  ALTER COLUMN phone DROP NOT NULL;

ALTER TABLE company_contacts
  ALTER COLUMN mail DROP NOT NULL;

ALTER TABLE company_contacts
  ALTER COLUMN address DROP NOT NULL;

ALTER TABLE company_contacts
  ALTER COLUMN note DROP NOT NULL;

ALTER TABLE company_contacts
  ALTER COLUMN mail DROP DEFAULT;

ALTER TABLE company_contacts
  ALTER COLUMN address DROP DEFAULT;

ALTER TABLE company_contacts
  ALTER COLUMN note DROP DEFAULT;
