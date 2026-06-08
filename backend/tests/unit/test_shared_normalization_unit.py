from __future__ import annotations

from shared.normalization import as_optional_int, is_truthy_env_flag, normalize_optional_str


def test_normalize_optional_str_trims_and_empty_to_none():
    assert normalize_optional_str("  value  ") == "value"
    assert normalize_optional_str("   ") is None
    assert normalize_optional_str(None) is None


def test_as_optional_int_accepts_int_and_numeric_string():
    assert as_optional_int(42) == 42
    assert as_optional_int(" 42 ") == 42
    assert as_optional_int("not-a-number") is None


def test_is_truthy_env_flag_supports_known_true_values():
    assert is_truthy_env_flag("true") is True
    assert is_truthy_env_flag(" YES ") is True
    assert is_truthy_env_flag("0") is False
    assert is_truthy_env_flag(None) is False
