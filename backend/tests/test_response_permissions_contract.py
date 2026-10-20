from app.schemas.auth import AuthSessionData
from app.schemas.requests import OpenRequestListData, RequestDetailsResponseData, RequestListData
from app.schemas.users import (
    EconomistListData,
    MeData,
    RequestContractorListData,
    RequestEconomistListData,
    UserListData,
)


def test_auth_session_data_keeps_only_iam_role_and_permissions():
    fields = AuthSessionData.model_fields
    assert "permissions" in fields
    assert "role" in fields
    assert "app_roles" not in fields
    assert "delegation_roles" not in fields


def test_request_list_and_detail_data_do_not_expose_global_permissions():
    assert "permissions" not in RequestListData.model_fields
    assert "permissions" not in OpenRequestListData.model_fields
    assert "permissions" not in RequestDetailsResponseData.model_fields


def test_users_list_data_do_not_expose_global_permissions():
    assert "permissions" not in UserListData.model_fields
    assert "permissions" not in EconomistListData.model_fields
    assert "permissions" not in RequestEconomistListData.model_fields
    assert "permissions" not in RequestContractorListData.model_fields


def test_me_data_can_keep_permissions_for_profile_compatibility():
    assert "permissions" in MeData.model_fields
