from __future__ import annotations


ROLE_TECHNICAL_NAME_BY_ID: dict[int, str] = {
    1: "superadmin",
    2: "admin",
    3: "contractor",
    4: "project_manager",
    5: "lead_economist",
    6: "economist",
    7: "operator",
    8: "security_officer",
}

ROLE_ID_BY_TECHNICAL_NAME: dict[str, int] = {
    name: role_id for role_id, name in ROLE_TECHNICAL_NAME_BY_ID.items()
}


def technical_role_name(role_id: int) -> str | None:
    return ROLE_TECHNICAL_NAME_BY_ID.get(role_id)


def local_role_id(role_name: str) -> int | None:
    return ROLE_ID_BY_TECHNICAL_NAME.get(role_name)
