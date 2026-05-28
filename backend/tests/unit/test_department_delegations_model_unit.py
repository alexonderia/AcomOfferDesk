from app.domain.department_delegations import (
    DEPARTMENT_DELEGATIONS,
    DEPARTMENT_PERMISSION_TO_DELEGATION_ROLE,
)


def test_department_delegations_include_chats_and_exclude_files_group():
    assert DEPARTMENT_PERMISSION_TO_DELEGATION_ROLE["department.chats.read"] == "delegation.department.chats.read"
    assert "department.chats.send_message" not in DEPARTMENT_PERMISSION_TO_DELEGATION_ROLE
    assert "department.files.read" not in DEPARTMENT_PERMISSION_TO_DELEGATION_ROLE
    assert "department.files.upload" not in DEPARTMENT_PERMISSION_TO_DELEGATION_ROLE
    assert "department.files.delete" not in DEPARTMENT_PERMISSION_TO_DELEGATION_ROLE

    role_codes = {item.role_code for item in DEPARTMENT_DELEGATIONS}
    assert "delegation.department.chats.read" in role_codes
    assert "delegation.department.chats.send_message" not in role_codes
    assert "delegation.department.files.read" not in role_codes
    assert "delegation.department.files.upload" not in role_codes
    assert "delegation.department.files.delete" not in role_codes
