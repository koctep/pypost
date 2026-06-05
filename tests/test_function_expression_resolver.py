import unittest

from pypost.core.function_expression_resolver import (
    NESTED_FUNCTION_CALLS_ALLOWED,
    FunctionExpressionResolver,
)
from pypost.core.function_registry import FunctionRegistry


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


if __name__ == "__main__":
    unittest.main()
