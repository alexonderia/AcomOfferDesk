from __future__ import annotations

import io
import zipfile

from fastapi.testclient import TestClient

from file_guard.app.main import app

client = TestClient(app)


def _valid_pdf_bytes() -> bytes:
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >>\nendobj\n"
        b"trailer\n<< /Root 1 0 R >>\n%%EOF"
    )


def _office_bytes(required_entry: str) -> bytes:
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types></Types>")
        archive.writestr(required_entry, "<xml />")
    return payload.getvalue()


_VALID_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\x0f"
    b"\x00\x01\x01\x01\x00\x18\xdd\x8d\xe1\x00\x00\x00\x00IEND\xaeB`\x82"
)
_VALID_JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xdb\x00C\x00" + b"\x08" * 64 + b"\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00"
    + b"\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xd2\xcf \xff\xd9"
)


def test_scan_allows_valid_pdf() -> None:
    response = client.post("/scan", files={"file": ("ok.pdf", _valid_pdf_bytes(), "application/pdf")})

    assert response.status_code == 200
    payload = response.json()
    assert payload["allowed"] is True
    assert payload["reason_code"] is None
    assert payload["detected_mime"] == "application/pdf"


def test_scan_blocks_disallowed_extension() -> None:
    response = client.post("/scan", files={"file": ("bad.exe", b"MZ...", "application/octet-stream")})

    assert response.status_code == 200
    assert response.json()["reason_code"] == "file_type_not_allowed"


def test_scan_blocks_pdf_exe_disguise() -> None:
    response = client.post("/scan", files={"file": ("file.pdf.exe", _valid_pdf_bytes(), "application/pdf")})

    assert response.status_code == 200
    assert response.json()["reason_code"] == "file_type_not_allowed"


def test_scan_blocks_mime_mismatch() -> None:
    response = client.post("/scan", files={"file": ("wrong.pdf", _VALID_PNG, "application/pdf")})

    assert response.status_code == 200
    assert response.json()["reason_code"] == "mime_mismatch"


def test_scan_blocks_invalid_pdf() -> None:
    response = client.post("/scan", files={"file": ("broken.pdf", b"%PDF-1.4 broken", "application/pdf")})

    assert response.status_code == 200
    assert response.json()["reason_code"] == "invalid_pdf"


def test_scan_allows_minimal_pdf_without_startxref() -> None:
    response = client.post("/scan", files={"file": ("minimal.pdf", _valid_pdf_bytes(), "application/pdf")})

    assert response.status_code == 200
    assert response.json()["allowed"] is True


def test_scan_allows_valid_docx_and_xlsx() -> None:
    docx = client.post(
        "/scan",
        files={"file": ("ok.docx", _office_bytes("word/document.xml"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    xlsx = client.post(
        "/scan",
        files={"file": ("ok.xlsx", _office_bytes("xl/workbook.xml"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert docx.json()["allowed"] is True
    assert xlsx.json()["allowed"] is True


def test_scan_blocks_invalid_office_document() -> None:
    response = client.post("/scan", files={"file": ("broken.docx", b"PK\x03\x04broken", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})

    assert response.status_code == 200
    assert response.json()["reason_code"] == "invalid_office_document"


def test_scan_allows_valid_images() -> None:
    png = client.post("/scan", files={"file": ("ok.png", _VALID_PNG, "image/png")})
    jpg = client.post("/scan", files={"file": ("ok.jpg", _VALID_JPEG, "image/jpeg")})

    assert png.json()["allowed"] is True
    assert jpg.json()["allowed"] is True


def test_scan_blocks_invalid_image() -> None:
    response = client.post("/scan", files={"file": ("broken.png", b"\x89PNG\r\n\x1a\nbroken", "image/png")})

    assert response.status_code == 200
    assert response.json()["reason_code"] == "invalid_image"
