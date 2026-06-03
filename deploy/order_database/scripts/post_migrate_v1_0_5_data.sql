-- Post-migration checks for V1.0.5 (idempotent). Run after flyway migrate.

BEGIN;

UPDATE normative_files
SET document_status = 'actual'
WHERE document_status IS NULL;

UPDATE requests
SET id = btrim(id)
WHERE id IS DISTINCT FROM btrim(id);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'requests'
      AND column_name = 'id'
      AND udt_name = 'text'
  ) THEN
    RAISE EXCEPTION 'post_migrate_v1_0_5: requests.id is not TEXT';
  END IF;
END $$;

COMMIT;

SELECT 'flyway_v1.0.5' AS check_name,
       version,
       description,
       success,
       installed_on
FROM flyway_schema_history
WHERE version = '1.0.5';

SELECT 'requests' AS entity,
       COUNT(*) AS row_count,
       pg_typeof(id)::text AS id_type
FROM requests
GROUP BY pg_typeof(id);
