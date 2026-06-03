-- Normative document lifecycle status (actual / outdated).
-- Column name matches order_database V1.0.4: document_status.
-- NOTE: canonical order_database V1.0.4 also converts requests.id to TEXT;
-- that part is in V1.0.5__request_id_text.sql (deploy snapshot was truncated before 2026-06).

ALTER TABLE normative_files
    ADD COLUMN IF NOT EXISTS document_status TEXT NOT NULL DEFAULT 'actual';

ALTER TABLE normative_files
    DROP CONSTRAINT IF EXISTS normative_files_document_status_chk;

ALTER TABLE normative_files
    ADD CONSTRAINT normative_files_document_status_chk
    CHECK (document_status IN ('actual', 'outdated'));

CREATE INDEX IF NOT EXISTS idx_normative_files_document_status_actual
    ON normative_files (id)
    WHERE document_status = 'actual';
