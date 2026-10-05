"""Automated failing repro tests for PYPOST-1261.

Reproduces parser and resolver misalignment where malformed nested calls,
unclosed parentheses, and extraneous closing parentheses were misclassified
as invalid_arity instead of invalid_argument.
"""
import unittest
from unittest.mock import MagicMock

import pytest

from pypost.core import template_expression_parser
from pypost.core.function_expression_resolver import FunctionExpressionResolver
from pypost.core.function_registry import FunctionRegistry
from pypost.core.template_service import TemplateService

pytestmark = pytest.mark.timeout(30)


class TestFunctionExpressionResolverMalformedRepro(unittest.TestCase):
    """Reproduction tests for FunctionExpressionResolver error classification."""

    def setUp(self) -> None:
        self.registry = FunctionRegistry()
        self.resolver = FunctionExpressionResolver(self.registry)

    @pytest.mark.timeout(30)
    def test_malformed_nested_unclosed_parenthesis_reports_invalid_argument(self) -> None:
        """Case M1: unclosed nested call must report invalid_argument for outer function."""
        # '{{ md5(urlencode(db) }}' missing closing paren for urlencode
        result = self.resolver.validate_content("{{ md5(urlencode(db) }}")
        self.assertFalse(result.is_valid)
        self.assertEqual("invalid_argument", result.code)
        self.assertEqual("md5", result.function_name)

    @pytest.mark.timeout(30)
    def test_malformed_nested_extra_closing_parenthesis_attributes_inner_call(self) -> None:
        """Case M2: extra closing paren inside nested call attributes invalid_argument to inner."""
        # '{{ md5(urlencode(db))) }}' has extraneous closing paren on urlencode
        result = self.resolver.validate_content("{{ md5(urlencode(db))) }}")
        self.assertFalse(result.is_valid)
        self.assertEqual("invalid_argument", result.code)
        self.assertEqual("urlencode", result.function_name)

    @pytest.mark.timeout(30)
    def test_malformed_deeply_nested_unclosed_parenthesis_reports_invalid_argument(self) -> None:
        """Case M4: 3-level chain with unclosed paren reports invalid_argument.

        Outer function should receive the invalid_argument error.
        """
        result = self.resolver.validate_content("{{ base64(md5(urlencode(db) }}")
        self.assertFalse(result.is_valid)
        self.assertEqual("invalid_argument", result.code)
        self.assertEqual("base64", result.function_name)

    @pytest.mark.timeout(30)
    def test_standalone_extra_closing_parenthesis_reports_invalid_argument(self) -> None:
        """Cases P1 & P2: standalone calls with extra closing paren report invalid_argument."""
        cases = [("{{ urlencode(db)) }}", "urlencode"), ("{{ md5(x)) }}", "md5")]
        for expr, expected_fn in cases:
            with self.subTest(expression=expr):
                result = self.resolver.validate_content(expr)
                self.assertFalse(result.is_valid)
                self.assertEqual("invalid_argument", result.code)
                self.assertEqual(expected_fn, result.function_name)

    @pytest.mark.timeout(30)
    def test_legitimate_multi_argument_reports_invalid_arity(self) -> None:
        """True multi-argument calls must still be rejected as invalid_arity."""
        result = self.resolver.validate_content("{{ urlencode(a, b) }}")
        self.assertFalse(result.is_valid)
        self.assertEqual("invalid_arity", result.code)
        self.assertEqual("urlencode", result.function_name)


class TestTemplateServiceAlignmentRepro(unittest.TestCase):
    """Reproduction tests for TemplateService validation and observability alignment."""

    def setUp(self) -> None:
        self.metrics = MagicMock()
        self.svc = TemplateService(metrics=self.metrics)

    @pytest.mark.timeout(30)
    def test_template_service_validate_malformed_nested(self) -> None:
        """TemplateService.validate_function_expressions must report invalid_argument."""
        result = self.svc.validate_function_expressions("{{ md5(urlencode(db) }}")
        self.assertFalse(result.is_valid)
        self.assertEqual("invalid_argument", result.code)
        self.assertEqual("md5", result.function_name)

    @pytest.mark.timeout(30)
    def test_template_service_observability_hover_tracks_invalid_argument(self) -> None:
        """Hover render of malformed nested call must track invalid_argument telemetry metric."""
        content = "{{ md5(urlencode(db) }}"
        result = self.svc.render_string(content, {"db": "x"}, render_path="hover")
        self.assertEqual(content, result)
        self.metrics.track_template_expression_validation_failure.assert_called_with(
            render_path="hover", code="invalid_argument", function_name="md5",
        )


class TestArgumentParsingContractRepro(unittest.TestCase):
    """Reproduction tests for the argument parsing contract defined in 20-architecture.md."""

    @pytest.mark.timeout(30)
    def test_parse_function_argument_interface_distinguishes_arity_and_malformation(self) -> None:
        """Contract: parse_function_argument must distinguish arity from syntax error."""
        parse_fn = getattr(template_expression_parser, "parse_function_argument", None)
        self.assertIsNotNone(
            parse_fn,
            "parse_function_argument must be implemented per 20-architecture.md",
        )
        # Verify contract on malformed vs multi-argument strings
        res_malformed = parse_fn("urlencode(db")
        self.assertTrue(res_malformed.is_malformed)
        self.assertFalse(res_malformed.has_multiple_arguments)

        res_multi = parse_fn("a, b")
        self.assertFalse(res_multi.is_malformed)
        self.assertTrue(res_multi.has_multiple_arguments)


if __name__ == "__main__":
    unittest.main()
