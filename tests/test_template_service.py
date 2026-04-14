import unittest
from unittest.mock import MagicMock

import jinja2.nodes

from pypost.core.template_service import TemplateService


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

    def test_validate_allows_nested_allowed_calls(self):
        result = self.svc.validate_function_expressions("{{md5(urlencode(db))}}")
        self.assertTrue(result.is_valid)

    def test_validate_reports_invalid_argument(self):
        result = self.svc.validate_function_expressions("{{urlencode('db')}}")
        self.assertFalse(result.is_valid)
        self.assertEqual("invalid_argument", result.code)

    def test_validate_reports_invalid_syntax(self):
        result = self.svc.validate_function_expressions("{{urlencode(db}}")
        self.assertFalse(result.is_valid)
        self.assertEqual("invalid_syntax", result.code)


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
        self.metrics.track_template_expression_validation_failure.assert_called_with(
            render_path="runtime", code="unknown_function", function_name="not_allowed",
        )

    def test_render_empty_content_tracks_metric(self):
        result = self.svc.render_string("", {}, render_path="hover")
        self.assertEqual("", result)
        self.metrics.track_template_expression_render_attempt.assert_called_with(
            render_path="hover", outcome="empty_content",
        )


if __name__ == "__main__":
    unittest.main()
