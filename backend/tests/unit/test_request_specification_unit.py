from __future__ import annotations

import base64
from dataclasses import replace
import io
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
import zipfile
from xml.etree import ElementTree

from docx import Document
from openpyxl import Workbook
import pymupdf
import pytest

from app.domain.exceptions import Conflict
from app.domain.auth_context import CurrentUser
from app.domain.permissions import PermissionCodes
from app.infrastructure.specification_parser import DOCX_MIME, ParseError, extract_documents, parse_rows
from app.services.files import PreparedUpload
from app.services.request_specification import RequestSpecificationService


ROWS = [
    ["Наименование", "Количество", "Ед. изм.", "Цена", "Сумма", "Реквизиты"],
    ["Насос промышленный", "2", "шт.", "15000", "30000", "ИНН 1234567890"],
    ["Монтаж оборудования", "1", "услуга", "12345", "12345", "ООО Поставщик"],
]


def docx_source(rows=ROWS) -> bytes:
    document = Document()
    document.core_properties.author = "Секретный поставщик"
    document.add_paragraph("Договор №123. ООО Поставщик, ИНН 1234567890. Итого 42345 рублей.")
    table = document.add_table(rows=0, cols=len(rows[0]))
    for values in rows:
        for cell, value in zip(table.add_row().cells, values):
            cell.text = value
    result = io.BytesIO()
    document.save(result)
    return result.getvalue()


def pdf_source() -> bytes:
    document = pymupdf.open()
    page = document.new_page(width=1000, height=600)
    html_rows = "".join("<tr>" + "".join(f'<td style="border:1px solid black;padding:8px">{cell}</td>' for cell in row) + "</tr>" for row in ROWS)
    page.insert_htmlbox(pymupdf.Rect(20, 20, 980, 580), '<table style="border-collapse:collapse;width:100%;font-size:16px">' + html_rows + "</table>")
    result = document.tobytes()
    document.close()
    return result


def assert_clean(content: bytes, count: int) -> None:
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        text = "\n".join(" ".join(ElementTree.fromstring(archive.read(name)).itertext()) for name in archive.namelist() if name.endswith(".xml"))
    assert "Насос промышленный" in text
    assert "Монтаж оборудования" in text
    assert count == 2
    for secret in ("15000", "30000", "12345", "ИНН", "Поставщик", "Секретный", "рублей", "Договор №123"):
        assert secret not in text
    document = Document(io.BytesIO(content))
    assert [row.cells[1].text for row in document.tables[0].rows[1:]] == ["2", "1"]


def test_docx_rebuilds_specification_without_financial_columns_or_metadata():
    content, count, ocr = extract_documents([("договор.docx", docx_source())])
    assert_clean(content, count)
    assert not ocr


def test_xlsx_extracts_positions_from_multiple_sheets():
    workbook = Workbook()
    workbook.active.append(ROWS[0])
    workbook.active.append(ROWS[1])
    sheet = workbook.create_sheet("Услуги")
    sheet.append(ROWS[0])
    sheet.append(ROWS[2])
    result = io.BytesIO()
    workbook.save(result)
    content, count, ocr = extract_documents([("договор.xlsx", result.getvalue())])
    assert_clean(content, count)
    assert not ocr


def test_xlsx_does_not_silently_drop_uncalculated_quantity():
    workbook = Workbook()
    workbook.active.append(ROWS[0])
    workbook.active.append(["Насос", "=1+1", "шт.", "=200*2", None, None])
    result = io.BytesIO()
    workbook.save(result)
    with pytest.raises(ParseError, match="результата формулы"):
        extract_documents([("source.xlsx", result.getvalue())])


def test_text_pdf_extracts_table_and_excludes_prices():
    content, count, ocr = extract_documents([("договор.pdf", pdf_source())])
    assert_clean(content, count)
    assert not ocr


@pytest.mark.parametrize("suffix", [".png", ".jpg", ".pdf"])
def test_scans_are_recognized_locally(suffix):
    # Runtime image installs both packs. Local runs can supply TESSDATA_PREFIX.
    try:
        tessdata = Path(pymupdf.get_tessdata())
    except RuntimeError:
        pytest.skip("Для OCR нужны локальные языковые пакеты Tesseract")
    if not all((tessdata / f"{language}.traineddata").exists() for language in ("rus", "eng")):
        pytest.skip("Для OCR нужны rus.traineddata и eng.traineddata")
    with pymupdf.open(stream=pdf_source(), filetype="pdf") as source:
        pixmap = source[0].get_pixmap(dpi=200)
        if suffix == ".pdf":
            with pymupdf.open() as scanned:
                page = scanned.new_page(width=source[0].rect.width, height=source[0].rect.height)
                page.insert_image(page.rect, pixmap=pixmap)
                data = scanned.tobytes()
        else:
            data = pixmap.tobytes("jpeg" if suffix == ".jpg" else "png")
    content, count, ocr = extract_documents([("скан" + suffix, data)])
    assert_clean(content, count)
    assert ocr


def test_sensitive_data_in_allowed_column_blocks_publication():
    with pytest.raises(ParseError, match="цены или реквизиты"):
        parse_rows([ROWS[0], ["Насос, цена 15000 руб.", "2", "шт.", "", "", ""]])


def test_unrecognized_source_is_not_silently_skipped():
    with pytest.raises(ParseError, match="не найдена таблица"):
        extract_documents([("empty.docx", docx_source([["Текст"], ["Нет таблицы товаров"]]))])


def test_isolated_pdf_parser_returns_clean_json_despite_library_diagnostics():
    result = RequestSpecificationService._parse([{"name": "source.pdf", "content": base64.b64encode(pdf_source()).decode()}])
    assert_clean(base64.b64decode(result["content"]), result["item_count"])


@pytest.mark.asyncio
async def test_confirmation_binds_user_original_and_exact_preview(monkeypatch):
    import hashlib

    def upload(name, content, mime=DOCX_MIME):
        return PreparedUpload(name, content, mime, hashlib.sha256(content).hexdigest())

    source = upload("договор.docx", docx_source())
    generated, count, _ = extract_documents([("договор.docx", source.content_bytes)])
    specification = upload("Заявка на закупку REQ-1.docx", generated)
    file_service = SimpleNamespace(prepare_bytes=AsyncMock(return_value=specification))
    service = RequestSpecificationService(file_service)
    monkeypatch.setattr(service, "_parse", lambda payload: {"content": base64.b64encode(generated).decode(), "item_count": count, "used_ocr": False})
    user = CurrentUser(user_id="economist", role_id=6, status="active", permissions=frozenset({PermissionCodes.REQUESTS_CREATE}),
                       iam_account_id="account", iam_session_id="session", system_role="economist")
    preview = await service.prepare(current_user=user, request_id="REQ-1", sources=[source])
    verified = service.verify(current_user=user, request_id="REQ-1", sources=[source], specification=specification, confirmation=preview.confirmation)
    assert verified.public_source_indices == ()
    assert verified.extraction_indices == (0,)
    public_preview = await service.prepare(current_user=user, request_id="REQ-1", sources=[source], public_source_indices=[0])
    assert service.verify(current_user=user, request_id="REQ-1", sources=[source], specification=specification, confirmation=public_preview.confirmation).public_source_indices == (0,)
    encoded, signature = preview.confirmation.split('.')
    import json
    claims = json.loads(base64.urlsafe_b64decode(encoded))
    claims["public_source_indices"] = [0]
    changed_encoded = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode()
    with pytest.raises(Conflict):
        service.verify(current_user=user, request_id="REQ-1", sources=[source], specification=specification,
                       confirmation=f"{changed_encoded}.{signature}")
    with pytest.raises(Conflict):
        service.verify(current_user=user, request_id="REQ-2", sources=[source], specification=specification, confirmation=preview.confirmation)
    for changed_user, changed_source, changed_spec, confirmation in (
        (replace(user, user_id="other"), source, specification, preview.confirmation),
        (user, replace(source, content_sha256="other"), specification, preview.confirmation),
        (user, source, replace(specification, content_sha256="other"), preview.confirmation),
        (user, source, specification, preview.confirmation + "bad"),
    ):
        with pytest.raises(Conflict):
            service.verify(current_user=changed_user, request_id="REQ-1", sources=[changed_source], specification=changed_spec, confirmation=confirmation)


@pytest.mark.parametrize("indices", [[], [-1], [1], [0, 0], [True]])
def test_extraction_selection_must_reference_nonempty_unique_source_subset(indices):
    with pytest.raises(Conflict, match="Выберите файлы"):
        RequestSpecificationService._extraction_indices([SimpleNamespace()], indices)
