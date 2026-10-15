from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.domain.iam_roles import ROLE_TECHNICAL_NAME_BY_ID
from app.domain.permissions import get_known_permissions
from app.scripts import migrate_users_to_iam
from app.scripts.seed_iam_rbac import build_rbac_matrix


def test_rbac_seed_matrix_is_derived_from_the_application_contract() -> None:
    matrix = build_rbac_matrix()
    assert set(matrix) == set(ROLE_TECHNICAL_NAME_BY_ID.values())
    assert set().union(*(set(values) for values in matrix.values())) == set(get_known_permissions())
    assert all(values == sorted(set(values)) for values in matrix.values())
    assert not any(name.startswith("delegation.") for name in matrix)


@pytest.mark.asyncio
async def test_migration_dry_run_has_no_iam_or_database_writes(monkeypatch, capsys) -> None:
    candidates = [
        migrate_users_to_iam.MigrationCandidate(
            user_id="login-may-be-email@example.com",
            role_id=6,
            status="active",
            email="user@example.com",
        )
    ]
    monkeypatch.setattr(migrate_users_to_iam, "find_candidates", lambda: _async_value(candidates))

    class ForbiddenClient:
        def __init__(self):
            raise AssertionError("dry-run must not instantiate the IAM client")

    monkeypatch.setattr(migrate_users_to_iam, "IamClient", ForbiddenClient)

    assert await migrate_users_to_iam.run(apply=False) == 0
    output = capsys.readouterr().out
    assert "login-may-be-email@example.com" not in output
    assert "user@example.com" not in output
    assert "token" not in output.lower()


async def _async_value(value):
    return value


@pytest.mark.asyncio
async def test_migration_candidate_is_idempotent_on_repeat(monkeypatch) -> None:
    state = {"binding": None, "put_calls": 0, "action_calls": 0, "emails": 0}

    class AuthAccounts:
        async def get_by_user_provider(self, **_kwargs):
            return state["binding"]

        async def add(self, binding):
            state["binding"] = binding

    class FakeUow:
        user_auth_accounts = AuthAccounts()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

    class FakeClient:
        async def put_account(self, *, account_id, **_kwargs):
            state["put_calls"] += 1
            return SimpleNamespace(id=str(account_id), auth_status="pending")

        async def create_action_token(self, **_kwargs):
            state["action_calls"] += 1
            return SimpleNamespace(token="opaque-action-token")

    monkeypatch.setattr(migrate_users_to_iam, "UnitOfWork", FakeUow)

    async def fake_send_email(**_kwargs):
        state["emails"] += 1

    monkeypatch.setattr(migrate_users_to_iam, "send_iam_password_action_email", fake_send_email)
    candidate = migrate_users_to_iam.MigrationCandidate(
        user_id="existing-user",
        role_id=6,
        status="active",
        email="user@example.com",
    )
    client = FakeClient()

    assert await migrate_users_to_iam.migrate_candidate(candidate, client=client) is True
    assert await migrate_users_to_iam.migrate_candidate(candidate, client=client) is True
    assert state["put_calls"] == 1
    assert state["action_calls"] == 1
    assert state["emails"] == 1


@pytest.mark.asyncio
async def test_migration_reactivates_inactive_binding_without_changing_subject(
    monkeypatch,
) -> None:
    binding = SimpleNamespace(
        is_active=False,
        external_subject_id="7846b846-56d2-4ab7-99c3-08b5effe8f04",
        external_username="old-login",
        external_email="old@example.com",
    )
    state = {"put_account_id": None}

    class AuthAccounts:
        async def get_by_user_provider(self, **_kwargs):
            return binding

    class FakeUow:
        user_auth_accounts = AuthAccounts()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

    class FakeClient:
        async def put_account(self, *, account_id, **_kwargs):
            state["put_account_id"] = str(account_id)
            return SimpleNamespace(id=str(account_id), auth_status="active")

    monkeypatch.setattr(migrate_users_to_iam, "UnitOfWork", FakeUow)
    candidate = migrate_users_to_iam.MigrationCandidate(
        user_id="reactivated-user",
        role_id=6,
        status="active",
        email="current@example.com",
    )

    assert await migrate_users_to_iam.migrate_candidate(candidate, client=FakeClient()) is True
    assert state["put_account_id"] == binding.external_subject_id
    assert binding.is_active is True
    assert binding.external_username == candidate.user_id
    assert binding.external_email == candidate.email


@pytest.mark.asyncio
async def test_migration_email_failure_rolls_back_binding_and_retry_reuses_account_id(
    monkeypatch,
) -> None:
    state = {"binding": None, "pending_binding": None, "put_ids": [], "emails": 0}

    class AuthAccounts:
        async def get_by_user_provider(self, **_kwargs):
            return state["binding"]

        async def add(self, binding):
            state["pending_binding"] = binding

    class FakeUow:
        def __init__(self):
            self.user_auth_accounts = AuthAccounts()

        async def __aenter__(self):
            state["pending_binding"] = None
            return self

        async def __aexit__(self, exc_type, *_args):
            if exc_type is None:
                state["binding"] = state["pending_binding"]
            state["pending_binding"] = None

    class FakeClient:
        async def put_account(self, *, account_id, **_kwargs):
            state["put_ids"].append(str(account_id))
            return SimpleNamespace(id=str(account_id), auth_status="pending")

        async def create_action_token(self, **_kwargs):
            return SimpleNamespace(token="replacement-action-token")

    async def flaky_send_email(**_kwargs):
        state["emails"] += 1
        if state["emails"] == 1:
            raise RuntimeError("sanitized SMTP failure")

    monkeypatch.setattr(migrate_users_to_iam, "UnitOfWork", FakeUow)
    monkeypatch.setattr(migrate_users_to_iam, "send_iam_password_action_email", flaky_send_email)
    candidate = migrate_users_to_iam.MigrationCandidate(
        user_id="retry-user",
        role_id=6,
        status="active",
        email="retry@example.com",
    )
    client = FakeClient()

    with pytest.raises(RuntimeError, match="sanitized SMTP failure"):
        await migrate_users_to_iam.migrate_candidate(candidate, client=client)
    assert state["binding"] is None

    assert await migrate_users_to_iam.migrate_candidate(candidate, client=client) is True
    assert state["binding"] is not None
    assert len(set(state["put_ids"])) == 1
    assert state["emails"] == 2


@pytest.mark.asyncio
async def test_migration_skips_user_without_valid_delivery_email(monkeypatch) -> None:
    class ForbiddenUow:
        def __init__(self):
            raise AssertionError("skipped candidate must not open a database transaction")

    monkeypatch.setattr(migrate_users_to_iam, "UnitOfWork", ForbiddenUow)
    candidate = migrate_users_to_iam.MigrationCandidate(
        user_id="missing-email",
        role_id=6,
        status="active",
        email=None,
    )
    assert await migrate_users_to_iam.migrate_candidate(candidate, client=object()) is False


def test_active_application_modules_do_not_import_legacy_keycloak_runtime() -> None:
    app_root = Path(__file__).resolve().parents[2] / "app"
    forbidden_prefixes = (
        "app.services.keycloak",
        "app.services.identity_sync",
        "app.core.oidc_state_tokens",
    )
    pending_modules = ["app.main"]
    visited_modules: set[str] = set()
    imported_modules: set[str] = set()

    def resolve_module(module: str) -> Path | None:
        if not module.startswith("app"):
            return None
        relative_parts = module.split(".")[1:]
        module_path = app_root.joinpath(*relative_parts)
        file_candidate = module_path.with_suffix(".py")
        if file_candidate.is_file():
            return file_candidate
        package_candidate = module_path / "__init__.py"
        return package_candidate if package_candidate.is_file() else None

    while pending_modules:
        module = pending_modules.pop()
        if module in visited_modules:
            continue
        visited_modules.add(module)
        path = resolve_module(module)
        if path is None:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                discovered = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                discovered = [node.module]
                discovered.extend(f"{node.module}.{alias.name}" for alias in node.names)
            else:
                continue
            for discovered_module in discovered:
                imported_modules.add(discovered_module)
                if discovered_module.startswith("app") and resolve_module(discovered_module):
                    pending_modules.append(discovered_module)

    assert not any(module.startswith(forbidden_prefixes) for module in imported_modules)
