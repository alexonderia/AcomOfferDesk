from __future__ import annotations

import io
from dataclasses import replace
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from pypdf.generic import ArrayObject, DecodedStreamObject, DictionaryObject, NameObject, TextStringObject

from file_guard.app import main as main_module
from file_guard.app import scanner as scanner_module
from file_guard.app.scanner import FileScanner


def _box(kind: bytes, payload: bytes) -> bytes:
    return (len(payload) + 8).to_bytes(4, "big") + kind + payload


def _description(kind: bytes, label: bytes) -> bytes:
    return _box(b"jumd", kind + bytes.fromhex("00110010800000aa00389b71") + b"\x03" + label + b"\0")


def _c2pa_bytes() -> bytes:
    claim = _box(b"jumb", _description(b"c2cl", b"c2pa.claim.v2") + _box(b"cbor", b"\xa0"))
    manifest = _box(b"jumb", _description(b"c2ma", b"urn:c2pa:test") + claim)
    return _box(b"jumb", _description(b"c2pa", b"c2pa") + manifest)


def _add_attachment(
    writer: PdfWriter,
    data: bytes,
    *,
    mime: str = "application/c2pa",
    relationship: str = "/C2PA_Manifest",
    compressed: bool = True,
):
    stream = DecodedStreamObject()
    stream.set_data(data)
    stream[NameObject("/Type")] = NameObject("/EmbeddedFile")
    stream[NameObject("/Subtype")] = NameObject("/" + mime)
    if compressed:
        stream = stream.flate_encode()
    stream_ref = writer._add_object(stream)
    spec = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Filespec"),
            NameObject("/F"): TextStringObject("Content Credentials"),
            NameObject("/Subtype"): TextStringObject(mime),
            NameObject("/AFRelationship"): NameObject(relationship),
            NameObject("/EF"): DictionaryObject({NameObject("/F"): stream_ref}),
        }
    )
    spec_ref = writer._add_object(spec)
    root = writer.root_object
    if "/Names" not in root:
        root[NameObject("/Names")] = DictionaryObject(
            {NameObject("/EmbeddedFiles"): DictionaryObject({NameObject("/Names"): ArrayObject()})}
        )
        root[NameObject("/AF")] = ArrayObject()
    root["/Names"]["/EmbeddedFiles"]["/Names"].extend([TextStringObject("Content Credentials"), spec_ref])
    root["/AF"].append(spec_ref)
    return spec, stream


def _writer() -> PdfWriter:
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    return writer


def _pdf_bytes(writer: PdfWriter) -> bytes:
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


class _Antivirus:
    def __init__(self):
        self.scanned: list[bytes] = []
        self.infected: bytes | None = None
        self.unavailable = False

    def is_ready(self):
        return True

    def scan_bytes(self, *, content_bytes: bytes):
        self.scanned.append(content_bytes)
        if self.unavailable:
            raise scanner_module.AntivirusUnavailableError("unavailable")
        return SimpleNamespace(infected=content_bytes == self.infected, signature="test-signature")


@pytest.fixture
def guard(monkeypatch):
    antivirus = _Antivirus()
    settings = replace(scanner_module.settings, antivirus_enabled=True)
    monkeypatch.setattr(main_module, "settings", settings)
    monkeypatch.setattr(scanner_module, "settings", settings)
    monkeypatch.setattr(main_module, "_scanner", FileScanner(antivirus_scanner=antivirus))
    return TestClient(main_module.app), antivirus


def _scan(guard, writer: PdfWriter):
    client, _ = guard
    return client.post("/scan", files={"file": ("metadata.pdf", _pdf_bytes(writer), "application/pdf")})


@pytest.mark.parametrize("compressed", [False, True])
@pytest.mark.parametrize("mime", ["application/c2pa", "application/x-c2pa-manifest-store"])
def test_allows_c2pa_and_scans_decoded_metadata_and_original_pdf(guard, compressed, mime):
    writer = _writer()
    data = _c2pa_bytes()
    _add_attachment(writer, data, mime=mime, compressed=compressed)
    payload = _pdf_bytes(writer)
    client, antivirus = guard
    response = client.post("/scan", files={"file": ("original.pdf", payload, "application/pdf")})

    assert response.status_code == 200
    assert response.json()["allowed"] is True
    assert antivirus.scanned == [data, payload]


@pytest.mark.parametrize("location", ["associated_file", "annotation", "name_tree"])
def test_checks_metadata_outside_the_embedded_files_name_tree(guard, location):
    writer = _writer()
    spec, _ = _add_attachment(writer, _c2pa_bytes())
    if location != "name_tree":
        del writer.root_object["/Names"]
    if location == "annotation":
        del writer.root_object["/AF"]
        writer.pages[0][NameObject("/Annots")] = ArrayObject(
            [DictionaryObject({NameObject("/Subtype"): NameObject("/FileAttachment"), NameObject("/FS"): spec})]
        )
    response = _scan(guard, writer)

    assert response.json()["allowed"] is True


def test_allows_older_c2pa_producer_without_file_spec_mime(guard):
    writer = _writer()
    spec, _ = _add_attachment(writer, _c2pa_bytes())
    del spec["/Subtype"]
    assert _scan(guard, writer).json()["allowed"] is True


@pytest.mark.parametrize("data", [b"MZ executable", b"<script>alert(1)</script>", b"PK\x03\x04archive", b"not C2PA"])
def test_rejects_arbitrary_payload_disguised_as_content_credentials(guard, data):
    writer = _writer()
    _add_attachment(writer, data)
    response = _scan(guard, writer)

    assert response.json()["reason_code"] == "invalid_pdf"
    assert guard[1].scanned == []


@pytest.mark.parametrize("mime,relationship", [("application/octet-stream", "/C2PA_Manifest"), ("application/c2pa", "/Data")])
def test_does_not_allow_arbitrary_attachment_declarations(guard, mime, relationship):
    writer = _writer()
    _add_attachment(writer, _c2pa_bytes(), mime=mime, relationship=relationship)
    assert _scan(guard, writer).json()["reason_code"] == "invalid_pdf"


@pytest.mark.parametrize("hidden", [False, True])
def test_c2pa_does_not_exempt_other_attachments_including_unreferenced_objects(guard, hidden):
    writer = _writer()
    _add_attachment(writer, _c2pa_bytes())
    _add_attachment(writer, b"MZ executable", mime="application/octet-stream", relationship="/Data")
    if hidden:
        del writer.root_object["/Names"]["/EmbeddedFiles"]["/Names"][-2:]
        writer.root_object["/AF"].pop()
    assert _scan(guard, writer).json()["reason_code"] == "invalid_pdf"


def test_blocks_undeclared_embedded_stream(guard):
    writer = _writer()
    spec, _ = _add_attachment(writer, _c2pa_bytes())
    del spec["/EF"]
    assert _scan(guard, writer).json()["reason_code"] == "invalid_pdf"


@pytest.mark.parametrize(
    "data",
    [
        _c2pa_bytes()[:-1],
        _c2pa_bytes() + b"trailing payload",
        _c2pa_bytes().replace(b"c2pa\x00\x11", b"fake\x00\x11", 1),
        _box(b"jumb", _description(b"c2pa", b"c2pa")),
        _box(b"jumb", _description(b"c2pa", b"c2pa") + b"\x00\x00\x00\x07jumb"),
    ],
)
def test_rejects_invalid_or_truncated_c2pa_envelope(guard, data):
    writer = _writer()
    _add_attachment(writer, data)
    assert _scan(guard, writer).json()["reason_code"] == "invalid_pdf"


def test_bounds_decompressed_metadata_size(guard, monkeypatch):
    writer = _writer()
    data = _box(b"jumb", _description(b"c2pa", b"c2pa") + _box(b"free", b"A" * 100_000))
    _add_attachment(writer, data)
    monkeypatch.setattr(scanner_module, "settings", replace(scanner_module.settings, max_file_size_bytes=4096))
    assert len(_pdf_bytes(writer)) < 4096
    assert _scan(guard, writer).json()["reason_code"] == "invalid_pdf"


@pytest.mark.parametrize("active", ["/JavaScript", "/JS", "/OpenAction", "/AA", "/Launch", "/RichMedia", "/XFA"])
def test_c2pa_does_not_exempt_pdf_active_content(guard, active):
    writer = _writer()
    _add_attachment(writer, _c2pa_bytes())
    writer.root_object[NameObject(active)] = TextStringObject("payload")
    assert _scan(guard, writer).json()["reason_code"] == "invalid_pdf"


def test_blocks_escaped_active_pdf_names(guard):
    writer = _writer()
    _add_attachment(writer, _c2pa_bytes())
    writer.root_object[NameObject("/JS")] = TextStringObject("payload")
    payload = _pdf_bytes(writer).replace(b"/JS ", b"/#4a#53 ")
    response = guard[0].post("/scan", files={"file": ("escaped.pdf", payload, "application/pdf")})
    assert response.json()["reason_code"] == "invalid_pdf"


def test_fails_closed_for_metadata_when_pdf_parser_is_unavailable(guard, monkeypatch):
    writer = _writer()
    _add_attachment(writer, _c2pa_bytes())
    monkeypatch.setattr(scanner_module, "PdfReader", None)
    assert _scan(guard, writer).json()["reason_code"] == "invalid_pdf"


@pytest.mark.parametrize("infect_metadata", [False, True])
def test_c2pa_does_not_bypass_antivirus_verdicts(guard, infect_metadata):
    writer = _writer()
    data = _c2pa_bytes()
    _add_attachment(writer, data)
    guard[1].infected = data if infect_metadata else _pdf_bytes(writer)
    assert _scan(guard, writer).json()["reason_code"] == "malware_detected"


def test_c2pa_fails_closed_when_antivirus_is_unavailable(guard):
    writer = _writer()
    _add_attachment(writer, _c2pa_bytes())
    guard[1].unavailable = True
    response = _scan(guard, writer)
    assert response.status_code == 503
    assert response.json()["reason_code"] == "file_scan_unavailable"
