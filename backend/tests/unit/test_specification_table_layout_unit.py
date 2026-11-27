"""Regressions for multi-page spare-part tables, merged cells and PDF backgrounds."""
from __future__ import annotations

import io
from pathlib import Path
import shutil

from docx import Document
from openpyxl import Workbook
import pymupdf
import pytest

from app.infrastructure import specification_parser as parser

HEADER = ["Оборудование", "Кол-\nво", "Наименование\nзапасной части", "Цена за ед.", "Общая\nстоимость"]
EQUIPMENT = "Станок сортировки аккумуляторных элементов"
PARTS = [
    ("Выключатель автоматический\nCHNT NXB-63 10", "3"),
    ("Пневмораспределитель электрический\nAIRTAC 4V 4V210-\n06", "3"),
    ("Датчик Panasonic PM\n-L45-P", "12"),
    ("Датчик SENVIEW\nsr3s-a5-na", "6"),
    ("Программируемый логический контроллер xinje yd3-60t-e", "1"),
    ("Блок питания lrs-350-48", "3"),
    ("Блок питания lrs-150-24", "3"),
    ("Держатель плавких вставок CHINT rt28n-32x", "3"),
    ("Реле DPD 24VDC RCM2LB2BD", "6"),
    ("Кулер SXD12038B2LM SXD00L", "6"),
]


def layout_pdf(*, pages=3, background=False, repeated_header=False) -> bytes:
    document = pymupdf.open()
    xs = [30, 210, 275, 650, 785, 940]
    for number in range(pages):
        page = document.new_page(width=970, height=780)
        if background:
            watermark = pymupdf.Pixmap(pymupdf.csRGB, (0, 0, 2, 2), False)
            watermark.clear_with(250)
            page.insert_image(page.rect, stream=watermark.tobytes("png"), overlay=False)
        rows = ([HEADER] if number == 0 or repeated_header else []) + [
            [EQUIPMENT if index == 0 and number == 0 else "", quantity, name, "15000", "30000"]
            for index, (name, quantity) in enumerate(PARTS)
        ]
        top, height = 45, 61
        header_rows = int(number == 0 or repeated_header)
        bottom = top + height * len(rows)
        for x in xs:
            page.draw_line((x, top), (x, bottom), width=0.5)
        for index in range(len(rows) + 1):
            left = xs[0] if index in {0, header_rows, len(rows)} else xs[1]
            page.draw_line((left, top + index * height), (xs[-1], top + index * height), width=0.5)
        for row_index, values in enumerate(rows):
            for col_index, value in enumerate(values):
                if not value:
                    continue
                y = top + row_index * height
                cell_bottom = bottom if col_index == 0 and row_index >= header_rows else y + height
                rect = pymupdf.Rect(xs[col_index] + 4, y + 4, xs[col_index + 1] - 4, cell_bottom - 4)
                page.insert_htmlbox(rect, '<div style="font-size:11px">' + value.replace("\n", "<br>") + "</div>")
    content = document.tobytes(deflate=True)
    document.close()
    return content


def output_rows(content):
    table = Document(io.BytesIO(content)).tables[0]
    headers = [cell.text for cell in table.rows[0].cells]
    return headers, [[cell.text for cell in row.cells] for row in table.rows[1:]]


def test_wrapped_headers_and_merged_equipment_are_preserved():
    rows = [HEADER] + [[EQUIPMENT if index == 0 else None, quantity, name, "15000", "30000"]
                       for index, (name, quantity) in enumerate(PARTS)]
    items = parser.parse_rows(rows)
    assert len(items) == len(PARTS)
    assert [item["quantity"] for item in items] == [quantity for _, quantity in PARTS]
    assert all(item["equipment"] == EQUIPMENT for item in items)
    assert items[1]["name"].endswith("4V210-06")
    assert items[2]["name"].endswith("PM-L45-P")


def test_header_ocr_confusables_do_not_change_part_codes():
    header = ["Оборудование", "Кол-\nBO", "Наименование запасной части", "Цена", "Сумма"]
    items = parser.parse_rows([header, [EQUIPMENT, "3", "CNHT NXB-63 10", "15000", "45000"]])
    assert items[0]["quantity"] == "3"
    assert items[0]["name"] == "CNHT NXB-63 10"


def test_native_word_wraps_join_only_short_non_function_fragments():
    assert parser._clean("Пневмораспределите\nль электрический") == "Пневмораспределитель электрический"
    assert parser._clean("Выключатель\nдля станка") == "Выключатель для станка"


def test_leading_page_fragment_joins_previous_item_instead_of_losing_quantity():
    state = parser.TableState(columns={0: "equipment", 1: "quantity", 2: "name", 3: "excluded", 4: "excluded"},
                              width=5, equipment=EQUIPMENT)
    items = parser.parse_rows([[None, None, "Meanwell LRS-350-\n24", None, None],
                               [None, "4", "Серводрайвер ELD5-400", "15000", "60000"]], state=state, continuation=True)
    assert state.leading_name == "Meanwell LRS-350-24"
    assert len(items) == 1
    assert items[0]["quantity"] == "4"


def test_total_row_is_not_treated_as_equipment():
    items = parser.parse_rows([HEADER, [EQUIPMENT, "3", "Реле", "15000", "45000"],
                               ["Итого с НДС 22% 45000 руб.", None, None, None, None]])
    assert len(items) == 1


def test_missing_quantity_with_financial_cells_is_not_a_line_wrap():
    state = parser.TableState(columns={0: "equipment", 1: "quantity", 2: "name", 3: "excluded", 4: "excluded"},
                              width=5, equipment=EQUIPMENT)
    with pytest.raises(parser.ParseError, match="количество"):
        parser.parse_rows([[None, None, "Продолжение модели", None, None],
                           [None, "4", "Серводрайвер", "15000", "60000"],
                           [None, None, "Новая позиция", "15000", "60000"]], state=state, continuation=True)


@pytest.mark.parametrize("repeated_header", [False, True])
def test_pdf_extracts_every_page_and_carries_merged_equipment(repeated_header):
    content, count, used_ocr = parser.extract_documents([("spare-parts.pdf", layout_pdf(repeated_header=repeated_header))])
    headers, rows = output_rows(content)
    assert count == 3 * len(PARTS)
    assert not used_ocr
    assert [row[1] for row in rows] == [quantity for _, quantity in PARTS] * 3
    equipment_index = headers.index("Оборудование / объект")
    assert all(row[equipment_index] == EQUIPMENT for row in rows)
    assert all("15000" not in cell and "30000" not in cell for row in rows for cell in row)


def test_incompatible_continuation_is_rejected_instead_of_silently_omitted():
    state = parser.TableState()
    with pymupdf.open(stream=layout_pdf(pages=2), filetype="pdf") as source:
        parser._page_items(source[0], state=state, page_number=0)
        state.edges = tuple(edge + 0.1 for edge in state.edges)
        with pytest.raises(parser.ParseError, match="продолжение таблицы"):
            parser._page_items(source[1], state=state, page_number=1)


def test_background_image_never_forces_ocr_over_valid_pdf_text(monkeypatch):
    def no_ocr(*args, **kwargs):
        raise AssertionError("Source text was unnecessarily sent to OCR")

    monkeypatch.setattr(parser, "_recognize_page", no_ocr)
    content, count, used_ocr = parser.extract_documents([("background.pdf", layout_pdf(pages=1, background=True))])
    _, rows = output_rows(content)
    assert count == len(PARTS)
    assert not used_ocr
    assert rows[1][0].endswith("AIRTAC 4V 4V210-06")
    assert rows[2][0].endswith("Panasonic PM-L45-P")


def test_visible_grid_fallback_keeps_native_text(monkeypatch):
    original = parser._page_items

    def with_overlapping_paths(page, **kwargs):
        if kwargs.get("boxes") is None:
            raise parser.ParseError("В строке спецификации не определено количество.")
        return original(page, **kwargs)

    monkeypatch.setattr(parser, "_page_items", with_overlapping_paths)
    content, count, used_ocr = parser.extract_documents([("grid.pdf", layout_pdf(pages=1))])
    _, rows = output_rows(content)
    assert count == len(PARTS)
    assert not used_ocr
    assert rows[2][0].endswith("Panasonic PM-L45-P")


def test_scanned_continuation_keeps_rows_and_quantities():
    if not shutil.which("tesseract"):
        pytest.skip("Для повторного чтения сложных количеств нужен Tesseract CLI; проверяется в Docker")
    try:
        tessdata = Path(pymupdf.get_tessdata())
    except RuntimeError:
        pytest.skip("Нужны локальные пакеты OCR")
    if not all((tessdata / f"{language}.traineddata").exists() for language in ("rus", "eng")):
        pytest.skip("Нужны локальные пакеты rus/eng")
    with pymupdf.open(stream=layout_pdf(pages=2), filetype="pdf") as source, pymupdf.open() as scanned:
        for page in source:
            target = scanned.new_page(width=page.rect.width, height=page.rect.height)
            target.insert_image(target.rect, stream=page.get_pixmap(dpi=200).tobytes("jpeg"))
        data = scanned.tobytes(deflate=True)
    content, count, used_ocr = parser.extract_documents([("scanned.pdf", data)])
    headers, rows = output_rows(content)
    assert used_ocr
    assert count == 2 * len(PARTS)
    assert [row[1] for row in rows] == [quantity for _, quantity in PARTS] * 2
    assert all(row[headers.index("Оборудование / объект")] for row in rows)


def test_docx_preserves_vertical_equipment_merge():
    document = Document()
    table = document.add_table(rows=0, cols=5)
    for values in [HEADER] + [[EQUIPMENT if index == 0 else "", quantity, name, "15000", "30000"]
                              for index, (name, quantity) in enumerate(PARTS)]:
        for cell, value in zip(table.add_row().cells, values):
            cell.text = value
    table.cell(1, 0).merge(table.cell(len(PARTS), 0))
    source = io.BytesIO()
    document.save(source)
    content, count, _ = parser.extract_documents([("source.docx", source.getvalue())])
    headers, rows = output_rows(content)
    assert count == len(PARTS)
    assert all(row[headers.index("Оборудование / объект")] == EQUIPMENT for row in rows)


def test_xlsx_preserves_vertical_equipment_merge():
    workbook = Workbook()
    for row in [HEADER] + [[EQUIPMENT if index == 0 else None, quantity, name, 15000, 30000]
                          for index, (name, quantity) in enumerate(PARTS)]:
        workbook.active.append(row)
    workbook.active.merge_cells(start_row=2, start_column=1, end_row=len(PARTS) + 1, end_column=1)
    source = io.BytesIO()
    workbook.save(source)
    content, count, _ = parser.extract_documents([("source.xlsx", source.getvalue())])
    headers, rows = output_rows(content)
    assert count == len(PARTS)
    assert all(row[headers.index("Оборудование / объект")] == EQUIPMENT for row in rows)
