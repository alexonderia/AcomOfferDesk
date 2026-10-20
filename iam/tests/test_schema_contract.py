from sqlalchemy import BigInteger, CheckConstraint

from iam_app.models import Account, AuthActionToken, Base


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
    audit_session_id = Base.metadata.tables["auth_audit_log"].c.session_id
    assert audit_session_id.nullable is True
    assert {foreign_key.ondelete for foreign_key in audit_session_id.foreign_keys} == {
        "SET NULL"
    }


def test_auth_action_tokens_support_lifecycle_purposes_and_email_context() -> None:
    table = AuthActionToken.__table__
    assert "context" in table.c
    assert table.c.context.nullable is True
    purpose_sql = " ".join(
        str(constraint.sqltext)
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    )
    for purpose in (
        "password_setup",
        "password_reset",
        "verify_email",
        "first_access",
        "profile_change",
    ):
        assert purpose in purpose_sql
    assert "complete_profile" not in purpose_sql


def test_accounts_store_durable_required_actions_without_ttl() -> None:
    table = Account.__table__
    assert "required_actions" in table.c
    assert table.c.required_actions.nullable is False
    assert "expires_at" not in table.c
