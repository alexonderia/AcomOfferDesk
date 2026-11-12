from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[3]
COMPOSE_FILES = (
    "docker-compose.yml",
    "docker-compose.dev.yml",
    "docker-compose.prod-like.yml",
    "docker-compose.prod.yml",
    "docker-compose.test.yml",
)


@pytest.fixture(scope="module")
def compose_environment(tmp_path_factory):
    docker = shutil.which("docker")
    if docker is None:
        pytest.skip("Docker Compose is required for configuration checks")
    version = subprocess.run([docker, "compose", "version"], capture_output=True, timeout=15)
    if version.returncode:
        pytest.skip("Docker Compose is unavailable")

    directory = tmp_path_factory.mktemp("compose-email-mode")
    environment = os.environ.copy()
    for filename in COMPOSE_FILES:
        content = (ROOT / filename).read_text(encoding="utf-8")
        (directory / filename).write_text(content, encoding="utf-8")
        for variable in re.findall(r"\$\{([A-Z][A-Z0-9_]*)", content):
            environment.pop(variable, None)
    for variable in ("COMPOSE_FILE", "COMPOSE_PROFILES", "COMPOSE_PROJECT_NAME"):
        environment.pop(variable, None)
    for filename in (".env.iam", ".env.iam-db"):
        (directory / filename).write_text("", encoding="utf-8")
    return docker, directory, environment


def render_compose(compose_environment, overlays: tuple[str, ...], mode: str | None):
    docker, directory, environment = compose_environment
    # Deliberately conflict with Compose interpolation: both services must use
    # the selected mode, even if the runtime env file has an older value.
    runtime_mode = "false" if mode == "true" else "true"
    (directory / ".env.app").write_text(
        f"EMAIL_ENABLED={runtime_mode}\nDATABASE_URL=test-only\nIAM_INTERNAL_SERVICE_TOKEN=test-only\n",
        encoding="utf-8",
    )
    compose_env = "APP_RUNTIME_ENV_FILE=.env.app\n"
    if mode is not None:
        compose_env += f"EMAIL_ENABLED={mode}\n"
    (directory / ".env.compose").write_text(compose_env, encoding="utf-8")
    command = [docker, "compose", "--env-file", ".env.compose", "-f", "docker-compose.yml"]
    for overlay in overlays:
        command.extend(["-f", overlay])
    return subprocess.run(
        [*command, "config", "--format", "json"],
        cwd=directory, env=environment, capture_output=True, text=True, encoding="utf-8", timeout=30,
    )


@pytest.mark.parametrize("mode", ["false", "true"])
@pytest.mark.parametrize("overlays", [
    ("docker-compose.dev.yml",),
    ("docker-compose.prod-like.yml",),
    ("docker-compose.prod.yml",),
    ("docker-compose.prod.yml", "docker-compose.test.yml"),
])
def test_compose_passes_one_explicit_mail_mode_to_backend_and_worker(compose_environment, overlays, mode):
    result = render_compose(compose_environment, overlays, mode)
    assert result.returncode == 0, result.stderr
    services = json.loads(result.stdout)["services"]
    for name in ("backend", "notifications_worker"):
        assert services[name]["environment"]["EMAIL_ENABLED"] == mode
    assert "EMAIL_ENABLED" not in services["web"].get("environment", {})
    guard_environment = services["file_guard"].get("environment", {})
    assert not {"EMAIL_ENABLED", "DATABASE_URL", "IAM_INTERNAL_SERVICE_TOKEN"}.intersection(guard_environment)


@pytest.mark.parametrize("mode", [None, ""])
def test_compose_rejects_missing_mail_mode_before_startup(compose_environment, mode):
    result = render_compose(compose_environment, ("docker-compose.dev.yml",), mode)
    assert result.returncode != 0
    assert "EMAIL_ENABLED" in result.stderr
