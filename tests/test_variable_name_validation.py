"""Unit tests for Jinja2-compatible environment variable name validation."""

import pytest

from pypost.core.variable_name_validation import (
    validate_variable_name,
    validation_failure_reason,
)


class TestValidateVariableName:
    @pytest.mark.parametrize(
        "name",
        [
            "api_key",
            "_internal",
            "userId123",
            "service_url",
            "DEBUG_MODE",
            "a",
            "Z9",
            "_",
            "a" * 200,
        ],
    )
    def test_valid_names(self, name: str) -> None:
        is_valid, error = validate_variable_name(name)
        assert is_valid is True
        assert error == ""
        assert validation_failure_reason(name) is None

    @pytest.mark.parametrize(
        ("name", "expected_error", "expected_reason"),
        [
            ("", "Variable name cannot be empty.", "empty"),
            ("123api", "Variable name cannot start with a digit.", "starts_with_digit"),
            ("0_", "Variable name cannot start with a digit.", "starts_with_digit"),
            (
                "api-key",
                "Variable name can only contain letters, numbers, and underscores.",
                "invalid_chars",
            ),
            (
                "user name",
                "Variable name can only contain letters, numbers, and underscores.",
                "invalid_chars",
            ),
            (
                "user.name",
                "Variable name can only contain letters, numbers, and underscores.",
                "invalid_chars",
            ),
            (
                "api key!",
                "Variable name can only contain letters, numbers, and underscores.",
                "invalid_chars",
            ),
        ],
    )
    def test_invalid_names(
        self,
        name: str,
        expected_error: str,
        expected_reason: str,
    ) -> None:
        is_valid, error = validate_variable_name(name)
        assert is_valid is False
        assert error == expected_error
        assert validation_failure_reason(name) == expected_reason

    @pytest.mark.parametrize("name", ["café", "变量", "über"])
    def test_unicode_letters_allowed_by_isalnum_policy(self, name: str) -> None:
        """Current rules use str.isalnum(), which accepts Unicode letters."""
        is_valid, error = validate_variable_name(name)
        assert is_valid is True
        assert error == ""


_INVALID_CHARS_MSG = (
    "Variable name can only contain letters, numbers, and underscores."
)
_STARTS_WITH_DIGIT_MSG = "Variable name cannot start with a digit."


class TestValidateVariableNameUnicode:
    @pytest.mark.parametrize(
        "name",
        [
            "naïve",
            "Ελληνικά",
            "变量名",
            "_变量",
            "api_über",
            "α",
        ],
    )
    def test_unicode_letters_valid(self, name: str) -> None:
        is_valid, error = validate_variable_name(name)
        assert is_valid is True
        assert error == ""
        assert validation_failure_reason(name) is None

    @pytest.mark.parametrize(
        ("name", "expected_error", "expected_reason"),
        [
            ("１abc", _STARTS_WITH_DIGIT_MSG, "starts_with_digit"),
            ("٩test", _STARTS_WITH_DIGIT_MSG, "starts_with_digit"),
            ("api🔑", _INVALID_CHARS_MSG, "invalid_chars"),
            ("key❤", _INVALID_CHARS_MSG, "invalid_chars"),
            ("café!", _INVALID_CHARS_MSG, "invalid_chars"),
            ("api\u200bkey", _INVALID_CHARS_MSG, "invalid_chars"),
            ("soft\u00adhyphen", _INVALID_CHARS_MSG, "invalid_chars"),
        ],
    )
    def test_unicode_invalid_names(
        self,
        name: str,
        expected_error: str,
        expected_reason: str,
    ) -> None:
        is_valid, error = validate_variable_name(name)
        assert is_valid is False
        assert error == expected_error
        assert validation_failure_reason(name) == expected_reason


class TestValidateVariableNameMixed:
    @pytest.mark.parametrize(
        ("name", "expected_error", "expected_reason"),
        [
            ("api_key!", _INVALID_CHARS_MSG, "invalid_chars"),
            ("valid-name", _INVALID_CHARS_MSG, "invalid_chars"),
            ("a b", _INVALID_CHARS_MSG, "invalid_chars"),
            ("letter1@domain", _INVALID_CHARS_MSG, "invalid_chars"),
            ("9valid_prefix", _STARTS_WITH_DIGIT_MSG, "starts_with_digit"),
            ("0_underscore", _STARTS_WITH_DIGIT_MSG, "starts_with_digit"),
            ("9!", _STARTS_WITH_DIGIT_MSG, "starts_with_digit"),
        ],
    )
    def test_mixed_strings_reject_with_canonical_reason(
        self,
        name: str,
        expected_error: str,
        expected_reason: str,
    ) -> None:
        is_valid, error = validate_variable_name(name)
        assert is_valid is False
        assert error == expected_error
        assert validation_failure_reason(name) == expected_reason


class TestValidateVariableNameBoundaries:
    @pytest.mark.parametrize(
        "name",
        [
            "___",
            "____",
            "__",
            "a" * 500,
            "_" + "x" * 999,
        ],
    )
    def test_boundary_valid_names(self, name: str) -> None:
        is_valid, error = validate_variable_name(name)
        assert is_valid is True
        assert error == ""
        assert validation_failure_reason(name) is None

    @pytest.mark.parametrize(
        ("name", "expected_error", "expected_reason"),
        [
            (" ", _INVALID_CHARS_MSG, "invalid_chars"),
            ("\t", _INVALID_CHARS_MSG, "invalid_chars"),
            ("  ", _INVALID_CHARS_MSG, "invalid_chars"),
        ],
    )
    def test_boundary_invalid_names(
        self,
        name: str,
        expected_error: str,
        expected_reason: str,
    ) -> None:
        is_valid, error = validate_variable_name(name)
        assert is_valid is False
        assert error == expected_error
        assert validation_failure_reason(name) == expected_reason
