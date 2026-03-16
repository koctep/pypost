import unittest
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


if __name__ == "__main__":
    unittest.main()
