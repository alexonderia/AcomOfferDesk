from __future__ import annotations

import io
import os
import struct
import zipfile
from dataclasses import replace
import zlib

from fastapi.testclient import TestClient
import pytest

os.environ.setdefault("FILE_GUARD_ANTIVIRUS_ENABLED", "false")

from file_guard.app import main as main_module
from file_guard.app import scanner as scanner_module
from file_guard.app.scanner import FileScanner

client = TestClient(main_module.app)


class _ReadyAntivirus:
    def is_ready(self) -> bool:
        return True

    def scan_bytes(self, *, content_bytes: bytes):
        _ = content_bytes
        return type("Result", (), {"infected": False, "signature": None})()


class _MalwareAntivirus(_ReadyAntivirus):
    def scan_bytes(self, *, content_bytes: bytes):
        _ = content_bytes
        return type("Result", (), {"infected": True, "signature": "Eicar-Test-Signature"})()


class _UnavailableAntivirus:
    def is_ready(self) -> bool:
        return False

    def scan_bytes(self, *, content_bytes: bytes):
        _ = content_bytes
        raise scanner_module.AntivirusUnavailableError("clamd unavailable")


def _valid_pdf_bytes() -> bytes:
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >>\nendobj\n"
        b"trailer\n<< /Root 1 0 R >>\n%%EOF"
    )


def _office_bytes(*entries: tuple[str, bytes | str]) -> bytes:
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types></Types>")
        for name, value in entries:
            archive.writestr(name, value)
    return payload.getvalue()


def _png_bytes(*, width: int = 1, height: int = 1) -> bytes:
    raw_row = b"\x00" + (b"\xff\x00\x00" * width)
    raw_data = raw_row * height
    compressed = zlib.compress(raw_data)

    def _chunk(chunk_type: bytes, payload: bytes) -> bytes:
        return (
            len(payload).to_bytes(4, "big")
            + chunk_type
            + payload
            + zlib.crc32(chunk_type + payload).to_bytes(4, "big")
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", compressed)
        + _chunk(b"IEND", b"")
    )


def _jpeg_bytes(*, width: int = 1, height: int = 1) -> bytes:
    _ = (width, height)
    return (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00C\x00" + b"\x08" * 64 + b"\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00"
        + b"\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xd2\xcf \xff\xd9"
    )


def _patch_scanner(monkeypatch, *, antivirus, **settings_overrides) -> None:
    if settings_overrides:
        monkeypatch.setattr(scanner_module, "settings", replace(scanner_module.settings, **settings_overrides))
        monkeypatch.setattr(main_module, "settings", replace(main_module.settings, **settings_overrides))
    monkeypatch.setattr(main_module, "_scanner", FileScanner(antivirus_scanner=antivirus))


def test_scan_allows_valid_pdf(monkeypatch) -> None:
    _patch_scanner(monkeypatch, antivirus=_ReadyAntivirus())
    response = client.post("/scan", files={"file": ("ok.pdf", _valid_pdf_bytes(), "application/pdf")})

    assert response.status_code == 200
    payload = response.json()
    assert payload["allowed"] is True
    assert payload["reason_code"] is None
    assert payload["detected_mime"] == "application/pdf"


def test_scan_blocks_disallowed_extension(monkeypatch) -> None:
    _patch_scanner(monkeypatch, antivirus=_ReadyAntivirus())
    response = client.post("/scan", files={"file": ("bad.exe", b"MZ...", "application/octet-stream")})

    assert response.status_code == 200
    assert response.json()["reason_code"] == "file_type_not_allowed"


def test_scan_blocks_pdf_exe_disguise(monkeypatch) -> None:
    _patch_scanner(monkeypatch, antivirus=_ReadyAntivirus())
    response = client.post("/scan", files={"file": ("file.pdf.exe", _valid_pdf_bytes(), "application/pdf")})

    assert response.status_code == 200
    assert response.json()["reason_code"] == "file_type_not_allowed"


def test_scan_blocks_mime_mismatch(monkeypatch) -> None:
    _patch_scanner(monkeypatch, antivirus=_ReadyAntivirus())
    response = client.post("/scan", files={"file": ("wrong.pdf", _png_bytes(), "application/pdf")})

    assert response.status_code == 200
    assert response.json()["reason_code"] == "mime_mismatch"


def test_scan_blocks_invalid_pdf(monkeypatch) -> None:
    _patch_scanner(monkeypatch, antivirus=_ReadyAntivirus())
    response = client.post("/scan", files={"file": ("broken.pdf", b"%PDF-1.4 broken", "application/pdf")})

    assert response.status_code == 200
    assert response.json()["reason_code"] == "invalid_pdf"


def test_scan_blocks_pdf_when_pypdf_parse_fails(monkeypatch) -> None:
    _patch_scanner(monkeypatch, antivirus=_ReadyAntivirus())
    original_reader = scanner_module.PdfReader

    def _raise_pdf_parse_error(*args, **kwargs):
        _ = (args, kwargs)
        raise ValueError("parse failed")

    monkeypatch.setattr(scanner_module, "PdfReader", _raise_pdf_parse_error)
    parse_failed_pdf = _valid_pdf_bytes()

    response = client.post("/scan", files={"file": ("broken_with_eof.pdf", parse_failed_pdf, "application/pdf")})

    assert response.status_code == 200
    assert response.json()["reason_code"] == "invalid_pdf"
    monkeypatch.setattr(scanner_module, "PdfReader", original_reader)


def test_scan_blocks_encrypted_pdf(monkeypatch) -> None:
    _patch_scanner(monkeypatch, antivirus=_ReadyAntivirus())
    encrypted_like_pdf = b"%PDF-1.4\n1 0 obj\n<< /Encrypt 2 0 R >>\nendobj\n%%EOF"

    response = client.post("/scan", files={"file": ("secret.pdf", encrypted_like_pdf, "application/pdf")})

    assert response.status_code == 200
    assert response.json()["reason_code"] == "encrypted_pdf_not_allowed"


def test_scan_blocks_pdf_with_javascript(monkeypatch) -> None:
    _patch_scanner(monkeypatch, antivirus=_ReadyAntivirus())
    suspicious_pdf = _valid_pdf_bytes() + b"\n/JavaScript"

    response = client.post("/scan", files={"file": ("script.pdf", suspicious_pdf, "application/pdf")})

    assert response.status_code == 200
    assert response.json()["reason_code"] == "invalid_pdf"


def test_scan_allows_valid_docx_and_xlsx(monkeypatch) -> None:
    _patch_scanner(monkeypatch, antivirus=_ReadyAntivirus())
    docx = client.post(
        "/scan",
        files={"file": ("ok.docx", _office_bytes(("word/document.xml", "<xml />")), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    xlsx = client.post(
        "/scan",
        files={"file": ("ok.xlsx", _office_bytes(("xl/workbook.xml", "<xml />")), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert docx.json()["allowed"] is True
    assert xlsx.json()["allowed"] is True


def test_scan_blocks_invalid_office_document(monkeypatch) -> None:
    _patch_scanner(monkeypatch, antivirus=_ReadyAntivirus())
    response = client.post("/scan", files={"file": ("broken.docx", b"PK\x03\x04broken", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})

    assert response.status_code == 200
    assert response.json()["reason_code"] == "invalid_office_document"


def test_scan_blocks_office_with_macro_payload(monkeypatch) -> None:
    _patch_scanner(monkeypatch, antivirus=_ReadyAntivirus())
    response = client.post(
        "/scan",
        files={
            "file": (
                "macro.docx",
                _office_bytes(("word/document.xml", "<xml />"), ("word/vbaProject.bin", b"macro")),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["reason_code"] == "invalid_office_document"


def test_scan_blocks_office_with_zip_slip_path(monkeypatch) -> None:
    _patch_scanner(monkeypatch, antivirus=_ReadyAntivirus())
    response = client.post(
        "/scan",
        files={
            "file": (
                "slip.docx",
                _office_bytes(("word/document.xml", "<xml />"), ("../evil.exe", b"boom")),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["reason_code"] == "invalid_office_document"


def test_scan_blocks_office_zip_bomb_like_payload(monkeypatch) -> None:
    _patch_scanner(
        monkeypatch,
        antivirus=_ReadyAntivirus(),
        office_max_compression_ratio=5.0,
    )
    response = client.post(
        "/scan",
        files={
            "file": (
                "bomb.docx",
                _office_bytes(("word/document.xml", "A" * 5000)),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["reason_code"] == "invalid_office_document"


def test_scan_allows_valid_images(monkeypatch) -> None:
    _patch_scanner(monkeypatch, antivirus=_ReadyAntivirus())
    png = client.post("/scan", files={"file": ("ok.png", _png_bytes(), "image/png")})
    jpg = client.post("/scan", files={"file": ("ok.jpg", _jpeg_bytes(), "image/jpeg")})

    assert png.json()["allowed"] is True
    assert jpg.json()["allowed"] is True


def test_scan_blocks_invalid_image(monkeypatch) -> None:
    _patch_scanner(monkeypatch, antivirus=_ReadyAntivirus())
    response = client.post("/scan", files={"file": ("broken.png", b"\x89PNG\r\n\x1a\nbroken", "image/png")})

    assert response.status_code == 200
    assert response.json()["reason_code"] == "invalid_image"


def test_scan_blocks_oversized_image_dimensions(monkeypatch) -> None:
    if scanner_module.Image is None:
        pytest.skip("Pillow is not installed in the current test environment")
    _patch_scanner(
        monkeypatch,
        antivirus=_ReadyAntivirus(),
        image_max_width=10,
        image_max_height=10,
        image_max_pixels=100,
    )
    response = client.post("/scan", files={"file": ("huge.png", _png_bytes(width=40, height=40), "image/png")})

    assert response.status_code == 200
    assert response.json()["reason_code"] == "invalid_image"


def test_scan_blocks_when_antivirus_detects_malware(monkeypatch) -> None:
    _patch_scanner(monkeypatch, antivirus=_MalwareAntivirus(), antivirus_enabled=True)
    response = client.post("/scan", files={"file": ("eicar.pdf", _valid_pdf_bytes(), "application/pdf")})

    assert response.status_code == 200
    assert response.json()["reason_code"] == "malware_detected"


def test_scan_fails_closed_when_antivirus_is_unavailable(monkeypatch) -> None:
    _patch_scanner(monkeypatch, antivirus=_UnavailableAntivirus(), antivirus_enabled=True)
    response = client.post("/scan", files={"file": ("blocked.pdf", _valid_pdf_bytes(), "application/pdf")})

    assert response.status_code == 503
    assert response.json()["reason_code"] == "file_scan_unavailable"


def test_health_reports_degraded_when_antivirus_not_ready(monkeypatch) -> None:
    _patch_scanner(monkeypatch, antivirus=_UnavailableAntivirus(), antivirus_enabled=True)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["reason_code"] == "file_scan_unavailable"
