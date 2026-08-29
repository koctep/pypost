import pytest

import unittest

from pypost.core.template_expression_tokenizer import (
    LOOSE_PLAIN_VARIABLE_PATTERN,
    PLAIN_VARIABLE_PATTERN,
    TEMPLATE_PLACEHOLDER_PATTERN,
    extract_loose_plain_variable_name,
    extract_plain_variable_name,
    is_loose_plain_variable_token,
    is_plain_variable_token,
    tokenize_template_expressions,
)

pytestmark = pytest.mark.timeout(30)


class TestTemplateExpressionTokenizer(unittest.TestCase):
    def test_empty_content(self):
        self.assertEqual(tokenize_template_expressions(""), [])

    def test_no_placeholders(self):
        self.assertEqual(tokenize_template_expressions("plain text"), [])

    def test_single_placeholder(self):
        self.assertEqual(tokenize_template_expressions("{{ host }}"), ["host"])

    def test_multiple_placeholders(self):
        content = "{{ a }} {{ b }} {{ urlencode(c) }}"
        self.assertEqual(
            tokenize_template_expressions(content),
            ["a", "b", "urlencode(c)"],
        )

    def test_whitespace_inside_delimiters(self):
        self.assertEqual(
            tokenize_template_expressions("{{  md5( db )  }}"),
            ["md5( db )"],
        )

    def test_nested_function_call(self):
        self.assertEqual(
            tokenize_template_expressions("{{ md5(urlencode(db)) }}"),
            ["md5(urlencode(db))"],
        )


class TestPlainVariablePattern(unittest.TestCase):
    def test_plain_pattern_matches_simple_name(self):
        self.assertTrue(is_plain_variable_token("{{host}}"))
        self.assertEqual(extract_plain_variable_name("{{host}}"), "host")

    def test_plain_pattern_rejects_whitespace_inside(self):
        whitespace_samples = [
            "{{ host }}",
            "{{ host}}",
            "{{host }}",
            "{{  host  }}",
            "{{\thost\t}}",
            "{{\n  host\n}}",
            "{{ \t\nhost\n\t }}",
        ]
        for token in whitespace_samples:
            with self.subTest(token=token):
                self.assertFalse(is_plain_variable_token(token))
                self.assertIsNone(extract_plain_variable_name(token))

    def test_plain_pattern_rejects_function_call(self):
        self.assertFalse(is_plain_variable_token("{{urlencode(db)}}"))
        self.assertIsNone(extract_plain_variable_name("{{urlencode(db)}}"))

    def test_plain_pattern_allows_underscore_name(self):
        self.assertEqual(extract_plain_variable_name("{{my_var}}"), "my_var")

    def test_loose_plain_pattern_accepts_whitespace_variations(self):
        valid_samples = [
            ("{{host}}", "host"),
            ("{{ host }}", "host"),
            ("{{ host}}", "host"),
            ("{{host }}", "host"),
            ("{{  host  }}", "host"),
            ("{{\thost\t}}", "host"),
            ("{{\n  my_var\n}}", "my_var"),
        ]
        for token, expected_name in valid_samples:
            with self.subTest(token=token):
                self.assertTrue(is_loose_plain_variable_token(token))
                self.assertEqual(extract_loose_plain_variable_name(token), expected_name)

    def test_loose_plain_pattern_rejects_invalid_tokens_and_functions(self):
        invalid_samples = [
            "{{urlencode(db)}}",
            "{{ md5(db) }}",
            "{{ foo + bar }}",
            "{{ }}",
            "{{}}",
            "not a template",
        ]
        for token in invalid_samples:
            with self.subTest(token=token):
                self.assertFalse(is_loose_plain_variable_token(token))
                self.assertIsNone(extract_loose_plain_variable_name(token))

    def test_variable_pattern_alias_matches_shared_export(self):
        from pypost.ui.widgets.mixins import VariableHoverHelper

        self.assertIs(VariableHoverHelper.VARIABLE_PATTERN, PLAIN_VARIABLE_PATTERN)

    def test_expression_pattern_differs_from_plain_pattern(self):
        text = "{{host}} {{ urlencode(db) }}"
        plain_names = PLAIN_VARIABLE_PATTERN.findall(text)
        loose_names = LOOSE_PLAIN_VARIABLE_PATTERN.findall(text)
        all_inner = [
            match.group(1) for match in TEMPLATE_PLACEHOLDER_PATTERN.finditer(text)
        ]
        self.assertEqual(plain_names, ["host"])
        self.assertEqual(loose_names, ["host"])
        self.assertEqual(all_inner, ["host", "urlencode(db)"])
