import pytest

import unittest
from functools import lru_cache
from unittest.mock import MagicMock, call, patch

import jinja2.nodes

from pypost.core.template_service import TemplateService
from pypost.core.template_expression_types import IntegerConversionError
from pypost.core.template_service_render import (
    fallback_content_after_render_exception,
    render_with_jinja,
)
from tests.test_function_expression_resolver import MALFORMED_NESTED_EXPRESSION_CASES

pytestmark = pytest.mark.timeout(30)


class TestTemplateServiceRenderString(unittest.TestCase):
    def setUp(self):
        self.svc = TemplateService()

    def test_render_known_variable(self):
        result = self.svc.render_string("Hello {{ name }}", {"name": "World"})
        self.assertEqual("Hello World", result)

    def test_render_unknown_variable_renders_empty_string(self):
        result = self.svc.render_string("{{ missing }}", {})
        self.assertEqual("", result)

    def test_render_urlencode_function_with_variable_argument(self):
        result = self.svc.render_string("{{urlencode(db)}}", {"db": "a b/c"})
        self.assertEqual("a%20b%2Fc", result)

    def test_render_urlencode_function_in_mixed_text(self):
        result = self.svc.render_string("/{{host}}/{{urlencode(db)}}", {
            "host": "localhost",
            "db": "hello world",
        })
        self.assertEqual("/localhost/hello%20world", result)

    def test_render_md5_function_with_variable_argument(self):
        result = self.svc.render_string("{{md5(db)}}", {"db": "hello"})
        self.assertEqual("5d41402abc4b2a76b9719d911017c592", result)

    def test_render_base64_function_with_variable_argument(self):
        result = self.svc.render_string("{{base64(db)}}", {"db": "hello"})
        self.assertEqual("aGVsbG8=", result)

    def test_render_to_int_function_with_single_value_argument(self):
        content = "{{to_int(value)}}"
        validation = self.svc.validate_function_expressions(content)
        self.assertTrue(validation.is_valid)
        self.assertEqual("42", self.svc.render_string(content, {"value": "42"}))

    def test_render_to_int_valid_decimal_grammar(self):
        cases = {
            "plain": ("42", "42"),
            "positive": ("+42", "42"),
            "negative": ("-42", "-42"),
        }
        for label, (value, expected) in cases.items():
            with self.subTest(label=label):
                self.assertEqual(
                    expected,
                    self.svc.render_string("{{to_int(value)}}", {"value": value}),
                )

    def test_render_to_int_accepts_native_integer_but_not_bool_or_float(self):
        """PYPOST-1038 R2: match the MCP integer-or-decimal-string union exactly."""
        content = "{{to_int(value)}}"

        self.assertEqual("42", self.svc.render_string(content, {"value": 42}))
        for invalid_value in (True, 42.0):
            with self.subTest(value=invalid_value):
                self.assertEqual(
                    content,
                    self.svc.render_string(content, {"value": invalid_value}),
                )

    def test_render_to_int_rejects_invalid_input_grammar(self):
        cases = {
            "empty": "",
            "leading_whitespace": " 42",
            "trailing_whitespace": "42 ",
            "decimal": "42.0",
            "exponent": "1e2",
            "underscore": "1_000",
            "boolean_like": "true",
            "boolean_object": True,
            "none": None,
            "object": {"id": "42"},
        }
        content = "{{to_int(value)}}"
        for label, value in cases.items():
            with self.subTest(label=label):
                self.assertEqual(content, self.svc.render_string(content, {"value": value}))

    def test_strict_conversion_keeps_literal_fallback_for_unrelated_failed_token(self):
        content = "{{to_int(issue_id)}}/{{not_allowed(value)}}"

        self.assertEqual(
            content,
            self.svc.render_string_strict_conversion(
                content,
                {"issue_id": "42", "value": "ignored"},
            ),
        )

    def test_strict_conversion_checks_later_direct_to_int_after_unrelated_failure(self):
        content = "{{not_allowed(value)}}/{{to_int(issue_id)}}"

        with self.assertRaisesRegex(
            IntegerConversionError,
            "Invalid to_int template expression",
        ):
            self.svc.render_string_strict_conversion(
                content,
                {"value": "ignored", "issue_id": "not-an-int"},
            )

    def test_render_mixed_variant_b_functions(self):
        result = self.svc.render_string(
            "/{{host}}/{{urlencode(db)}}/{{md5(secret)}}/{{base64(db)}}",
            {
                "host": "localhost",
                "db": "hello world",
                "secret": "abc",
            },
        )
        self.assertEqual(
            "/localhost/hello%20world/900150983cd24fb0d6963f7d28e17f72/aGVsbG8gd29ybGQ=",
            result,
        )

    def test_render_unknown_function_returns_original_content(self):
        content = "{{not_allowed(db)}}"
        result = self.svc.render_string(content, {"db": "x"})
        self.assertEqual(content, result)

    def test_render_nested_function_with_allowed_catalog(self):
        content = "{{md5(urlencode(db))}}"
        result = self.svc.render_string(content, {"db": "a b"})
        self.assertEqual("4c85f5eb3a20b8ad41bddfdd57ff6347", result)

    def test_catalog_allow_list_matches_jinja_globals(self):
        """TemplateService init binds every catalog name on env.globals."""
        registry = self.svc._function_registry
        for name in registry.allowed_names():
            self.assertIn(name, self.svc.env.globals)
            self.assertIs(self.svc.env.globals[name], registry.get(name))

    def test_runtime_hover_parity_nested_valid(self):
        content = "{{md5(urlencode(db))}}"
        variables = {"db": "a b"}
        expected = "4c85f5eb3a20b8ad41bddfdd57ff6347"
        for render_path in ("runtime", "hover"):
            with self.subTest(render_path=render_path):
                result = self.svc.render_string(
                    content, variables, render_path=render_path,
                )
                self.assertEqual(expected, result)

    def test_runtime_hover_parity_valid_spaced_nested(self):
        nested_hash = "4c85f5eb3a20b8ad41bddfdd57ff6347"
        cases = [
            ("S1", "{{  md5( db )  }}", "0cc9cd4dd26c5137b675a0d819cb9ab0"),
            ("S2", "{{  md5( urlencode( db ) )  }}", nested_hash),
            ("S3", "{{md5( urlencode(db))}}", nested_hash),
        ]
        variables = {"db": "a b"}
        for label, content, expected in cases:
            for render_path in ("runtime", "hover"):
                with self.subTest(label=label, render_path=render_path):
                    result = self.svc.render_string(
                        content, variables, render_path=render_path,
                    )
                    self.assertEqual(expected, result)

    def test_runtime_hover_parity_malformed_nested(self):
        variables = {"db": "a b"}
        for label, content, *_ in MALFORMED_NESTED_EXPRESSION_CASES:
            for render_path in ("runtime", "hover"):
                with self.subTest(label=label, render_path=render_path):
                    result = self.svc.render_string(
                        content, variables, render_path=render_path,
                    )
                    self.assertEqual(content, result)

    def test_runtime_hover_parity_invalid_spacing(self):
        cases = [
            ("S4", "{{ md5 ( urlencode ( db ) ) }}"),
            ("S5", "{{md5(urlencode (db))}}"),
        ]
        variables = {"db": "a b"}
        for label, content in cases:
            for render_path in ("runtime", "hover"):
                with self.subTest(label=label, render_path=render_path):
                    result = self.svc.render_string(
                        content, variables, render_path=render_path,
                    )
                    self.assertEqual(content, result)

    def test_render_rejects_nested_unknown(self):
        content = "{{md5(bad(db))}}"
        result = self.svc.render_string(content, {"db": "a b"})
        self.assertEqual(content, result)

    def test_render_multi_argument_function_returns_original_content(self):
        content = "{{urlencode(db, host)}}"
        result = self.svc.render_string(content, {"db": "hello", "host": "localhost"})
        self.assertEqual(content, result)

    def test_render_function_with_malformed_parenthesis_returns_original_content(self):
        content = "{{urlencode(db}}"
        result = self.svc.render_string(content, {"db": "hello"})
        self.assertEqual(content, result)

    def test_render_function_with_literal_argument_returns_original_content(self):
        content = "{{urlencode('db')}}"
        result = self.svc.render_string(content, {"db": "hello"})
        self.assertEqual(content, result)

    def test_render_preserves_backward_compatible_fallback_for_typed_outcomes(self):
        cases = [
            "{{not_allowed(db)}}",
            "{{urlencode(db, host)}}",
            "{{urlencode('db')}}",
            "{{urlencode(db}}",
        ]
        variables = {"db": "hello", "host": "localhost"}
        for content in cases:
            with self.subTest(content=content):
                self.assertEqual(content, self.svc.render_string(content, variables))

    def test_render_none_returns_empty_string(self):
        result = self.svc.render_string(None, {})
        self.assertEqual("", result)

    def test_render_empty_string_returns_empty_string(self):
        result = self.svc.render_string("", {})
        self.assertEqual("", result)

    def test_render_invalid_syntax_returns_original_content(self):
        content = "{{ unclosed"
        result = self.svc.render_string(content, {})
        self.assertEqual(content, result)

    def test_render_jinja_filter_form_returns_original_content(self):
        content = "{{ db|upper }}"
        result = self.svc.render_string(content, {"db": "secret"})
        self.assertEqual(content, result)

    def test_render_attribute_access_form_returns_original_content(self):
        content = "{{ db.__class__ }}"
        result = self.svc.render_string(content, {"db": "secret"})
        self.assertEqual(content, result)

    def test_render_nested_mcp_request_variable(self):
        """PYPOST-1033: nested mcp.request dict must substitute placeholders."""
        result = self.svc.render_string(
            "{{ mcp.request.issue_key }}",
            {"mcp": {"request": {"issue_key": "PROJ-1"}}},
        )
        self.assertEqual("PROJ-1", result)


class TestTemplateServiceVariableTypes(unittest.TestCase):
    """PYPOST-145: render_string with non-string variable values."""

    def setUp(self):
        self.svc = TemplateService()

    def test_render_integer_variable(self):
        result = self.svc.render_string("port={{port}}/api", {"port": 8080})
        self.assertEqual("port=8080/api", result)

    def test_render_float_variable(self):
        result = self.svc.render_string("v={{ratio}}", {"ratio": 3.14})
        self.assertEqual("v=3.14", result)

    def test_render_boolean_variables(self):
        for value, expected in [(True, "True"), (False, "False")]:
            with self.subTest(value=value):
                result = self.svc.render_string("{{flag}}", {"flag": value})
                self.assertEqual(expected, result)

    def test_render_none_variable_value(self):
        result = self.svc.render_string("x={{value}}y", {"value": None})
        self.assertEqual("x=Noney", result)

    def test_render_catalog_function_with_integer_argument(self):
        result = self.svc.render_string("{{urlencode(port)}}", {"port": 8080})
        self.assertEqual("8080", result)

    def test_render_mixed_type_variables_in_one_template(self):
        result = self.svc.render_string(
            "{{host}}:{{port}}/{{enabled}}",
            {"host": "localhost", "port": 443, "enabled": True},
        )
        self.assertEqual("localhost:443/True", result)


class TestTemplateServiceSingleEnvironment(unittest.TestCase):
    """PYPOST-146: one jinja2.Environment per TemplateService instance."""

    def test_single_environment_shared_by_render_and_parse(self):
        svc = TemplateService()
        env = svc.env
        svc.render_string("{{ x }}", {"x": "value"})
        svc.parse("{{ x }}")
        self.assertIs(svc.env, env)


class TestTemplateServiceParse(unittest.TestCase):
    def setUp(self):
        self.svc = TemplateService()

    def test_parse_valid_template_returns_ast(self):
        ast = self.svc.parse("Hello {{ name }}")
        self.assertIsInstance(ast, jinja2.nodes.Template)


class TestTemplateServiceValidationOutcomes(unittest.TestCase):
    def setUp(self):
        self.svc = TemplateService()

    def test_validate_reports_unknown_function(self):
        result = self.svc.validate_function_expressions("{{not_allowed(db)}}")
        self.assertFalse(result.is_valid)
        self.assertEqual("unknown_function", result.code)
        self.assertEqual(result.function_name, "not_allowed")

    def test_validate_reports_invalid_arity(self):
        result = self.svc.validate_function_expressions("{{urlencode(db, host)}}")
        self.assertFalse(result.is_valid)
        self.assertEqual("invalid_arity", result.code)

    def test_validate_allows_plain_identifier(self):
        result = self.svc.validate_function_expressions("{{name}}")
        self.assertTrue(result.is_valid)

    def test_validate_allows_nested_allowed_calls(self):
        result = self.svc.validate_function_expressions("{{md5(urlencode(db))}}")
        self.assertTrue(result.is_valid)

    def test_validate_rejects_nested_unknown(self):
        result = self.svc.validate_function_expressions("{{md5(bad(db))}}")
        self.assertFalse(result.is_valid)
        self.assertEqual("unknown_function", result.code)
        self.assertEqual("bad", result.function_name)

    def test_validate_reports_invalid_argument(self):
        result = self.svc.validate_function_expressions("{{urlencode('db')}}")
        self.assertFalse(result.is_valid)
        self.assertEqual("invalid_argument", result.code)

    def test_validate_reports_invalid_syntax(self):
        result = self.svc.validate_function_expressions("{{urlencode(db}}")
        self.assertFalse(result.is_valid)
        self.assertEqual("invalid_syntax", result.code)

    def test_validate_rejects_jinja_filter_form(self):
        result = self.svc.validate_function_expressions("{{ db|md5 }}")
        self.assertFalse(result.is_valid)
        self.assertEqual("invalid_syntax", result.code)

    def test_validate_rejects_attribute_access_form(self):
        result = self.svc.validate_function_expressions("{{ db.__class__ }}")
        self.assertFalse(result.is_valid)
        self.assertEqual("invalid_syntax", result.code)

    def test_validate_malformed_nested_alignment(self):
        for label, content, expected_code, expected_fn in MALFORMED_NESTED_EXPRESSION_CASES:
            with self.subTest(label=label, content=content):
                result = self.svc.validate_function_expressions(content)
                self.assertFalse(result.is_valid)
                self.assertEqual(expected_code, result.code)
                self.assertEqual(expected_fn, result.function_name)


class TestTemplateServiceObservability(unittest.TestCase):
    def setUp(self):
        self.metrics = MagicMock()
        self.svc = TemplateService(metrics=self.metrics)

    def test_render_success_tracks_success_metric(self):
        result = self.svc.render_string("{{urlencode(db)}}", {"db": "a b"}, render_path="runtime")
        self.assertEqual("a%20b", result)
        self.metrics.track_template_expression_render_attempt.assert_called_with(
            render_path="runtime", outcome="success",
        )

    def test_render_validation_failure_tracks_validation_metrics(self):
        content = "{{not_allowed(db)}}"
        result = self.svc.render_string(content, {"db": "x"}, render_path="runtime")
        self.assertEqual(content, result)
        self.metrics.track_template_expression_render_attempt.assert_any_call(
            render_path="runtime", outcome="validation_error",
        )
        self.assertNotIn(
            call(render_path="runtime", outcome="render_error"),
            self.metrics.track_template_expression_render_attempt.call_args_list,
        )
        self.metrics.track_template_expression_validation_failure.assert_called_with(
            render_path="runtime", code="unknown_function", function_name="not_allowed",
        )

    def test_render_nested_validation_failure_tracks_validation_metrics(self):
        content = "{{md5(bad(db))}}"
        result = self.svc.render_string(content, {"db": "x"}, render_path="hover")
        self.assertEqual(content, result)
        self.metrics.track_template_expression_render_attempt.assert_any_call(
            render_path="hover", outcome="validation_error",
        )
        self.assertNotIn(
            call(render_path="hover", outcome="render_error"),
            self.metrics.track_template_expression_render_attempt.call_args_list,
        )
        self.metrics.track_template_expression_validation_failure.assert_called_with(
            render_path="hover", code="unknown_function", function_name="bad",
        )

    def test_render_nested_success_tracks_success_metric(self):
        result = self.svc.render_string(
            "{{md5(urlencode(db))}}", {"db": "a b"}, render_path="hover",
        )
        self.assertEqual("4c85f5eb3a20b8ad41bddfdd57ff6347", result)
        self.metrics.track_template_expression_render_attempt.assert_called_with(
            render_path="hover", outcome="success",
        )

    def test_render_malformed_nested_validation_failure_tracks_validation_metrics_on_hover(
        self,
    ):
        content = "{{ md5(urlencode(db) }}"
        result = self.svc.render_string(content, {"db": "x"}, render_path="hover")
        self.assertEqual(content, result)
        self.metrics.track_template_expression_render_attempt.assert_any_call(
            render_path="hover", outcome="validation_error",
        )
        self.assertNotIn(
            call(render_path="hover", outcome="render_error"),
            self.metrics.track_template_expression_render_attempt.call_args_list,
        )
        self.metrics.track_template_expression_validation_failure.assert_called_with(
            render_path="hover", code="invalid_argument", function_name="md5",
        )

    def test_render_invalid_spacing_validation_failure_tracks_validation_metrics_on_hover(
        self,
    ):
        cases = [
            ("S4", "{{ md5 ( urlencode ( db ) ) }}", "invalid_syntax", None),
            ("S5", "{{md5(urlencode (db))}}", "invalid_argument", "md5"),
        ]
        for label, content, expected_code, expected_fn in cases:
            with self.subTest(label=label):
                self.metrics.reset_mock()
                result = self.svc.render_string(
                    content, {"db": "x"}, render_path="hover",
                )
                self.assertEqual(content, result)
                self.metrics.track_template_expression_render_attempt.assert_any_call(
                    render_path="hover", outcome="validation_error",
                )
                self.assertNotIn(
                    call(render_path="hover", outcome="render_error"),
                    self.metrics.track_template_expression_render_attempt.call_args_list,
                )
                self.metrics.track_template_expression_validation_failure.assert_called_with(
                    render_path="hover",
                    code=expected_code,
                    function_name=expected_fn,
                )

    def test_render_spaced_nested_success_tracks_success_metric_on_hover(self):
        result = self.svc.render_string(
            "{{  md5( urlencode( db ) )  }}", {"db": "a b"}, render_path="hover",
        )
        self.assertEqual("4c85f5eb3a20b8ad41bddfdd57ff6347", result)
        self.metrics.track_template_expression_render_attempt.assert_called_with(
            render_path="hover", outcome="success",
        )

    def test_render_empty_content_tracks_metric(self):
        result = self.svc.render_string("", {}, render_path="hover")
        self.assertEqual("", result)
        self.metrics.track_template_expression_render_attempt.assert_called_with(
            render_path="hover", outcome="empty_content",
        )


class TestTemplateServiceRenderStages(unittest.TestCase):
    def setUp(self):
        self.metrics = MagicMock()
        self.svc = TemplateService(metrics=self.metrics)

    def test_stage_empty_returns_empty_string_and_tracks_empty_content(self):
        result = self.svc.render_string("", {}, render_path="hover")

        self.assertEqual("", result)
        self.metrics.track_template_expression_render_attempt.assert_called_once_with(
            render_path="hover", outcome="empty_content",
        )
        self.metrics.track_template_expression_validation_failure.assert_not_called()

    def test_stage_invalid_returns_original_content_without_render_error(self):
        content = "{{not_allowed(db)}}"

        result = self.svc.render_string(content, {"db": "x"}, render_path="runtime")

        self.assertEqual(content, result)
        self.metrics.track_template_expression_render_attempt.assert_any_call(
            render_path="runtime", outcome="validation_error",
        )
        self.assertNotIn(
            call(render_path="runtime", outcome="render_error"),
            self.metrics.track_template_expression_render_attempt.call_args_list,
        )

    def test_stage_success_tracks_success_metric(self):
        result = self.svc.render_string("{{urlencode(db)}}", {"db": "a b"}, render_path="runtime")

        self.assertEqual("a%20b", result)
        self.metrics.track_template_expression_render_attempt.assert_called_with(
            render_path="runtime", outcome="success",
        )
        self.metrics.track_template_expression_validation_failure.assert_not_called()
        self.metrics.track_template_expression_render_duration.assert_called_once()
        duration_args = self.metrics.track_template_expression_render_duration.call_args[0]
        self.assertEqual("runtime", duration_args[0])
        self.assertGreaterEqual(duration_args[1], 0.0)

    def test_stage_render_error_returns_original_content_and_tracks_render_error(self):
        content = "{{urlencode(db)}}"

        with patch(
            "pypost.core.template_service.render_with_jinja",
            side_effect=RuntimeError("boom"),
        ):
            result = self.svc.render_string(content, {"db": "alice"}, render_path="hover")

        self.assertEqual(content, result)
        self.metrics.track_template_expression_render_attempt.assert_called_with(
            render_path="hover", outcome="render_error",
        )
        self.metrics.track_template_expression_validation_failure.assert_not_called()


class TestTemplateServiceHelperStages(unittest.TestCase):
    def setUp(self):
        self.metrics = MagicMock()
        self.svc = TemplateService(metrics=self.metrics)

    def test_tokenize_template_expressions_counts_all_tokens(self):
        from pypost.core.template_expression_tokenizer import (
            tokenize_template_expressions,
        )

        content = "{{name}}/{{urlencode(db)}}/{{ missing }}"

        result = len(tokenize_template_expressions(content))

        self.assertEqual(3, result)

    def test_fallback_helper_tracks_render_error_for_non_value_error(self):
        result = fallback_content_after_render_exception(
            self.metrics,
            RuntimeError("boom"),
            "{{name.upper(}}",
            "runtime",
            1,
        )

        self.assertEqual("{{name.upper(}}", result)
        self.metrics.track_template_expression_render_attempt.assert_called_once_with(
            render_path="runtime", outcome="render_error",
        )

    def test_fallback_helper_skips_render_error_for_value_error(self):
        result = fallback_content_after_render_exception(
            self.metrics,
            ValueError("bad validation"),
            "{{not_allowed(db)}}",
            "runtime",
            1,
        )

        self.assertEqual("{{not_allowed(db)}}", result)
        self.metrics.track_template_expression_render_attempt.assert_not_called()

    def test_render_with_jinja_records_duration_on_success(self):
        from jinja2 import Environment

        env = Environment()

        @lru_cache(maxsize=256)
        def compile_template(content: str):
            return env.from_string(content)

        result = render_with_jinja(
            compile_template,
            "{{ name }}",
            {"name": "alice"},
            self.metrics,
            "hover",
        )

        self.assertEqual("alice", result)
        self.metrics.track_template_expression_render_duration.assert_called_once()
        args = self.metrics.track_template_expression_render_duration.call_args[0]
        self.assertEqual("hover", args[0])
        self.assertGreaterEqual(args[1], 0.0)

    def test_render_with_jinja_records_duration_on_render_error(self):
        def compile_template(_content: str):
            mock_template = MagicMock()
            mock_template.render.side_effect = RuntimeError("boom")
            return mock_template

        with self.assertRaises(RuntimeError):
            render_with_jinja(
                compile_template,
                "{{ urlencode(db) }}",
                {"db": "alice"},
                self.metrics,
                "runtime",
            )

        self.metrics.track_template_expression_render_duration.assert_called_once()
        args = self.metrics.track_template_expression_render_duration.call_args[0]
        self.assertEqual("runtime", args[0])
        self.assertGreaterEqual(args[1], 0.0)


if __name__ == "__main__":
    unittest.main()
