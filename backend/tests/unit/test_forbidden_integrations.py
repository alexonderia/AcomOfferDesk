from __future__ import annotations

import re
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOTS = (
    REPOSITORY_ROOT / "backend" / "app",
    REPOSITORY_ROOT / "iam" / "iam_app",
    REPOSITORY_ROOT / "web" / "src",
    REPOSITORY_ROOT / "notifications_worker",
    REPOSITORY_ROOT / "file_guard",
    REPOSITORY_ROOT / "shared",
    REPOSITORY_ROOT / "scripts",
    REPOSITORY_ROOT / "deploy",
)
ROOT_CONFIG_FILES = (
    *REPOSITORY_ROOT.glob(".env*.example"),
    *REPOSITORY_ROOT.glob("docker-compose*.yml"),
    REPOSITORY_ROOT / "backend" / "Dockerfile",
    REPOSITORY_ROOT / "backend" / "nginx.conf",
    REPOSITORY_ROOT / "iam" / "Dockerfile",
    REPOSITORY_ROOT / "web" / "Dockerfile",
    REPOSITORY_ROOT / "web" / "nginx.conf",
)
DEPENDENCY_MANIFESTS = {
    *REPOSITORY_ROOT.glob("package*.json"),
    *REPOSITORY_ROOT.glob("requirements*.txt"),
    *(REPOSITORY_ROOT / "backend").glob("requirements*.txt"),
    *(REPOSITORY_ROOT / "iam").glob("requirements*.txt"),
    *(REPOSITORY_ROOT / "notifications_worker").glob("requirements*.txt"),
    *(REPOSITORY_ROOT / "file_guard").glob("requirements*.txt"),
    *(REPOSITORY_ROOT / "web").glob("package*.json"),
    *(REPOSITORY_ROOT / "web").glob("*lock*.yaml"),
    *(REPOSITORY_ROOT / "web").glob("*lock*.yml"),
}
SKIPPED_DIRECTORY_NAMES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
}
TEXT_SUFFIXES = {
    "",
    ".conf",
    ".css",
    ".env",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}
FORBIDDEN_PATTERNS = {
    "keycloak runtime": re.compile(r"keycloak", re.IGNORECASE),
    "telegram bot runtime": re.compile(
        r"\btg_bot\b|/api/v1/tg\b|"
        r"\bTelegram(?:Bot|Client|Service|Router)\b|api\.telegram\.org",
        re.IGNORECASE,
    ),
    "telegram env": re.compile(r"\bTELEGRAM_[A-Z0-9_]*\b"),
    "MAX bot runtime": re.compile(
        r"\bmax_bot\b|/api/v1/max\b|"
        r"\bMax(?:Bot|Client|Service|Router)\b",
        re.IGNORECASE,
    ),
    "MAX bot env": re.compile(r"\bMAX_BOT_[A-Z0-9_]*\b"),
}
FORBIDDEN_DEPENDENCY = re.compile(
    r"keycloak|telegram|tg[-_]bot|max[-_]bot",
    re.IGNORECASE,
)
ALLOWED_KEYCLOAK_DATA_COMPATIBILITY = {
    REPOSITORY_ROOT / "backend" / "app" / "models" / "auth_models.py",
}


def _runtime_files() -> list[Path]:
    files = [
        path
        for path in (*ROOT_CONFIG_FILES, *DEPENDENCY_MANIFESTS)
        if path.is_file()
    ]
    for root in RUNTIME_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if (
                path.is_file()
                and path.suffix.lower() in TEXT_SUFFIXES
                and not any(part in SKIPPED_DIRECTORY_NAMES for part in path.parts)
            ):
                files.append(path)
    return sorted(set(files))


def test_forbidden_auth_and_messenger_integrations_are_not_in_runtime() -> None:
    violations: list[str] = []
    for path in _runtime_files():
        relative_path = path.relative_to(REPOSITORY_ROOT).as_posix()
        lowered_parts = {part.lower() for part in path.parts}
        if {"tg_bot", "max_bot"} & lowered_parts:
            violations.append(f"{relative_path}: forbidden runtime directory")
        text = path.read_text(encoding="utf-8", errors="ignore")
        if path in DEPENDENCY_MANIFESTS:
            for match in FORBIDDEN_DEPENDENCY.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                violations.append(
                    f"{relative_path}:{line}: forbidden integration dependency"
                )
        for label, pattern in FORBIDDEN_PATTERNS.items():
            if (
                label == "keycloak runtime"
                and path in ALLOWED_KEYCLOAK_DATA_COMPATIBILITY
            ):
                continue
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                violations.append(f"{relative_path}:{line}: {label}")

    assert violations == [], "\n".join(violations)
