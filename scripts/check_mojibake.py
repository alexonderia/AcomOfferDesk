#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCLUDE_EXTENSIONS = {".py", ".ts", ".tsx", ".md", ".json", ".yml", ".yaml"}
IGNORE_DIRS = {
    ".git",
    ".trellis",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
}
IGNORE_FILES = {
    "package-lock.json",
    "web/tsconfig.tsbuildinfo",
}

# Typical UTF-8/cp1251 mojibake fragments in Russian text.
MOJIBAKE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\?{3,}"),
    re.compile(r"[РС][ЀЁЂЃЄЅІЇЈЉЊЋЌЎЏѐёђѓєѕіїјљњћќўџ]"),
    re.compile(r"(?:Ð.|Ñ.){2,}"),
)


def is_ignored(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    if rel in IGNORE_FILES:
        return True
    return any(part in IGNORE_DIRS for part in path.parts)


def iter_files() -> list[Path]:
    candidates: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in INCLUDE_EXTENSIONS:
            continue
        if is_ignored(path):
            continue
        candidates.append(path)
    return candidates


def line_has_suspicious_mojibake(line: str) -> bool:
    matches_count = 0
    for pattern in MOJIBAKE_PATTERNS:
        match = pattern.search(line)
        if not match:
            continue
        # Avoid common false positives on simple punctuation-only lines.
        if line.strip(" ?.") == "":
            continue
        matches_count += 1
    return matches_count >= 1


def safe_print(text: str) -> None:
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="backslashreplace"))


def main() -> int:
    issues: list[tuple[Path, int, str]] = []
    for file_path in iter_files():
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            issues.append((file_path, 0, "File is not valid UTF-8"))
            continue

        for line_number, line in enumerate(text.splitlines(), start=1):
            if line_has_suspicious_mojibake(line):
                issues.append((file_path, line_number, line.strip()))

    if not issues:
        safe_print("OK: mojibake patterns were not found")
        return 0

    safe_print("Found possible mojibake:")
    for path, line_number, line in issues:
        rel = path.relative_to(ROOT).as_posix()
        if line_number == 0:
            safe_print(f"- {rel}: {line}")
        else:
            safe_print(f"- {rel}:{line_number}: {line}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
