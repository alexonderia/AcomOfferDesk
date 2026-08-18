from __future__ import annotations

from pathlib import Path

from app.models.auth_models import UserContactChannel
from app.models.base import Base
from app.models.orm_models import User
from app.models import auth_models as _auth_models  # noqa: F401
from app.models import orm_models as _orm_models  # noqa: F401


FORBIDDEN_MAIN_LIFECYCLE_TABLES = {
    "registration_invitations",
    "email_verification_actions",
    "registration_tokens",
    "onboarding_sessions",
    "verification_tokens",
    "recovery_actions",
    "pending_users",
    "invite_logs",
}


def test_main_schema_has_no_registration_lifecycle_entities() -> None:
    table_names = set(Base.metadata.tables)
    assert FORBIDDEN_MAIN_LIFECYCLE_TABLES.isdisjoint(table_names)
    assert "onboarding_state" not in {column.name for column in User.__table__.columns}
    assert UserContactChannel.__table__.c.is_verified is not None
    assert User.__table__.c.status is not None


def test_main_flyway_has_no_v108_registration_lifecycle_migration() -> None:
    sql_dir = Path(__file__).resolve().parents[3] / "deploy" / "order_database" / "flyway" / "sql"
    names = {path.name for path in sql_dir.glob("*.sql")}
    assert "V1.0.8__registration_lifecycle.sql" not in names
    for path in sql_dir.glob("*.sql"):
        text = path.read_text(encoding="utf-8")
        assert "onboarding_state" not in text
        assert "registration_invitations" not in text
        assert "email_verification_actions" not in text
