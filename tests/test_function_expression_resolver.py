import pytest

import unittest

from pypost.core.function_expression_resolver import (
    NESTED_FUNCTION_CALLS_ALLOWED,
    FunctionExpressionResolver,
)
from pypost.core.function_registry import FunctionRegistry

pytestmark = pytest.mark.timeout(30)


MALFORMED_NESTED_EXPRESSION_CASES = [
    ("M1", "{{ md5(urlencode(db) }}", "invalid_argument", "md5"),
    ("M2", "{{ md5(urlencode(db))) }}", "invalid_argument", "urlencode"),
    ("M3", "{{ md5((urlencode(db))) }}", "invalid_argument", "md5"),
    ("M4", "{{ base64(md5(urlencode(db) }}", "invalid_argument", "base64"),
]

EMPTY_ARGUMENT_CASES = [
    ("E1", "{{ md5() }}", "invalid_argument", "md5"),
    ("E2", "{{ urlencode() }}", "invalid_argument", "urlencode"),
    ("E3", "{{ base64() }}", "invalid_argument", "base64"),
]

STANDALONE_MALFORMED_CLOSING_PAREN_CASES = [
    ("P1", "{{ urlencode(db)) }}", "invalid_argument", "urlencode"),
    ("P2", "{{ md5(x)) }}", "invalid_argument", "md5"),
]

MULTI_PLACEHOLDER_FIRST_FAILURE_CASES = [
    (
        "F1",
        "{{ host }} {{ md5() }}",
        "invalid_argument",
        "md5",
    ),
    (
        "F2",
        "{{ urlencode(x) }} {{ mystery(y) }}",
        "unknown_function",
        "mystery",
    ),
    (
        "F3",
        "{{ mystery(y) }} {{ urlencode(x) }}",
        "unknown_function",
        "mystery",
    ),
    (
        "F4",
        "{{ md5(urlencode(db)) }} {{ md5() }}",
        "invalid_argument",
        "md5",
    ),
    (
        "F5",
        "{{ host }} {{ urlencode(a, b) }}",
        "invalid_arity",
        "urlencode",
    ),
]


class TestFunctionExpressionResolver(unittest.TestCase):
    def setUp(self):
        self.registry = FunctionRegistry()
        self.resolver = FunctionExpressionResolver(self.registry)

    def test_multiple_placeholders_all_valid(self):
        r = self.resolver.validate_content("{{ a }} {{ b }} {{ urlencode(c) }}")
        self.assertTrue(r.is_valid)

    def test_whitespace_inside_delimiters(self):
        r = self.resolver.validate_content("{{  md5( db )  }}")
        self.assertTrue(r.is_valid)

    def test_unknown_function(self):
        r = self.resolver.validate_content("{{ mystery(x) }}")
        self.assertFalse(r.is_valid)
        self.assertEqual("unknown_function", r.code)
        self.assertEqual("mystery", r.function_name)

    def test_nested_allowed_calls(self):
        r = self.resolver.validate_content("{{ md5(urlencode(db)) }}")
        self.assertTrue(r.is_valid)

    def test_nested_function_calls_allowed_constant(self):
        self.assertTrue(NESTED_FUNCTION_CALLS_ALLOWED)

    def test_valid_three_level_chain(self):
        r = self.resolver.validate_content("{{ base64(md5(urlencode(db))) }}")
        self.assertTrue(r.is_valid)

    def test_unknown_function_nested(self):
        r = self.resolver.validate_content("{{ md5(unknown(db)) }}")
        self.assertFalse(r.is_valid)
        self.assertEqual("unknown_function", r.code)
        self.assertEqual("unknown", r.function_name)

    def test_invalid_nested_literal_arg(self):
        r = self.resolver.validate_content("{{ md5(urlencode('db')) }}")
        self.assertFalse(r.is_valid)
        self.assertEqual("invalid_argument", r.code)
        self.assertEqual("urlencode", r.function_name)

    def test_multi_arg_inside_nested(self):
        r = self.resolver.validate_content("{{ md5(urlencode(a, b)) }}")
        self.assertFalse(r.is_valid)
        self.assertEqual("invalid_argument", r.code)
        self.assertEqual("md5", r.function_name)

    def test_invalid_arity(self):
        r = self.resolver.validate_content("{{ urlencode(a, b) }}")
        self.assertFalse(r.is_valid)
        self.assertEqual("invalid_arity", r.code)
        self.assertEqual("urlencode", r.function_name)

    def test_invalid_syntax_unclosed_call(self):
        r = self.resolver.validate_content("{{ urlencode(db }}")
        self.assertFalse(r.is_valid)
        self.assertEqual("invalid_syntax", r.code)

    def test_invalid_argument_literal_string(self):
        r = self.resolver.validate_content("{{ urlencode('db') }}")
        self.assertFalse(r.is_valid)
        self.assertEqual("invalid_argument", r.code)

    def test_malformed_nested_expressions(self):
        for label, content, expected_code, expected_fn in MALFORMED_NESTED_EXPRESSION_CASES:
            with self.subTest(label=label, content=content):
                r = self.resolver.validate_content(content)
                self.assertFalse(r.is_valid)
                self.assertEqual(expected_code, r.code)
                self.assertEqual(expected_fn, r.function_name)

    def test_nested_spacing_variants(self):
        valid_cases = [
            ("S1", "{{  md5( db )  }}"),
            ("S2", "{{  md5( urlencode( db ) )  }}"),
            ("S3", "{{md5( urlencode(db))}}"),
        ]
        for label, content in valid_cases:
            with self.subTest(label=label, content=content):
                r = self.resolver.validate_content(content)
                self.assertTrue(r.is_valid)

        invalid_cases = [
            ("S4", "{{ md5 ( urlencode ( db ) ) }}", "invalid_syntax", None),
            ("S5", "{{md5(urlencode (db))}}", "invalid_argument", "md5"),
        ]
        for label, content, expected_code, expected_fn in invalid_cases:
            with self.subTest(label=label, content=content):
                r = self.resolver.validate_content(content)
                self.assertFalse(r.is_valid)
                self.assertEqual(expected_code, r.code)
                self.assertEqual(expected_fn, r.function_name)

    def test_empty_argument_calls(self):
        for label, content, expected_code, expected_fn in EMPTY_ARGUMENT_CASES:
            with self.subTest(label=label, content=content):
                r = self.resolver.validate_content(content)
                self.assertFalse(r.is_valid)
                self.assertEqual(expected_code, r.code)
                self.assertEqual(expected_fn, r.function_name)

    def test_standalone_malformed_closing_paren(self):
        for label, content, expected_code, expected_fn in (
            STANDALONE_MALFORMED_CLOSING_PAREN_CASES
        ):
            with self.subTest(label=label, content=content):
                r = self.resolver.validate_content(content)
                self.assertFalse(r.is_valid)
                self.assertEqual(expected_code, r.code)
                self.assertEqual(expected_fn, r.function_name)

    def test_multi_placeholder_first_failure(self):
        for label, content, expected_code, expected_fn in (
            MULTI_PLACEHOLDER_FIRST_FAILURE_CASES
        ):
            with self.subTest(label=label, content=content):
                r = self.resolver.validate_content(content)
                self.assertFalse(r.is_valid)
                self.assertEqual(expected_code, r.code)
                self.assertEqual(expected_fn, r.function_name)

    def test_multi_placeholder_first_failure_via_validate_expressions(self):
        cases = [
            (
                "V1",
                ["host", "urlencode(x)", "mystery(y)"],
                "unknown_function",
                "mystery",
            ),
            (
                "V2",
                ["md5(urlencode(db))", "md5()"],
                "invalid_argument",
                "md5",
            ),
        ]
        for label, expressions, expected_code, expected_fn in cases:
            with self.subTest(label=label, expressions=expressions):
                r = self.resolver.validate_expressions(expressions)
                self.assertFalse(r.is_valid)
                self.assertEqual(expected_code, r.code)
                self.assertEqual(expected_fn, r.function_name)

    def test_validation_result_identifies_the_failed_expression(self):
        r = self.resolver.validate_content(
            "{{ to_int(issue_id) }} {{ not_allowed(value) }}"
        )

        self.assertFalse(r.is_valid)
        self.assertEqual("not_allowed(value)", r.expression)

    def test_validate_accepts_safe_mcp_request_path(self):
        """PYPOST-1033: dotted mcp.request.* must validate as a safe path."""
        r = self.resolver.validate_content("{{ mcp.request.issue_key }}")
        self.assertTrue(r.is_valid)

    def test_validate_rejects_unsafe_underscore_attribute_segments(self):
        """PYPOST-1033: underscore-leading attribute segments stay invalid."""
        cases = [
            ("A1", "{{ db.__class__ }}"),
            ("A2", "{{ mcp.request.__class__ }}"),
        ]
        for label, content in cases:
            with self.subTest(label=label, content=content):
                r = self.resolver.validate_content(content)
                self.assertFalse(r.is_valid)
                self.assertEqual("invalid_syntax", r.code)


    def test_env_function_validation_valid(self):
        cases = [
            ("standalone", "{{ env(API_KEY) }}"),
            ("dotted_path", "{{ env(mcp.request.env_var) }}"),
            ("nested_outer", "{{ md5(env(API_KEY)) }}"),
            ("nested_inner", "{{ env(urlencode(var)) }}"),
            ("chain", "{{ base64(md5(env(API_KEY))) }}"),
        ]
        for label, content in cases:
            with self.subTest(label=label, content=content):
                r = self.resolver.validate_content(content)
                self.assertTrue(r.is_valid)

    def test_env_function_validation_invalid(self):
        cases = [
            ("multi_arg", "{{ env(a, b) }}", "invalid_arity", "env"),
            ("empty_arg", "{{ env() }}", "invalid_argument", "env"),
            ("literal_arg", "{{ env('API_KEY') }}", "invalid_argument", "env"),
            ("nested_multi_arg", "{{ md5(env(a, b)) }}", "invalid_argument", "md5"),
        ]
        for label, content, expected_code, expected_fn in cases:
            with self.subTest(label=label, content=content):
                r = self.resolver.validate_content(content)
                self.assertFalse(r.is_valid)
                self.assertEqual(expected_code, r.code)
                self.assertEqual(expected_fn, r.function_name)


if __name__ == "__main__":
    unittest.main()
