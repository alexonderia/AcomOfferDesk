-- Hidden attachments are separate from public request_files.
CREATE TABLE request_hidden_files (
    id BIGINT PRIMARY KEY REFERENCES files(id) ON DELETE RESTRICT,
    id_request TEXT NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
    -- NULL is reserved for historical links whose extraction choice is unknown.
    is_specification_source BOOLEAN DEFAULT FALSE
);
CREATE INDEX request_hidden_files_request_idx ON request_hidden_files(id_request);

COMMENT ON TABLE request_hidden_files IS 'Скрытые файлы заявок, недоступные контрагентам';
COMMENT ON COLUMN request_hidden_files.is_specification_source IS
    'TRUE — исходник для выделения ТЗ; FALSE — обычное скрытое вложение; NULL — назначение старого файла неизвестно';
