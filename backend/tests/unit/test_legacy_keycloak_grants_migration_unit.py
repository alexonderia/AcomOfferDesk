from __future__ import annotations

import pytest

from app.scripts import migrate_legacy_keycloak_grants as migration


def test_maps_all_supported_legacy_delegation_families_to_atomic_permissions() -> None:
    assert migration.map_legacy_roles(
        frozenset(
            {
                "delegation.department.requests.update",
                "delegation.department.chats.send_message",
                "delegation.department.files.read",
                "delegation.contractors.profile.status.update",
            }
        )
    ) == frozenset(
        {
            "department.requests.update",
            "department.chats.send_message",
            "department.files.read",
            "contractors.read",
            "contractors.profile.read",
            "contractors.profile.status.update",
        }
    )


def test_rejects_unknown_legacy_delegation_role() -> None:
    with pytest.raises(ValueError, match="Unsupported legacy delegation"):
        migration.map_legacy_roles(
            frozenset({"delegation.department.unknown"})
        )


@pytest.mark.asyncio
async def test_apply_preserves_existing_iam_grants_and_is_idempotent(
    monkeypatch,
    capsys,
) -> None:
    target = migration.LegacyGrantTarget(
        user_id="user-1",
        iam_account_id="iam-account-1",
        role_name="economist",
        legacy_roles=frozenset({"delegation.department.requests.update"}),
        permissions=frozenset({"department.requests.update"}),
    )
    monkeypatch.setattr(
        migration,
        "find_targets",
        lambda: _async_value(([target], [])),
    )

    class Client:
        grants = frozenset({"unrelated.permission"})
        put_calls: list[frozenset[str]] = []

        async def seed_rbac(self, matrix):
            assert matrix
            assert not any(
                permission.startswith("delegation.")
                for permissions in matrix.values()
                for permission in permissions
            )

        async def get_account_permissions(self, *, account_id: str):
            assert account_id == "iam-account-1"
            return type(
                "Permissions",
                (),
                {"individually_granted_permissions": self.grants},
            )()

        async def replace_account_permission_grants(
            self,
            *,
            account_id: str,
            permissions: frozenset[str],
        ):
            assert account_id == "iam-account-1"
            self.put_calls.append(permissions)
            self.grants = permissions

    client = Client()
    monkeypatch.setattr(migration, "IamClient", lambda: client)

    assert await migration.run(apply=True) == 0
    assert await migration.run(apply=True) == 0
    assert client.put_calls == [
        frozenset({"unrelated.permission", "department.requests.update"})
    ]
    assert '"legacy_grants_migrated": 1' in capsys.readouterr().out


async def _async_value(value):
    return value
