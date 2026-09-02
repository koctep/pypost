"""Edge-case coverage for strict template expressions (PYPOST-1250)."""

from __future__ import annotations

import unittest

import pytest

from pypost.core.template_service import TemplateService
from pypost.core.template_expression_types import IntegerConversionError


pytestmark = pytest.mark.timeout(30)


class TestStrictExpressionEdgeCases(unittest.TestCase):
    """Lock strict rendering behavior at expression syntax boundaries."""

    def setUp(self) -> None:
        self.service = TemplateService()

    def test_three_level_nested_expression_renders(self) -> None:
        content = "{{base64(md5(to_int(value)))}}"

        self.assertEqual(
            "YTFkMGM2ZTgzZjAyNzMyN2Q4NDYxMDYzZjRhYzU4YTY=",
            self.service.render_string(content, {"value": "42"}),
        )

    def test_three_level_nested_strict_failure_propagates(self) -> None:
        content = "{{base64(md5(to_int(value)))}}"

        with self.assertRaises(IntegerConversionError):
            self.service.render_string_strict_conversion(content, {"value": "not-an-int"})

    def test_multiline_strict_expression_fails_closed(self) -> None:
        content = "{{\n  to_int(\n    value\n  )\n}}"

        with self.assertRaises(IntegerConversionError):
            self.service.render_string_strict_conversion(content, {"value": "not-an-int"})

    def test_valid_strict_expression_inside_jinja_comment_is_not_evaluated(self) -> None:
        content = "before {# {{to_int(value)}} #} after"

        self.assertEqual(
            "before  after",
            self.service.render_string_strict_conversion(content, {"value": "not-an-int"}),
        )

    def test_commented_invalid_nested_expression_remains_fail_closed(self) -> None:
        content = "before {# {{to_int(value, extra)}} #} after"

        with self.assertRaises(IntegerConversionError):
            self.service.render_string_strict_conversion(
                content,
                {"value": "42", "extra": "ignored"},
            )
