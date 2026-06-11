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
            ("api-key", "Variable name can only contain letters, numbers, and underscores.", "invalid_chars"),
            ("user name", "Variable name can only contain letters, numbers, and underscores.", "invalid_chars"),
            ("user.name", "Variable name can only contain letters, numbers, and underscores.", "invalid_chars"),
            ("api key!", "Variable name can only contain letters, numbers, and underscores.", "invalid_chars"),
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
