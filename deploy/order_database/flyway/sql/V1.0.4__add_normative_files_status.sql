-- Normative document lifecycle status (actual / outdated).
-- Column name matches order_database V1.0.4: document_status.

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
