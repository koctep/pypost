"""Regression tests for the centralized template expression lexer and parser."""

import pytest

from pypost.core.template_expression_parser import (
    function_names,
    identifier_names,
    lex_template_expressions,
    split_single_argument,
)

pytestmark = pytest.mark.timeout(30)


def test_lexer_handles_closed_and_unclosed_placeholders_in_one_pass():
    tokens = lex_template_expressions("{{ first }} / {{ broken / {{ second }}")

    assert [(token.expression, token.closed) for token in tokens] == [
        ("first", True),
        ("broken /", False),
        ("second", True),
    ]


def test_parser_handles_nested_calls_and_quoted_delimiters():
    expression = 'outer(inner("a,b"))'

    assert function_names(expression) == ("outer", "inner")
    assert split_single_argument('inner("a,b")') == 'inner("a,b")'
    assert split_single_argument('a, inner(b)') is None


def test_identifier_extraction_is_shared_with_environment_resolution():
    assert identifier_names("profile.base_url + urlencode(host)") == (
        "profile",
        "urlencode",
        "host",
    )
