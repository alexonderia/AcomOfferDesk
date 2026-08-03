CREATE TABLE IF NOT EXISTS units (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  id_parent BIGINT NULL REFERENCES units(id) ON DELETE RESTRICT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  id_created_by_user TEXT NULL REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now(),
  CONSTRAINT units_parent_name_key UNIQUE (id_parent, name)
);

CREATE TABLE IF NOT EXISTS unit_members (
  id_unit BIGINT NOT NULL REFERENCES units(id) ON DELETE CASCADE,
  id_user TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  id_assigned_by_user TEXT NULL REFERENCES users(id) ON DELETE SET NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now(),
  PRIMARY KEY (id_unit, id_user)
);

CREATE INDEX IF NOT EXISTS idx_units_id_parent ON units (id_parent);
CREATE INDEX IF NOT EXISTS idx_units_is_active ON units (is_active);
CREATE INDEX IF NOT EXISTS idx_unit_members_id_user ON unit_members (id_user);
CREATE INDEX IF NOT EXISTS idx_unit_members_is_active ON unit_members (is_active);
