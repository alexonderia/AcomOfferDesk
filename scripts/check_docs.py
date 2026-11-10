#!/usr/bin/env python3
"""Check local Markdown links in repository documentation (no network access)."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


LINK = re.compile(r"!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+\"[^\"]*\")?\s*\)")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")


def check(root: Path) -> list[str]:
    files = [
        *root.glob("*.md"),
        *root.glob("*/README.md"),
        *(root / "backend").rglob("README.md"),
        *(root / "iam").rglob("README.md"),
        *(root / "docs").rglob("*.md"),
    ]
    failures: list[str] = []
    for file in sorted(set(files)):
        fence: str | None = None
        for number, line in enumerate(file.read_text(encoding="utf-8-sig").splitlines(), 1):
            marker = FENCE.match(line)
            if marker:
                if fence is None:
                    fence = marker[1][0]
                elif fence == marker[1][0]:
                    fence = None
                continue
            if fence is not None:
                continue
            for match in LINK.finditer(line):
                target = match[1].strip("<>")
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                target_path = unquote(parsed.path)
                destination = (root / target_path.lstrip("/")) if target_path.startswith("/") else file.parent / target_path
                if not destination.exists():
                    failures.append(f"{file.relative_to(root).as_posix()}:{number}: missing {target}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    failures = check(args.root.resolve())
    for failure in failures:
        print(failure)
    if failures:
        print(f"Broken local links: {len(failures)}")
        return 1
    print("OK: local Markdown links resolve")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
