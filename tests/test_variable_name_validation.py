"""Unit tests for Jinja2-compatible environment variable name validation."""

import unicodedata

import pytest

from pypost.core.variable_name_validation import (
    MSG_EMPTY,
    MSG_INVALID_CHARS,
    MSG_STARTS_WITH_DIGIT,
    validate_variable_name,
    validation_failure_reason,
)

pytestmark = pytest.mark.timeout(30)


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
            ("", MSG_EMPTY, "empty"),
            ("123api", MSG_STARTS_WITH_DIGIT, "starts_with_digit"),
            ("0_", MSG_STARTS_WITH_DIGIT, "starts_with_digit"),
            ("api-key", MSG_INVALID_CHARS, "invalid_chars"),
            ("user name", MSG_INVALID_CHARS, "invalid_chars"),
            ("user.name", MSG_INVALID_CHARS, "invalid_chars"),
            ("api key!", MSG_INVALID_CHARS, "invalid_chars"),
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


_INVALID_CHARS_MSG = MSG_INVALID_CHARS
_STARTS_WITH_DIGIT_MSG = MSG_STARTS_WITH_DIGIT


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


class TestIsidentifierDivergencePYPOST632:
    """PYPOST-632: document isalnum() vs str.isidentifier() divergences — keep isalnum policy."""

    def test_superscript_digit_accepted_by_isalnum_rejected_by_isidentifier(self) -> None:
        name = "x²"
        assert name.isidentifier() is False
        is_valid, error = validate_variable_name(name)
        assert is_valid is True
        assert error == ""

    def test_nfd_combining_marks_rejected_by_isalnum_not_by_isidentifier(self) -> None:
        nfd = unicodedata.normalize("NFD", "naïve")
        assert nfd != "naïve"
        assert nfd.isidentifier() is True
        is_valid, error = validate_variable_name(nfd)
        assert is_valid is False
        assert error == _INVALID_CHARS_MSG
