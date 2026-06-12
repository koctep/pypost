"""PYPOST-455 / PYPOST-628: Template compile cache properties and guards.

Compiled templates are cached per TemplateService instance (LRU maxsize=256).
"""

import pytest

pytestmark = pytest.mark.timeout(30)

import unittest

from pypost.core.template_service import TemplateService


class TestTemplateRenderCachingPrerequisites(unittest.TestCase):
    """Guard properties any future render cache must preserve."""

    def setUp(self) -> None:
        self.svc = TemplateService()

    def test_identical_inputs_produce_identical_output(self) -> None:
        content = "{{urlencode(host)}}/items/{{id}}"
        variables = {"host": "example.com", "id": "7"}
        first = self.svc.render_string(content, variables)
        second = self.svc.render_string(content, variables)
        self.assertEqual(first, second)
        self.assertEqual(first, "example.com/items/7")

    def test_variable_change_produces_different_output(self) -> None:
        content = "{{host}}/api"
        self.assertNotEqual(
            self.svc.render_string(content, {"host": "a"}),
            self.svc.render_string(content, {"host": "b"}),
        )

    def test_invalid_template_falls_back_each_call(self) -> None:
        content = "{{unknown(var)}}"
        variables = {"var": "x"}
        for _ in range(3):
            self.assertEqual(
                self.svc.render_string(content, variables),
                content,
            )

    def test_empty_content_stays_empty(self) -> None:
        for _ in range(3):
            self.assertEqual(self.svc.render_string("", {"a": "1"}), "")

    def test_compile_cache_reuses_template_for_identical_content(self) -> None:
        content = "{{host}}/api"
        variables = {"host": "example.com"}
        self.svc.render_string(content, variables)
        info_after_first = self.svc._compile_template.cache_info()
        self.svc.render_string(content, variables)
        info_after_second = self.svc._compile_template.cache_info()
        self.assertEqual(info_after_first.misses, 1)
        self.assertEqual(info_after_second.hits, 1)
        self.assertEqual(info_after_second.misses, 1)


if __name__ == "__main__":
    unittest.main()
