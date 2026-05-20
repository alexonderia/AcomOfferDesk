"""Expected Keycloak app.* composite members (source: infra/keycloak/bootstrap.sh)."""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

_APP_ROLE_BLOCK_PATTERN = re.compile(
    r"^ROLE_(APP_[A-Z0-9_]+)=\$\(cat <<(?:'EOF'|EOF)\n(.*?)^EOF\n\)",
    re.MULTILINE | re.DOTALL,
)
_PERMISSION_BLOCK_PATTERN = re.compile(
    r"^PERMISSION_ROLE_NAMES=\$\(cat <<'EOF'\n(.*?)^EOF\n\)",
    re.MULTILINE | re.DOTALL,
)


def _bootstrap_path() -> Path:
    """Resolve bootstrap.sh in dev checkout or inside backend image (/app/keycloak/)."""
    override = os.environ.get("KEYCLOAK_BOOTSTRAP_SH_PATH", "").strip()
    if override:
        path = Path(override)
        if path.is_file():
            return path
        raise FileNotFoundError(f"KEYCLOAK_BOOTSTRAP_SH_PATH not found: {override}")

    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "keycloak" / "bootstrap.sh",
        here.parents[3] / "infra" / "keycloak" / "bootstrap.sh",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate

    raise FileNotFoundError(
        "infra/keycloak/bootstrap.sh not found (expected /app/keycloak/bootstrap.sh in backend image "
        "or repo layout AcomOfferDesk/backend/app/scripts); rebuild backend or set KEYCLOAK_BOOTSTRAP_SH_PATH"
    )


def _parse_line_block(block: str) -> frozenset[str]:
    members: set[str] = set()
    for line in block.splitlines():
        normalized = line.strip()
        if normalized:
            members.add(normalized)
    return frozenset(members)


@lru_cache(maxsize=1)
def load_permission_role_names() -> frozenset[str]:
    text = _bootstrap_path().read_text(encoding="utf-8")
    match = _PERMISSION_BLOCK_PATTERN.search(text)
    if match is None:
        raise RuntimeError("PERMISSION_ROLE_NAMES block not found in bootstrap.sh")
    return _parse_line_block(match.group(1))


@lru_cache(maxsize=1)
def load_app_role_members() -> dict[str, frozenset[str]]:
    text = _bootstrap_path().read_text(encoding="utf-8")
    manifest: dict[str, frozenset[str]] = {}
    for match in _APP_ROLE_BLOCK_PATTERN.finditer(text):
        # APP_CONTRACTOR -> app.contractor, APP_PROJECT_MANAGER -> app.project_manager
        role_name = f"app.{match.group(1)[4:].lower()}"
        manifest[role_name] = _parse_line_block(match.group(2))
    return manifest
