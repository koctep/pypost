import pytest

pytestmark = pytest.mark.timeout(30)

import unittest

from pypost.core.template_expression_tokenizer import tokenize_template_expressions


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
