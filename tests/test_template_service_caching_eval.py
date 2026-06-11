"""PYPOST-455: Properties required if template caching is added later.

Caching is not implemented. Evaluation concluded deferral — see
doc/dev/template_expression_functions.md (Caching evaluation).
"""

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


if __name__ == "__main__":
    unittest.main()
