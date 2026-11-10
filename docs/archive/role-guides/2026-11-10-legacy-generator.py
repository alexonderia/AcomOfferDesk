"""Legacy generator from plain-text extract. Prefer generate_role_guides_from_docx.py."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTRACT = ROOT / "docs/reports/reorganized-user-guide-extract.txt"
OUTPUT = ROOT / "web/src/shared/content/roleGuides.ts"

ROLE_SPLITS = [
    ("CONTRACTOR", "Памятка пользователя (контрагент)", "Памятка контрагента"),
    ("OPERATOR", "Памятка оператора", "Памятка оператора"),
    ("ECONOMIST", "Памятка экономиста", "Памятка экономиста"),
    ("LEAD_ECONOMIST", "Памятка ведущего экономиста", "Памятка ведущего экономиста"),
    ("PROJECT_MANAGER", "Памятка руководителя проекта", "Памятка руководителя проекта"),
    ("ADMIN", "Памятка администратора", "Памятка администратора"),
    ("SUPERADMIN", "Памятка суперадмина", "Памятка суперадмина"),
]

SKIP_LINES = {"Раздел", "Что можно делать", "Статус", "Что означает"}
SECTION_RE = re.compile(r"^\d+\.\s+(.+)$")


def escape_ts(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'")


def is_section_start(line: str) -> bool:
    return bool(SECTION_RE.match(line.strip()))


def parse_section_body(lines: list[str]) -> list[str]:
    points: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        if line == "Раздел" and i + 1 < len(lines) and lines[i + 1].strip() == "Что можно делать":
            i += 2
            while i < len(lines) and lines[i].strip() and not is_section_start(lines[i]):
                a = lines[i].strip()
                i += 1
                if a in SKIP_LINES:
                    continue
                if i >= len(lines) or is_section_start(lines[i]):
                    points.append(f"**{a}**")
                    break
                b = lines[i].strip()
                i += 1
                if b in SKIP_LINES:
                    points.append(f"**{a}**")
                else:
                    points.append(f"**{a}** — {b}")
            continue

        if line == "Статус" and i + 1 < len(lines) and lines[i + 1].strip() == "Что означает":
            i += 2
            while i < len(lines) and lines[i].strip() and not is_section_start(lines[i]):
                a = lines[i].strip()
                i += 1
                if a in SKIP_LINES:
                    continue
                if i >= len(lines) or is_section_start(lines[i]):
                    points.append(a)
                    break
                b = lines[i].strip()
                i += 1
                if b not in SKIP_LINES:
                    points.append(f"{a} — {b}")
            continue

        i += 1
        if line.endswith(":") and len(line) < 120:
            points.append(f"**{line.rstrip(':')}:**")
            continue

        # Subsection heading (short title without trailing period)
        if (
            len(line) < 80
            and not line.endswith(".")
            and not line.endswith(":")
            and line[0].isupper()
            and not line.startswith("**")
        ):
            next_line = lines[i].strip() if i < len(lines) else ""
            if next_line and not is_section_start(lines[i]):
                if next_line[0].islower() or next_line.startswith(
                    ("Получите", "Здесь", "После", "Если", "Откройте", "Раздел")
                ):
                    points.append(f"**{line}**")
                    continue

        points.append(line)

    return points


def parse_role_block(block: str) -> tuple[str, list[dict]]:
    raw_lines = block.splitlines()
    lines = [ln for ln in raw_lines if ln.strip()]

    summary_lines: list[str] = []
    idx = 0
    while idx < len(lines) and not is_section_start(lines[idx]):
        summary_lines.append(lines[idx].strip())
        idx += 1
    summary = " ".join(summary_lines)

    sections: list[dict] = []
    while idx < len(lines):
        m = SECTION_RE.match(lines[idx].strip())
        if not m:
            idx += 1
            continue
        title = m.group(1).strip()
        idx += 1
        body: list[str] = []
        while idx < len(lines) and not is_section_start(lines[idx]):
            body.append(lines[idx])
            idx += 1
        points = parse_section_body(body)
        if points:
            sections.append({"title": title, "points": points})

    return summary, sections


def split_roles(text: str) -> dict[str, str]:
    chunks: dict[str, str] = {}
    for i, (key, marker, _) in enumerate(ROLE_SPLITS):
        start = text.find(marker)
        if start < 0:
            raise ValueError(f"Marker not found: {marker}")
        end = len(text)
        for _, next_marker, _ in ROLE_SPLITS[i + 1 :]:
            pos = text.find(next_marker, start + 1)
            if pos >= 0:
                end = pos
                break
        chunks[key] = text[start + len(marker) : end].strip()
    return chunks


def emit_ts(roles: dict) -> str:
    lines = [
        "import { ROLE } from '@shared/constants/roles';",
        "",
        "export type GuideSection = {",
        "    title: string;",
        "    points: string[];",
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

    role_key_to_const = {k: f"ROLE.{k}" for k, _, _ in ROLE_SPLITS}

    for key, _, ui_title in ROLE_SPLITS:
        data = roles[key]
        lines.append(f"    [{role_key_to_const[key]}]: {{")
        lines.append(f"        title: '{escape_ts(ui_title)}',")
        lines.append(f"        summary: '{escape_ts(data['summary'])}',")
        lines.append("        sections: [")
        for section in data["sections"]:
            lines.append("            {")
            lines.append(f"                title: '{escape_ts(section['title'])}',")
            lines.append("                points: [")
            for point in section["points"]:
                lines.append(f"                    '{escape_ts(point)}',")
            lines.append("                ]")
            lines.append("            },")
        lines.append("        ]")
        lines.append("    },")
        lines.append("")

    lines.append("};")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    text = EXTRACT.read_text(encoding="utf-8")
    chunks = split_roles(text)
    roles = {}
    for key, _, _ in ROLE_SPLITS:
        summary, sections = parse_role_block(chunks[key])
        roles[key] = {"summary": summary, "sections": sections}

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(emit_ts(roles), encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    for key, _, title in ROLE_SPLITS:
        print(f"  {title}: {len(roles[key]['sections'])} sections")


if __name__ == "__main__":
    main()
