import hashlib
import os
import unittest
from unittest.mock import patch

import pytest

from pypost.core.function_expression_resolver import FunctionExpressionResolver
from pypost.core.function_registry import FunctionRegistry
from pypost.core.template_service import TemplateService

pytestmark = pytest.mark.timeout(30)


class TestFunctionArgSafePaths(unittest.TestCase):
    """
    Contract unit tests locking function argument path validation and rendering.

    Specifically verifies safe dotted variable paths (e.g. mcp.request.query)
    and unsafe attribute access paths (e.g. db.__class__) across all catalog
    functions in FunctionExpressionResolver and TemplateService.
    """

    def setUp(self) -> None:
        self.registry = FunctionRegistry()
        self.resolver = FunctionExpressionResolver(self.registry)
        self.template_service = TemplateService()

    def test_resolver_accepts_catalog_functions_with_safe_dotted_args(self) -> None:
        """FunctionExpressionResolver accepts catalog functions with safe dotted arguments."""
        catalog_funcs = ["urlencode", "md5", "base64", "to_int", "env"]
        safe_args = [
            "mcp.request.query",
            "nested.key",
            "a.b.c.d",
            "_leading.safe_prop",
            "request.headers.authorization",
            "data.items.count",
        ]

        for fn in catalog_funcs:
            for arg in safe_args:
                expression = f"{{{{ {fn}({arg}) }}}}"
                with self.subTest(fn=fn, arg=arg, expression=expression):
                    result = self.resolver.validate_content(expression)
                    self.assertTrue(
                        result.is_valid,
                        f"Expected expression '{expression}' to be valid, got code: {result.code}",
                    )

    def test_resolver_accepts_nested_catalog_functions_with_safe_dotted_args(self) -> None:
        """FunctionExpressionResolver accepts nested function calls with safe dotted arguments."""
        cases = [
            ("{{ md5(urlencode(mcp.request.query)) }}"),
            ("{{ base64(md5(payload.data)) }}"),
            ("{{ to_int(env(config.port_key)) }}"),
            ("{{ urlencode(env(mcp.secret_name)) }}"),
            ("{{ base64(urlencode(md5(nested.data.value))) }}"),
        ]
        for expr in cases:
            with self.subTest(expression=expr):
                result = self.resolver.validate_content(expr)
                self.assertTrue(
                    result.is_valid,
                    f"Expected expression '{expr}' to be valid, got code: {result.code}",
                )

    def test_resolver_rejects_catalog_functions_with_unsafe_attribute_paths(self) -> None:
        """FunctionExpressionResolver rejects catalog functions with unsafe attribute access."""
        catalog_funcs = ["urlencode", "md5", "base64", "to_int", "env"]
        unsafe_args = [
            "db.__class__",
            "mcp.request.__class__",
            "data._private",
            "nested.__dict__",
            "obj._hidden.attr",
            "mcp.request.__globals__",
        ]

        for fn in catalog_funcs:
            for arg in unsafe_args:
                expression = f"{{{{ {fn}({arg}) }}}}"
                with self.subTest(fn=fn, arg=arg, expression=expression):
                    result = self.resolver.validate_content(expression)
                    self.assertFalse(
                        result.is_valid,
                        f"Expected expression '{expression}' to be rejected as invalid",
                    )
                    self.assertEqual(
                        "invalid_argument",
                        result.code,
                        f"Expected code 'invalid_argument' for '{expression}', got: {result.code}",
                    )
                    self.assertEqual(
                        fn,
                        result.function_name,
                        f"Expected function_name '{fn}' for '{expression}', got: {result.function_name}",
                    )

    def test_template_service_renders_dotted_paths_as_function_arguments(self) -> None:
        """TemplateService renders dotted paths as function arguments across nested dict variables."""
        variables = {
            "mcp": {
                "request": {
                    "query": "hello world/query&test=1",
                    "body": "payload content for md5",
                    "count": "1042",
                    "env_key": "DYNAMIC_SAFE_ENV_VAR",
                },
                "nested": {
                    "binary_text": "sample text to encode",
                },
            },
        }

        # urlencode
        urlencode_result = self.template_service.render_string(
            "{{ urlencode(mcp.request.query) }}",
            variables,
        )
        self.assertEqual("hello%20world%2Fquery%26test%3D1", urlencode_result)

        # md5
        expected_md5 = hashlib.md5(b"payload content for md5").hexdigest()
        md5_result = self.template_service.render_string(
            "{{ md5(mcp.request.body) }}",
            variables,
        )
        self.assertEqual(expected_md5, md5_result)

        # base64
        base64_result = self.template_service.render_string(
            "{{ base64(mcp.nested.binary_text) }}",
            variables,
        )
        self.assertEqual("c2FtcGxlIHRleHQgdG8gZW5jb2Rl", base64_result)

        # to_int
        to_int_result = self.template_service.render_string(
            "{{ to_int(mcp.request.count) }}",
            variables,
        )
        self.assertEqual("1042", to_int_result)

        # env
        with patch.dict(os.environ, {"DYNAMIC_SAFE_ENV_VAR": "secret-token-value"}):
            env_result = self.template_service.render_string(
                "{{ env(mcp.request.env_key) }}",
                variables,
            )
            self.assertEqual("secret-token-value", env_result)

    def test_template_service_renders_nested_function_calls_with_dotted_paths(self) -> None:
        """TemplateService renders nested function calls with dotted arguments."""
        variables = {
            "mcp": {
                "request": {
                    "path_val": "foo bar/baz",
                },
            },
        }
        # urlencode then md5
        # urlencode("foo bar/baz") -> "foo%20bar%2Fbaz"
        expected_hash = hashlib.md5(b"foo%20bar%2Fbaz").hexdigest()
        rendered = self.template_service.render_string(
            "{{ md5(urlencode(mcp.request.path_val)) }}",
            variables,
        )
        self.assertEqual(expected_hash, rendered)


if __name__ == "__main__":
    unittest.main()
