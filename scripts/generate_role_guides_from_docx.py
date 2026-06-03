# -*- coding: utf-8 -*-
"""Generate web/src/shared/content/roleGuides.ts from Reorganized-user-guide.docx."""
from __future__ import annotations

import json
import re
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[1]
DOCX = Path(r"c:\Users\alexonderia\Downloads\Reorganized-user-guide.docx")
OUTPUT = ROOT / "web/src/shared/content/roleGuides.ts"
DEBUG_JSON = ROOT / "docs/reports/role-guides-from-docx.json"

NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": NS_W}

ROLE_MAP: list[tuple[str, str, str]] = [
    ("CONTRACTOR", "Памятка пользователя (контрагент)", "Памятка контрагента"),
    ("OPERATOR", "Памятка оператора", "Памятка оператора"),
    ("ECONOMIST", "Памятка экономиста", "Памятка экономиста"),
    ("LEAD_ECONOMIST", "Памятка ведущего экономиста", "Памятка ведущего экономиста"),
    ("PROJECT_MANAGER", "Памятка руководителя проекта", "Памятка руководителя проекта"),
    ("ADMIN", "Памятка администратора", "Памятка администратора"),
    ("SUPERADMIN", "Памятка суперадмина", "Памятка суперадмина"),
]

SECTION_RE = re.compile(r"^\d+\.\s+.+")
ROLE_TITLE_RE = re.compile(r"^Памятка\s")


def escape_ts(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'").replace("\r\n", "\n").replace("\n", "\\n")


def iter_blocks(document: Document):
    body = document.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            yield ("p", Paragraph(child, document))
        elif child.tag == qn("w:tbl"):
            yield ("tbl", Table(child, document))


def runs_to_markdown(paragraph: Paragraph) -> str:
    chunks: list[str] = []
    for run in paragraph.runs:
        text = run.text
        if not text:
            continue
        if run.bold:
            chunks.append(f"**{text}**")
        else:
            chunks.append(text)
    merged = "".join(chunks)
    merged = re.sub(r"\*\*\s*→\s*\*\*", " → ", merged)
    merged = re.sub(r"\*\*\s+\*\*", " ", merged)
    merged = re.sub(r"(?<=[а-яА-ЯёЁa-zA-Z0-9:])(\*\*)", r" \1", merged)
    merged = re.sub(r"(\*\*)(?=[«А-ЯA-ZЁ])", r"\1 ", merged)
    merged = re.sub(r"\*\* +", "**", merged)
    merged = re.sub(r" +\*\*([.,;!?]|$)", r"**\1", merged)
    merged = re.sub(r"  +", " ", merged)
    merged = re.sub(r"(\*\*){3,}", "**", merged)
    return merged.strip()


def paragraph_text(paragraph: Paragraph) -> str:
    style = paragraph_style(paragraph)
    if style in ("Heading 2", "Heading 3"):
        return paragraph.text.strip()
    return runs_to_markdown(paragraph)


def list_num_id(paragraph: Paragraph) -> int | None:
    p_pr = paragraph._p.pPr
    if p_pr is None or p_pr.numPr is None:
        return None
    return int(p_pr.numPr.numId.val)


def list_is_ordered(document: Document, paragraph: Paragraph) -> bool:
    num_id = list_num_id(paragraph)
    if num_id is None:
        return False

    numbering = document.part.numbering_part
    if numbering is None:
        return True

    root = numbering.element
    abstract_id: int | None = None
    for num in root.findall("w:num", NS):
        if int(num.get(f"{{{NS_W}}}numId")) != num_id:
            continue
        abstract = num.find("w:abstractNumId", NS)
        if abstract is not None:
            abstract_id = int(abstract.get(f"{{{NS_W}}}val"))
        break

    if abstract_id is None:
        return True

    for abs_num in root.findall("w:abstractNum", NS):
        if int(abs_num.get(f"{{{NS_W}}}abstractNumId")) != abstract_id:
            continue
        lvl = abs_num.find("w:lvl", NS)
        if lvl is None:
            return True
        fmt = lvl.find("w:numFmt", NS)
        if fmt is None:
            return True
        return fmt.get(f"{{{NS_W}}}val") != "bullet"

    return True


def is_list_paragraph(paragraph: Paragraph) -> bool:
    if list_num_id(paragraph) is not None:
        return True
    style = paragraph.style.name if paragraph.style else ""
    return style == "Compact"


def table_to_block(table: Table) -> dict:
    rows: list[list[str]] = []
    for row in table.rows:
        cells: list[str] = []
        for cell in row.cells:
            parts = [runs_to_markdown(p) for p in cell.paragraphs if p.text.strip()]
            cells.append(" ".join(parts).strip())
        rows.append(cells)

    if not rows:
        return {"type": "table", "headers": [], "rows": []}

    return {"type": "table", "headers": rows[0], "rows": rows[1:]}


def paragraph_style(paragraph: Paragraph) -> str:
    return paragraph.style.name if paragraph.style else ""


def parse_document(document: Document) -> dict[str, dict]:
    roles: dict[str, dict] = {}
    current_key: str | None = None
    current_section: dict | None = None
    summary_lines: list[str] = []
    pending_list: dict | None = None

    def flush_list() -> None:
        nonlocal pending_list
        if pending_list and current_section is not None:
            current_section["blocks"].append(pending_list)
        pending_list = None

    def flush_section() -> None:
        nonlocal current_section
        flush_list()
        current_section = None

    def start_role(key: str, ui_title: str) -> None:
        nonlocal current_key, summary_lines
        flush_section()
        current_key = key
        summary_lines = []
        roles[key] = {"title": ui_title, "summary": [], "sections": []}

    def start_section(title: str) -> None:
        nonlocal current_section
        flush_section()
        if current_key is None:
            return
        current_section = {"title": title, "blocks": []}
        roles[current_key]["sections"].append(current_section)

    def append_block(block: dict) -> None:
        if current_section is None:
            return
        current_section["blocks"].append(block)

    def append_summary(text: str) -> None:
        if current_key is not None:
            roles[current_key]["summary"].append(text)

    for kind, block in iter_blocks(document):
        if kind == "tbl":
            flush_list()
            if current_section is not None:
                append_block(table_to_block(block))
            continue

        paragraph: Paragraph = block
        text = paragraph_text(paragraph)
        if not text:
            continue

        style = paragraph_style(paragraph)

        if style == "Heading 1" and ROLE_TITLE_RE.match(text):
            matched = next(((k, ui) for k, marker, ui in ROLE_MAP if marker == text), None)
            if matched:
                start_role(matched[0], matched[1])
            continue

        if current_key is None:
            continue

        if style == "Heading 2" and SECTION_RE.match(text):
            start_section(text)
            continue

        if current_section is None:
            if style in ("First Paragraph", "Body Text", "Normal"):
                append_summary(text)
            continue

        if is_list_paragraph(paragraph):
            ordered = list_is_ordered(document, paragraph)
            if pending_list and pending_list.get("ordered") == ordered:
                pending_list["items"].append(text)
            else:
                flush_list()
                pending_list = {"type": "list", "ordered": ordered, "items": [text]}
            continue

        flush_list()

        if style == "Heading 3":
            append_block({"type": "subheading", "text": text})
            continue

        append_block({"type": "paragraph", "text": text})

    flush_section()

    for key, _, _ in ROLE_MAP:
        if key in roles:
            roles[key]["summary"] = "\n\n".join(roles[key]["summary"])

    return roles


def emit_block(block: dict, indent: str) -> list[str]:
    block_type = block["type"]
    lines: list[str] = [f"{indent}{{ type: '{block_type}',"]

    if block_type == "paragraph":
        lines.append(f"{indent}    text: '{escape_ts(block['text'])}'")
    elif block_type == "subheading":
        lines.append(f"{indent}    text: '{escape_ts(block['text'])}'")
    elif block_type == "list":
        lines.append(f"{indent}    ordered: {'true' if block['ordered'] else 'false'},")
        lines.append(f"{indent}    items: [")
        for item in block["items"]:
            lines.append(f"{indent}        '{escape_ts(item)}',")
        lines.append(f"{indent}    ]")
    elif block_type == "table":
        header_cells = ", ".join(f"'{escape_ts(h)}'" for h in block["headers"])
        lines.append(f"{indent}    headers: [{header_cells}],")
        lines.append(f"{indent}    rows: [")
        for row in block["rows"]:
            cells = ", ".join(f"'{escape_ts(cell)}'" for cell in row)
            lines.append(f"{indent}        [{cells}],")
        lines.append(f"{indent}    ]")
    else:
        raise ValueError(f"Unknown block type: {block_type}")

    lines.append(f"{indent}}}")
    return lines


def emit_ts(roles: dict[str, dict]) -> str:
    lines = [
        "import { ROLE } from '@shared/constants/roles';",
        "",
        "export type GuideTableBlock = {",
        "    type: 'table';",
        "    headers: string[];",
        "    rows: string[][];",
        "};",
        "",
        "export type GuideListBlock = {",
        "    type: 'list';",
        "    ordered: boolean;",
        "    items: string[];",
        "};",
        "",
        "export type GuideTextBlock = {",
        "    type: 'paragraph' | 'subheading';",
        "    text: string;",
        "};",
        "",
        "export type GuideBlock = GuideTextBlock | GuideListBlock | GuideTableBlock;",
        "",
        "export type GuideSection = {",
        "    title: string;",
        "    blocks: GuideBlock[];",
        "};",
        "",
        "export type GuideRole = {",
        "    title: string;",
        "    summary: string;",
        "    sections: GuideSection[];",
        "};",
        "",
        "export const roleGuides: Record<number, GuideRole> = {",
    ]

    for key, _, ui_title in ROLE_MAP:
        data = roles[key]
        lines.append(f"    [ROLE.{key}]: {{")
        lines.append(f"        title: '{escape_ts(ui_title)}',")
        lines.append(f"        summary: '{escape_ts(data['summary'])}',")
        lines.append("        sections: [")
        for section in data["sections"]:
            lines.append("            {")
            lines.append(f"                title: '{escape_ts(section['title'])}',")
            lines.append("                blocks: [")
            for block in section["blocks"]:
                block_lines = emit_block(block, "                    ")
                block_lines[-1] = block_lines[-1] + ","
                lines.extend(block_lines)
            lines.append("                ]")
            lines.append("            },")
        lines.append("        ]")
        lines.append("    },")
        lines.append("")

    lines.append("};")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    if not DOCX.exists():
        raise FileNotFoundError(DOCX)

    document = Document(DOCX)
    roles = parse_document(document)

    DEBUG_JSON.parent.mkdir(parents=True, exist_ok=True)
    DEBUG_JSON.write_text(json.dumps(roles, ensure_ascii=False, indent=2), encoding="utf-8")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(emit_ts(roles), encoding="utf-8")

    print(f"Wrote {OUTPUT}")
    for key, _, title in ROLE_MAP:
        sections = roles[key]["sections"]
        blocks = sum(len(s["blocks"]) for s in sections)
        print(f"  {title}: {len(sections)} sections, {blocks} blocks")


if __name__ == "__main__":
    main()
