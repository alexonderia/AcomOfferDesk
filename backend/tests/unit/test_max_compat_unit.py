from app.repositories.max_compat import build_max_user, derive_max_status, max_subject_value


def test_max_subject_value_normalizes_to_string() -> None:
    assert max_subject_value(123456789) == "123456789"
    assert max_subject_value(" 987 ") == "987"


def test_derive_max_status_unregistered_when_no_linkage() -> None:
    assert derive_max_status(
        account_is_active=None,
        channel_is_verified=None,
        channel_is_active=None,
    ) is None


def test_derive_max_status_blocked_when_account_inactive() -> None:
    assert derive_max_status(
        account_is_active=False,
        channel_is_verified=True,
        channel_is_active=True,
        user_status="active",
    ) == "disapproved"


def test_derive_max_status_blocked_when_channel_inactive() -> None:
    assert derive_max_status(
        account_is_active=True,
        channel_is_verified=True,
        channel_is_active=False,
        user_status="active",
    ) == "disapproved"


def test_derive_max_status_blocked_when_user_inactive() -> None:
    assert derive_max_status(
        account_is_active=True,
        channel_is_verified=True,
        channel_is_active=True,
        user_status="inactive",
    ) == "disapproved"


def test_derive_max_status_blocked_when_user_blacklist() -> None:
    assert derive_max_status(
        account_is_active=True,
        channel_is_verified=True,
        channel_is_active=True,
        user_status="blacklist",
    ) == "disapproved"


def test_derive_max_status_approved_when_verified_and_active() -> None:
    assert derive_max_status(
        account_is_active=True,
        channel_is_verified=True,
        channel_is_active=True,
        user_status="active",
    ) == "approved"


def test_derive_max_status_review_when_not_verified() -> None:
    assert derive_max_status(
        account_is_active=True,
        channel_is_verified=False,
        channel_is_active=True,
        user_status="active",
    ) == "review"


def test_build_max_user_returns_none_without_linkage() -> None:
    assert build_max_user(
        max_user_id="123",
        account_is_active=None,
        channel_is_verified=None,
        channel_is_active=None,
    ) is None
