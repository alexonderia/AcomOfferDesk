from sqlalchemy import BigInteger

from iam_app.models import Base


def test_iam_schema_contains_exactly_the_ten_approved_tables() -> None:
    assert set(Base.metadata.tables) == {
        "accounts",
        "account_credentials",
        "roles",
        "permissions",
        "role_permissions",
        "account_permission_grants",
        "auth_sessions",
        "authorization_codes",
        "auth_action_tokens",
        "auth_audit_log",
    }


def test_account_permission_grants_schema_uses_cascading_composite_key() -> None:
    table = Base.metadata.tables["account_permission_grants"]
    assert {column.name for column in table.primary_key.columns} == {
        "account_id",
        "permission_id",
    }
    assert isinstance(table.c.permission_id.type, BigInteger)
    foreign_keys = {
        foreign_key.parent.name: (
            foreign_key.target_fullname,
            foreign_key.ondelete,
        )
        for foreign_key in table.foreign_keys
    }
    assert foreign_keys == {
        "account_id": ("accounts.id", "CASCADE"),
        "permission_id": ("permissions.id", "CASCADE"),
    }
    assert Base.metadata.tables["auth_audit_log"].c.session_id.nullable is True
