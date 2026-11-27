"""Local, bounded document parser. This module also runs as an isolated child process."""
from __future__ import annotations

import base64
from copy import deepcopy
from contextlib import redirect_stdout
from dataclasses import dataclass, field
import io
import json
import math
import os
from pathlib import Path
import re
import sys
import shutil
import subprocess

MAX_PAGES = 40
MAX_ROWS = 2000
MAX_CELLS = 60000
MAX_ITEMS = 1000
UNCACHED_FORMULA = "\x00uncached-formula\x00"
FIELDS = ("name", "quantity", "unit", "equipment", "article", "description")
LABELS = ("Наименование товара, работы или услуги", "Количество", "Ед. изм.", "Оборудование / объект", "Артикул / модель", "Характеристики и комплектность")
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
SENSITIVE = re.compile(
    r"[₽$€]|\b(?:руб(?:\.|ль|ля|лей)?|RUB|USD|EUR|НДС|ИНН|КПП|ОГРН|БИК)\b"
    r"|\b(?:цен[аыу]|стоимость|оплат[аыу]|предоплат[аыу]|поставщик|покупатель|продавец)\b"
    r"|\b(?:договор|контракт)\s*(?:№|номер)|\b(?:ООО|ПАО|ОАО|ЗАО)\b"
    r"|[\w.+-]+@[\w.-]+\.[a-zа-я]{2,}|\b[рк]\s*/\s*с\b|\+7[\s(\d]",
    re.IGNORECASE,
)


class ParseError(ValueError):
    """Safe, user-facing parsing failure."""


@dataclass
class TableState:
    columns: dict[int, str] = field(default_factory=dict)
    width: int = 0
    equipment: str = ""
    edges: tuple[float, ...] = ()
    page: int = -1
    leading_name: str = ""

    def replace_from(self, other: TableState) -> None:
        self.columns = other.columns.copy()
        self.width = other.width
        self.equipment = other.equipment
        self.edges = other.edges
        self.page = other.page
        self.leading_name = other.leading_name


def _clean(value: object) -> str:
    text = str(value if value is not None else "").replace("\u00ad", "")
    # Join explicit line wraps without changing model spelling or punctuation.
    text = re.sub(r"(?<=[а-яё])[-‐‑]\s*\n\s*(?=[а-яё])", "", text)
    text = re.sub(r"(?<=[A-Za-z0-9])[-‐‑]\s*\n\s*(?=[A-Za-z0-9])", "-", text)
    text = re.sub(r"(?<=[A-Za-z0-9])\s*\n\s*(?=-[A-Za-z0-9])", "", text)
    function_words = {"и", "в", "во", "на", "для", "из", "по", "с", "со", "от", "до", "за", "к", "ко", "у", "не", "без", "под", "при", "над", "или"}
    text = re.sub(r"([А-ЯЁа-яё]{5,})[ \t]*\n[ \t]*([а-яё]{1,3})(?=\s|$)",
                  lambda match: match[1] + (" " if match[2] in function_words else "") + match[2], text)
    return re.sub(r"\s+", " ", text).strip()


def _kind(value: object) -> str | None:
    text = _clean(value).casefold().replace("ё", "е")
    compact = re.sub(r"[^a-zа-я0-9]", "", text)
    quantity_key = compact.translate(str.maketrans({"b": "в", "o": "о", "k": "к", "l": "л"}))
    if re.search(r"цен|стоим|сумм|ндс|налог|валют|скид|реквизит|инн|кпп|банк|подпис|поставщик|покупател|продавец", text):
        return "excluded"
    if re.search(r"оборудован|^объект|^узел|^агрегат|^группа", compact):
        return "equipment"
    if re.search(r"наименован|номенклатур|название", compact):
        return "name"
    if re.search(r"колич|колво|объем|^кол$", quantity_key) or compact in {"qty", "quantity"}:
        return "quantity"
    if re.search(r"едизм|единиц|^ед$", compact):
        return "unit"
    if re.search(r"артикул|модель|маркировк", text):
        return "article"
    if re.search(r"характерист|техническ|комплект|параметр|описание|состав работ", text):
        return "description"
    return None


def _header(values: list[str]) -> dict[int, str]:
    columns = {index: kind for index, value in enumerate(values) if (kind := _kind(value))}
    # In equipment-only procurement the equipment itself is the item.
    if "name" not in columns.values() and "equipment" in columns.values() and "quantity" in columns.values():
        columns = {index: "name" if kind == "equipment" else kind for index, kind in columns.items()}
    if "name" not in columns.values() or len(columns) < 2:
        return {}
    # A data row mentioning a product name is not a column header.
    if any(re.search(r"\d", value) for value in values):
        return {}
    return columns


def parse_rows(rows: list[list[object]], *, state: TableState | None = None, continuation: bool = False) -> list[dict[str, str]]:
    """Select columns by meaning. Unknown and financial columns never reach output."""
    if len(rows) > MAX_ROWS or sum(len(row) for row in rows) > MAX_CELLS:
        raise ParseError("В документе слишком большая таблица. Разделите файл на части.")
    state = state if state is not None else TableState()
    mapping = state.columns.copy() if continuation else {}
    items: list[dict[str, str]] = []
    for row in rows:
        values = [_clean(value) for value in row]
        first_value = next((value for value in values if value), "")
        if re.match(r"^(?:итого|всего|общая\s+(?:сумма|цена)|в том числе)\b", first_value, re.I):
            continue
        kinds = {index: kind for index, value in enumerate(values) if (kind := _kind(value))}
        header = _header(values)
        if header:
            if header != state.columns or len(values) != state.width:
                state.equipment = ""
            mapping = state.columns = header
            state.width = len(values)
            continue
        if not mapping:
            continue
        # A second header tier may supply units or quantities below merged cells.
        if kinds and not any(re.search(r"\d", value) for value in values) and all(
            not value or index in kinds or value in {"№", "п/п"} for index, value in enumerate(values)
        ):
            mapping.update(kinds)
            continue
        item = {key: "" for key in FIELDS}
        for index, kind in mapping.items():
            if kind in item and index < len(values) and values[index]:
                if values[index] == UNCACHED_FORMULA:
                    raise ParseError("В XLSX нет сохранённого результата формулы. Пересчитайте и сохраните книгу перед загрузкой.")
                item[kind] = " ".join(filter(None, (item[kind], values[index])))
        name = item["name"]
        if not name and item["equipment"] and not any(item[key] for key in FIELDS if key != "equipment"):
            if SENSITIVE.search(item["equipment"]):
                raise ParseError("В описании оборудования найдены цены или реквизиты. Проверьте исходную таблицу.")
            state.equipment = item["equipment"]
            continue
        if not name or re.match(r"^(?:итого|всего|общая\s+(?:сумма|цена)|в том числе)\b", name, re.I):
            continue
        if not any(char.isalpha() for char in name):
            continue
        if "quantity" in mapping.values() and not item["quantity"]:
            excluded_values = [values[index] for index, kind in mapping.items() if kind == "excluded" and index < len(values)]
            if (continuation and not items and not any(excluded_values)
                    and not any(item[key] for key in ("unit", "article", "description"))
                    and (not item["equipment"] or item["equipment"] == state.equipment)):
                if SENSITIVE.search(name):
                    raise ParseError("В продолжении позиции найдены цены или реквизиты. Проверьте исходную таблицу.")
                state.leading_name = "\n".join(filter(None, (state.leading_name, name)))
                continue
            raise ParseError("В строке спецификации не определено количество. Проверьте исходную таблицу.")
        if any(len(value) > 3000 for value in item.values()):
            raise ParseError("Слишком длинное описание позиции. Подготовьте отдельную таблицу спецификации.")
        if any(SENSITIVE.search(value) for value in item.values()):
            raise ParseError("В описании позиций найдены цены или реквизиты. Подготовьте таблицу с отдельными столбцами для этих данных.")
        if item["quantity"] and not re.fullmatch(r"\d[\d\s]*(?:[.,]\d+)?", item["quantity"]):
            raise ParseError("Не удалось однозначно определить количество. Проверьте таблицу спецификации.")
        if "equipment" in mapping.values():
            if item["equipment"]:
                state.equipment = item["equipment"]
            else:
                item["equipment"] = state.equipment
        items.append(item)
        if len(items) > MAX_ITEMS:
            raise ParseError("В спецификации слишком много позиций. Разделите файл на части.")
    return items


def _docx_tables(content: bytes) -> list[list[list[object]]]:
    from docx import Document

    document = Document(io.BytesIO(content))
    return [[[cell.text for cell in row.cells] for row in table.rows] for table in document.tables]


def _xlsx_tables(content: bytes) -> list[list[list[object]]]:
    from openpyxl import load_workbook

    workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True, keep_links=False)
    formulas = load_workbook(io.BytesIO(content), read_only=True, data_only=False, keep_links=False)
    try:
        tables = []
        total = 0
        for sheet in workbook:
            if sheet.sheet_state != "visible":
                continue
            if sheet.max_row > MAX_ROWS or sheet.max_column > 60:
                raise ParseError("Лист XLSX слишком большой. Оставьте в файле таблицу спецификации.")
            rows = [list(row) for row in sheet.iter_rows(values_only=True)]
            for values, raw_row in zip(rows, formulas[sheet.title].iter_rows(values_only=True)):
                for index, raw in enumerate(raw_row):
                    if isinstance(raw, str) and raw.startswith("=") and values[index] is None:
                        values[index] = UNCACHED_FORMULA
            total += sum(len(row) for row in rows)
            if total > MAX_CELLS:
                raise ParseError("В XLSX слишком много ячеек. Разделите файл на части.")
            tables.append(rows)
        return tables
    finally:
        workbook.close()
        formulas.close()


def _table_edges(table, page) -> tuple[float, ...]:
    edges = sorted({round(float(cell[index]) / page.rect.width, 4)
                    for row in table.rows for cell in row.cells if cell is not None for index in (0, 2)})
    return tuple(edges)


def _page_items(page, *, lines=None, boxes=None, state: TableState | None = None, page_number: int = 0,
                quantity_reader=None) -> list[dict[str, str]]:
    state = state if state is not None else TableState()
    errors = []
    ruling_options = {"add_lines": lines}
    if boxes is not None:
        ruling_options.update(paths=[], add_boxes=boxes)
    for options in (ruling_options, {"strategy": "text", "min_words_vertical": 1, "min_words_horizontal": 1}):
        tables = page.find_tables(**options)
        result = []
        candidate_state = deepcopy(state)
        failed = False
        for table in tables.tables:
            rows = table.extract()
            has_header = any(_header([_clean(value) for value in row]) for row in rows)
            edges = _table_edges(table, page)
            continuation = (bool(candidate_state.columns) and candidate_state.page == page_number - 1
                and table.col_count == candidate_state.width and len(edges) == len(candidate_state.edges)
                and all(abs(left - right) <= 0.012 for left, right in zip(edges, candidate_state.edges)))
            if not has_header and not continuation:
                name_indices = [index for index, kind in candidate_state.columns.items() if kind == "name"]
                quantity_indices = [index for index, kind in candidate_state.columns.items() if kind == "quantity"]
                if (candidate_state.page == page_number - 1 and table.col_count == candidate_state.width
                        and name_indices and quantity_indices and any(
                            _clean(row[quantity_indices[0]]).isdigit() and any(char.isalpha() for char in _clean(row[name_indices[0]]))
                            for row in rows)):
                    errors.append(ParseError("Не удалось однозначно связать продолжение таблицы со следующей страницей. Проверьте её заголовки."))
                    failed = True
                    break
                continue
            if quantity_reader is not None:
                columns = candidate_state.columns.copy() if continuation else {}
                for row, geometry in zip(rows, table.rows):
                    header = _header([_clean(value) for value in row])
                    if header:
                        columns = header
                        continue
                    for index, kind in columns.items():
                        if kind != "quantity" or index >= len(row):
                            continue
                        quantity = _clean(row[index])
                        if quantity and not re.fullmatch(r"\d[\d\s]*(?:[.,]\d+)?", quantity) and geometry.cells[index]:
                            recognized = quantity_reader(geometry.cells[index])
                            if recognized:
                                row[index] = recognized
            try:
                items = parse_rows(rows, state=candidate_state, continuation=continuation and not has_header)
            except ParseError as exc:
                errors.append(exc)
                result = []
                failed = True
                break
            if items or candidate_state.leading_name:
                result.extend(items)
                candidate_state.edges = edges
                candidate_state.page = page_number
        if not failed and (result or candidate_state.leading_name):
            state.replace_from(candidate_state)
            return result
    if errors:
        raise errors[0]
    return []


def _raster_grid(page, *, dpi: int | None = None):
    import cv2
    import numpy as np
    import pymupdf

    cv2.setNumThreads(1)
    # Small spare-part labels need more detail than a 200 dpi page render.
    # Bound pixels as well as DPI so unusually large pages stay within the worker budget.
    dpi = dpi or min(300, max(72, int(72 * math.sqrt(16_000_000 / page.rect.get_area()))))
    pixmap = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB, alpha=False)
    rgb = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width, 3).copy()
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, np.ones((1, max(40, pixmap.width // 20)), np.uint8))
    vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, np.ones((max(40, pixmap.height // 20), 1), np.uint8))
    lines = []
    scale = 72 / dpi
    for mask, is_horizontal in ((horizontal, True), (vertical, False)):
        contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
        for contour in contours:
            x, y, width, height = cv2.boundingRect(contour)
            start = (x * scale, (y + height / 2) * scale) if is_horizontal else ((x + width / 2) * scale, y * scale)
            end = ((x + width) * scale, start[1]) if is_horizontal else (start[0], (y + height) * scale)
            lines.append((start, end))
    return rgb, horizontal, vertical, lines, dpi


def _recognize_page(page, *, state: TableState | None = None, page_number: int = 0) -> list[dict[str, str]]:
    import cv2
    import numpy as np
    import pymupdf

    rgb, horizontal, vertical, lines, dpi = _raster_grid(page)
    # Remove raster rules before OCR; restore their geometry for table extraction.
    rules = cv2.dilate(cv2.bitwise_or(horizontal, vertical), np.ones((3, 3), np.uint8))
    rgb[rules > 0] = 255
    cleaned = pymupdf.Pixmap(pymupdf.csRGB, rgb.shape[1], rgb.shape[0], rgb.tobytes(), False)
    cleaned.set_dpi(dpi, dpi)
    searchable = cleaned.pdfocr_tobytes(language="rus+eng", tessdata=os.environ.get("TESSDATA_PREFIX"))
    def quantity_reader(rect):
        executable = shutil.which("tesseract")
        if not executable:
            return None
        scale = dpi / 72
        x0, y0, x1, y1 = rect
        crop = rgb[max(0, int(y0 * scale)):min(rgb.shape[0], int(y1 * scale)),
                   max(0, int(x0 * scale)):min(rgb.shape[1], int(x1 * scale))]
        if not crop.size:
            return None
        binary = cv2.threshold(cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY), 0, 255,
                               cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        binary = cv2.copyMakeBorder(binary, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=255)
        image = cv2.imencode(".png", binary)[1].tobytes()
        readings = []
        try:
            for language in ("eng", "rus"):
                result = subprocess.run([executable, "stdin", "stdout", "-l", language, "--psm", "6", "-c",
                                         "tessedit_char_whitelist=0123456789.,"], input=image, capture_output=True,
                                        timeout=5, check=True)
                readings.append(_clean(result.stdout.decode("utf-8")))
        except (OSError, subprocess.SubprocessError):
            return None
        value = readings[0]
        return value if readings[1] == value and re.fullmatch(r"\d[\d\s]*(?:[.,]\d+)?", value) else None
    with pymupdf.open(stream=searchable, filetype="pdf") as recognized:
        return _page_items(recognized[0], lines=lines, state=state, page_number=page_number, quantity_reader=quantity_reader)


def _pdf_items(content: bytes, *, image: bool = False) -> tuple[list[dict[str, str]], bool]:
    import pymupdf

    used_ocr = False
    items = []
    state = TableState()
    with pymupdf.open(stream=content) as source:
        pdf_bytes = source.convert_to_pdf() if image else content
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as document:
        if len(document) > MAX_PAGES:
            raise ParseError(f"Документ содержит больше {MAX_PAGES} страниц. Разделите файл на части.")
        for page_number, page in enumerate(document):
            if page.rect.width * page.rect.height > 4_000_000:
                raise ParseError("Слишком большой размер страницы. Сохраните документ в обычном формате A4/A3.")
            state.leading_name = ""
            try:
                page_items = _page_items(page, state=state, page_number=page_number)
            except ParseError as native_error:
                # Some PDF generators leave overlapping, invisible grid paths.
                # Recover the visible grid while keeping the original text layer.
                boxes = [tuple(table.bbox) for table in page.find_tables().tables]
                _, _, _, visible_lines, _ = _raster_grid(page, dpi=200)
                page_items = _page_items(page, lines=visible_lines, boxes=boxes, state=state, page_number=page_number)
                if not page_items and not state.leading_name:
                    raise native_error
            has_large_image = any(
                pymupdf.Rect(info["bbox"]).get_area() > page.rect.get_area() * 0.2
                for info in page.get_image_info()
            )
            # A watermark / background image must never replace usable source text.
            if not page_items and not state.leading_name and (has_large_image or not page.get_text().strip()):
                try:
                    recognized_items = _recognize_page(page, state=state, page_number=page_number)
                    if recognized_items:
                        page_items = recognized_items
                        used_ocr = True
                except ParseError:
                    raise
                except Exception as exc:
                    raise ParseError("Не удалось распознать скан. Попробуйте позже или загрузите исходный DOCX/XLSX.") from exc
            if state.leading_name:
                if not items:
                    raise ParseError("Не удалось связать продолжение позиции с предыдущей страницей.")
                items[-1]["name"] = _clean(items[-1]["name"] + "\n" + state.leading_name)
                state.leading_name = ""
            items.extend(page_items)
    return items, used_ocr


def render_specification(items: list[dict[str, str]]) -> bytes:
    from docx import Document
    from docx.enum.section import WD_ORIENT
    from docx.oxml import OxmlElement
    from docx.shared import Mm, Pt

    document = Document()
    document.core_properties.author = ""
    document.core_properties.last_modified_by = ""
    document.core_properties.title = "Заявка на закупку"
    document.core_properties.comments = ""
    style = document.styles["Normal"]
    style.font.name = "Alabuga Sans"
    style.font.size = Pt(10)
    style.paragraph_format.space_after = Pt(0)
    style.paragraph_format.line_spacing = 1.1
    heading = document.add_heading("Заявка на закупку", level=1)
    for run in heading.runs:
        run.font.name = "Alabuga Sans"
        run.font.size = Pt(16)
    active_fields = [key for key in FIELDS if key == "name" or any(item[key] for item in items)]
    section = document.sections[0]
    if len(active_fields) >= 4:
        section.orientation = WD_ORIENT.LANDSCAPE
        section.page_width, section.page_height = Mm(297), Mm(210)
    section.left_margin = section.right_margin = Mm(12)
    section.top_margin = section.bottom_margin = Mm(12)
    table = document.add_table(rows=1, cols=len(active_fields))
    table.style = "Table Grid"
    table.autofit = False
    weights = {"name": 3.5, "quantity": 0.7, "unit": 0.8, "equipment": 2.5, "article": 1.5, "description": 3.0}
    total_weight = sum(weights[key] for key in active_fields)
    width = section.page_width - section.left_margin - section.right_margin
    for column, key in zip(table.columns, active_fields):
        column.width = int(width * weights[key] / total_weight)
    table.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
    for cell, key in zip(table.rows[0].cells, active_fields):
        cell.text = LABELS[FIELDS.index(key)]
        for run in cell.paragraphs[0].runs:
            run.bold = True
    for item in items:
        row = table.add_row()
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for cell, key in zip(row.cells, active_fields):
            cell.text = item[key]
            cell.width = int(width * weights[key] / total_weight)
    result = io.BytesIO()
    document.save(result)
    return result.getvalue()


def extract_documents(documents: list[tuple[str, bytes]]) -> tuple[bytes, int, bool]:
    all_items = []
    used_ocr = False
    for filename, content in documents:
        suffix = Path(filename).suffix.casefold()
        if suffix in {".docx", ".xlsx"}:
            tables = _docx_tables(content) if suffix == ".docx" else _xlsx_tables(content)
            items = [item for table in tables for item in parse_rows(table)]
        elif suffix in {".pdf", ".png", ".jpg", ".jpeg"}:
            items, ocr = _pdf_items(content, image=suffix != ".pdf")
            used_ocr = used_ocr or ocr
        else:
            raise ParseError("Поддерживаются DOCX, XLSX, PDF и сканы PNG/JPEG.")
        if not items:
            raise ParseError("В одном из файлов не найдена таблица товаров или услуг с наименованиями и количеством или характеристиками.")
        all_items.extend(items)
        if len(all_items) > MAX_ITEMS:
            raise ParseError("В спецификации слишком много позиций. Разделите заявку.")
    if not all_items:
        raise ParseError("Прикрепите договор или таблицу спецификации.")
    return render_specification(all_items), len(all_items), used_ocr


def main() -> None:
    if sys.platform != "win32":
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (1024 ** 3, 1024 ** 3))
    try:
        payload = json.loads(sys.stdin.buffer.read(40 * 1024 * 1024))
        documents = [(item["name"], base64.b64decode(item["content"], validate=True)) for item in payload]
        with redirect_stdout(sys.stderr):
            content, count, used_ocr = extract_documents(documents)
        result = {"content": base64.b64encode(content).decode("ascii"), "item_count": count, "used_ocr": used_ocr}
    except ParseError as exc:
        result = {"error": str(exc)}
    except Exception:
        result = {"error": "Не удалось разобрать документ. Проверьте файл и структуру таблицы спецификации."}
    sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))


if __name__ == "__main__":
    main()
