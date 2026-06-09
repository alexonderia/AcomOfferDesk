# File Security

## Purpose

`file_guard` is the single isolated runtime responsible for validating user-uploaded files before backend persists them in MinIO/S3 and links them in the database.

The main data flow stays unchanged:

```text
frontend -> backend -> file_guard -> verdict -> backend persistence
```

## Why Validation Stays Outside Backend

* Backend remains the orchestrator and does not duplicate deep file parsing logic.
* A single guard service keeps upload rules consistent across requests, offers, chat files, and normative documents.
* Fail-closed behavior is centralized: if `file_guard` cannot complete a mandatory check, backend must not save the file.

## Container Model

`file_guard` remains one dedicated internal container on `project_net`.

Inside the same container:

* FastAPI exposes `/scan` and `/health`
* format validators inspect PDF, DOCX, XLSX, PNG, and JPEG
* local ClamAV (`clamd`) performs antivirus checks through a Unix socket

There is no separate `clamav` service in the runtime stack.

## Allowed File Types

Allowed extensions:

* `.pdf`
* `.docx`
* `.xlsx`
* `.jpg`
* `.jpeg`
* `.png`

Everything else is rejected with `reason_code=file_type_not_allowed`.

## Validation Stages

Each upload goes through these checks before backend may persist it:

1. File name safety
2. Empty-file and file-size validation
3. Extension allowlist / denylist validation
4. MIME and signature validation
5. Deep format validation
6. Antivirus scan

Examples of deep validation:

* PDF: parseability, non-encrypted structure, no dangerous active objects
* DOCX/XLSX: required OpenXML entries, no zip-slip, no macro payloads, no zip-bomb/resource-abuse patterns
* PNG/JPEG: decodable image with safe dimensions

## Fail-Closed Rules

The file is blocked if:

* `file_guard` cannot complete a mandatory check
* ClamAV is unavailable or times out
* MIME/signature does not match the extension
* the file structure is corrupted or suspicious
* malware is detected

Backend also blocks persistence when `file_guard` itself is unreachable.

## Reason Codes

Current public-facing reasons include:

* `file_type_not_allowed`
* `file_too_large`
* `empty_file`
* `unsafe_file_name`
* `mime_mismatch`
* `invalid_pdf`
* `encrypted_pdf_not_allowed`
* `invalid_office_document`
* `invalid_image`
* `malware_detected`
* `file_scan_unavailable`

`file_guard` may keep technical internal messages in English, but backend must return safe Russian user-facing text by `reason_code`.

## Health And Readiness

`/health` returns success only when:

* FastAPI is alive
* antivirus is either explicitly disabled by config or ready for scans

If ClamAV is enabled but unavailable, `file_guard` health degrades and the container must not be treated as ready to accept safe uploads.

## Environment Variables

Important backend variables:

* `FILE_GUARD_ENABLED`
* `FILE_GUARD_URL`
* `FILE_GUARD_TIMEOUT_SECONDS`
* `MAX_UPLOAD_SIZE_BYTES`

Important `file_guard` variables:

* `FILE_GUARD_MAX_FILE_SIZE_BYTES`
* `FILE_GUARD_ALLOW_LIBMAGIC_FALLBACK`
* `FILE_GUARD_ANTIVIRUS_ENABLED`
* `FILE_GUARD_ANTIVIRUS_TIMEOUT_SECONDS`
* `FILE_GUARD_CLAMD_SOCKET_PATH`
* `FILE_GUARD_CLAMAV_UPDATE_ON_START`
* `FILE_GUARD_OFFICE_MAX_ENTRIES`
* `FILE_GUARD_OFFICE_MAX_TOTAL_UNCOMPRESSED_BYTES`
* `FILE_GUARD_OFFICE_MAX_ENTRY_UNCOMPRESSED_BYTES`
* `FILE_GUARD_OFFICE_MAX_COMPRESSION_RATIO`
* `FILE_GUARD_IMAGE_MAX_WIDTH`
* `FILE_GUARD_IMAGE_MAX_HEIGHT`
* `FILE_GUARD_IMAGE_MAX_PIXELS`

## Notes

The current implementation keeps ClamAV inside `file_guard`. If runtime load grows later, the antivirus engine can be split into a separate service without changing the backend upload contract.

Any manual smoke that persists a file through backend must also remove the created database link and storage object after the happy-path is confirmed. Direct `/scan` checks do not leave persistence artifacts, but backend upload checks must not leave test files in MinIO or in file-link tables.
