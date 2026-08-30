"""
Failing repro test suite for PYPOST-1120.

Validates that:
1. ExpressionFailureProvenance class exists in template_expression_types and is
   integrated with ValidationResult.
2. FunctionRegistry provides is_strict_conversion(func_name) metadata.
3. FunctionExpressionResolver provides inspect_failure_provenance(...) returning
   structured failure provenance.
4. TemplateService has NO _DIRECT_TO_INT_CALL_RE or _STARTED_TO_INT_CALL_RE
   class or instance attributes, relying entirely on structured resolver provenance.
5. Nested strict function calls (e.g. {{ md5(to_int(bad)) }}) and mixed templates
   correctly report strict conversion failure provenance and fail closed in
   render_string_strict_conversion.
"""

from __future__ import annotations

import logging
import unittest
import pytest

from pypost.core.function_registry import FunctionRegistry
from pypost.core.function_expression_resolver import FunctionExpressionResolver
from pypost.core.template_expression_types import (
    IntegerConversionError,
    ValidationResult,
)
from pypost.core.template_service import TemplateService

pytestmark = pytest.mark.timeout(60)


class TestTemplateServiceStrictProvenanceRepro(unittest.TestCase):
    """Repro tests asserting required contracts and behavior for PYPOST-1120."""

    def test_expression_failure_provenance_type_exists(self) -> None:
        """Assert ExpressionFailureProvenance exists in template_expression_types."""
        import pypost.core.template_expression_types as types_mod

        self.assertTrue(
            hasattr(types_mod, "ExpressionFailureProvenance"),
            "ExpressionFailureProvenance class must exist in template_expression_types",
        )
        cls = getattr(types_mod, "ExpressionFailureProvenance")
        provenance = cls(
            code="conversion_error",
            expression="to_int(bad)",
            function_name="to_int",
            is_strict=True,
        )
        self.assertEqual(provenance.code, "conversion_error")
        self.assertEqual(provenance.expression, "to_int(bad)")
        self.assertEqual(provenance.function_name, "to_int")
        self.assertTrue(provenance.is_strict)

    def test_validation_result_carries_provenance_failures(self) -> None:
        """Assert ValidationResult carries structured provenance failures and has_strict_failure."""
        valid_result = ValidationResult.valid()
        self.assertTrue(
            hasattr(valid_result, "failures"),
            "ValidationResult must provide a 'failures' tuple attribute",
        )
        self.assertEqual(valid_result.failures, ())
        self.assertTrue(
            hasattr(valid_result, "has_strict_failure"),
            "ValidationResult must provide a 'has_strict_failure' boolean property",
        )
        self.assertFalse(valid_result.has_strict_failure)

    def test_function_registry_provides_strict_conversion_metadata(self) -> None:
        """Assert FunctionRegistry provides is_strict_conversion(name) metadata."""
        registry = FunctionRegistry()
        self.assertTrue(
            hasattr(registry, "is_strict_conversion"),
            "FunctionRegistry must provide is_strict_conversion(name: str) -> bool",
        )
        self.assertTrue(
            registry.is_strict_conversion("to_int"),
            "'to_int' must be recognized as a strict conversion function",
        )
        self.assertFalse(
            registry.is_strict_conversion("md5"),
            "'md5' must not be recognized as a strict conversion function",
        )
        self.assertFalse(
            registry.is_strict_conversion("urlencode"),
            "'urlencode' must not be recognized as a strict conversion function",
        )
        self.assertFalse(
            registry.is_strict_conversion("unknown_function"),
            "Unknown function must not be recognized as strict conversion",
        )

    def test_resolver_inspect_failure_provenance_multi_expression(self) -> None:
        """Assert resolver inspects content and returns structured failure provenance."""
        registry = FunctionRegistry()
        resolver = FunctionExpressionResolver(registry)
        self.assertTrue(
            hasattr(resolver, "inspect_failure_provenance")
            or hasattr(resolver, "inspect_content_failures"),
            "FunctionExpressionResolver must provide inspect_failure_provenance method",
        )
        inspect_fn = getattr(
            resolver,
            "inspect_failure_provenance",
            getattr(resolver, "inspect_content_failures", None),
        )
        content = "{{not_allowed(x)}}/{{to_int(42, 99)}}"
        failures = inspect_fn(content)
        self.assertEqual(
            len(failures),
            2,
            "Resolver must capture provenance for both failed placeholders",
        )
        self.assertEqual(failures[0].function_name, "not_allowed")
        self.assertEqual(failures[0].code, "unknown_function")
        self.assertFalse(failures[0].is_strict)

        self.assertEqual(failures[1].function_name, "to_int")
        self.assertEqual(failures[1].code, "invalid_arity")
        self.assertTrue(failures[1].is_strict)

    def test_resolver_inspect_failure_provenance_unclosed_placeholder(self) -> None:
        """Assert FunctionExpressionResolver inspects unclosed placeholders for strict functions."""
        registry = FunctionRegistry()
        resolver = FunctionExpressionResolver(registry)
        inspect_fn = getattr(
            resolver,
            "inspect_failure_provenance",
            getattr(resolver, "inspect_content_failures", None),
        )
        self.assertIsNotNone(
            inspect_fn,
            "FunctionExpressionResolver must provide inspect_failure_provenance",
        )
        failures = inspect_fn("{{to_int(unclosed")
        self.assertTrue(
            len(failures) >= 1,
            "Resolver must return provenance for unclosed strict placeholder",
        )
        self.assertEqual(failures[0].function_name, "to_int")
        self.assertTrue(failures[0].is_strict)

    def test_template_service_has_no_regex_coupling_attributes(self) -> None:
        """Assert TemplateService has no regex coupling attributes for to_int."""
        self.assertFalse(
            hasattr(TemplateService, "_DIRECT_TO_INT_CALL_RE"),
            "TemplateService class must not define regex attribute _DIRECT_TO_INT_CALL_RE",
        )
        self.assertFalse(
            hasattr(TemplateService, "_STARTED_TO_INT_CALL_RE"),
            "TemplateService class must not define regex attribute _STARTED_TO_INT_CALL_RE",
        )
        svc = TemplateService()
        self.assertFalse(
            hasattr(svc, "_DIRECT_TO_INT_CALL_RE"),
            "TemplateService instance must not have _DIRECT_TO_INT_CALL_RE attribute",
        )
        self.assertFalse(
            hasattr(svc, "_STARTED_TO_INT_CALL_RE"),
            "TemplateService instance must not have _STARTED_TO_INT_CALL_RE attribute",
        )

    def test_nested_strict_conversion_fails_closed_in_mixed_template(self) -> None:
        """Assert nested strict function calls fail closed in strict rendering."""
        svc = TemplateService()
        content = "{{not_allowed(dummy)}}/{{md5(to_int(val))}}"
        with self.assertRaises(
            IntegerConversionError,
            msg=(
                "Strict conversion must fail closed on nested to_int failure "
                "despite outer non-strict function"
            ),
        ):
            svc.render_string_strict_conversion(
                content,
                {"val": "not-an-int", "dummy": "x"},
            )

    def test_resolver_logs_strict_failure_provenance_without_secrets(self) -> None:
        """Assert FunctionExpressionResolver emits structured debug logs without secrets."""
        registry = FunctionRegistry()
        resolver = FunctionExpressionResolver(registry)
        secret_content = "{{to_int(my_super_secret_password_123, extra)}}"

        with self.assertLogs("pypost.core.function_expression_resolver", level=logging.DEBUG) as cm:
            resolver.inspect_failure_provenance(secret_content)

        output = "\n".join(cm.output)
        self.assertIn("strict_conversion_failure_provenance_detected", output)
        self.assertIn("function_name=to_int", output)
        self.assertNotIn("my_super_secret_password_123", output)

    def test_template_service_logs_strict_failure_propagation_without_secrets(self) -> None:
        """Assert TemplateService emits structured logs on strict conversion failure without secrets."""
        svc = TemplateService()
        secret_content = "{{to_int(my_super_secret_key)}}"
        secret_vars = {"my_super_secret_key": "not-an-integer-secret-token"}

        with self.assertLogs("pypost.core.template_service", level=logging.DEBUG) as cm:
            with self.assertRaises(IntegerConversionError):
                svc.render_string_strict_conversion(secret_content, secret_vars)

        output = "\n".join(cm.output)
        self.assertIn("strict_conversion_failure_identified", output)
        self.assertIn("strict_conversion_failure_propagated", output)
        self.assertNotIn("not-an-integer-secret-token", output)

