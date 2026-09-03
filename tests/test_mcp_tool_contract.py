"""Tests for MCP tool contract preview (PYPOST-555)."""

import json
import unittest

import pytest

import pypost.core.mcp_tool_contract as mcp_tool_contract
from pypost.core.mcp_tool_contract import (
    build_mcp_tool_contract_preview,
    build_tool_input_schema,
    format_mcp_tool_contract_preview,
    normalize_mcp_tool_name,
)
from pypost.core.template_service import TemplateService
from pypost.models.models import McpToolParam, RequestData

pytestmark = pytest.mark.timeout(30)


class TestMcpToolContract(unittest.TestCase):
    def test_integer_or_string_schema_is_an_explicit_decimal_union(self):
        """PYPOST-1038 R1: publish both native and decimal-string identifiers."""
        schema = build_tool_input_schema(
            {
                "identifier": McpToolParam(
                    type="integer_or_string",
                    description="A Jira identifier.",
                    required=True,
                ),
                "legacy_count": McpToolParam(type="integer", required=False),
                "legacy_name": McpToolParam(type="string", required=False),
            }
        )

        self.assertEqual(
            schema["properties"]["identifier"],
            {
                "anyOf": [
                    {"type": "integer"},
                    {"type": "string", "pattern": "^[+-]?[0-9]+$"},
                ],
                "description": "A Jira identifier.",
            },
        )
        self.assertEqual(schema["properties"]["legacy_count"], {"type": "integer"})
        self.assertEqual(schema["properties"]["legacy_name"], {"type": "string"})
        self.assertEqual(schema["required"], ["identifier"])

    def test_schema_includes_default_and_omits_optional_from_required(self):
        """PYPOST-1054: schema includes default when set and omits optional params from required."""
        schema = build_tool_input_schema(
            {
                "maxResults": McpToolParam(
                    type="integer_or_string",
                    description="Maximum boards per page.",
                    required=False,
                    default=50,
                ),
                "startAt": McpToolParam(
                    type="integer_or_string",
                    description="Offset into list.",
                    required=False,
                    default=0,
                ),
                "identifier": McpToolParam(
                    type="integer_or_string",
                    description="A Jira identifier.",
                    required=True,
                ),
            }
        )

        self.assertEqual(schema["properties"]["maxResults"]["default"], 50)
        self.assertEqual(schema["properties"]["startAt"]["default"], 0)
        self.assertNotIn("default", schema["properties"]["identifier"])
        self.assertEqual(schema["required"], ["identifier"])
        self.assertNotIn("maxResults", schema.get("required", []))
        self.assertNotIn("startAt", schema.get("required", []))

    def test_normalize_mcp_tool_name(self):
        self.assertEqual(normalize_mcp_tool_name("Fetch User"), "fetch_user")

    def test_preview_none_when_not_exposed(self):
        req = RequestData(name="Hidden", expose_as_mcp=False, method="GET", url="http://x")
        self.assertIsNone(build_mcp_tool_contract_preview(req))

    def test_preview_matches_list_tools_metadata(self):
        req = RequestData(
            name="Echo Tool",
            mcp_description="Echo response",
            expose_as_mcp=True,
            method="GET",
            url="http://{{ mcp.request.host }}/p",
            mcp_params={
                "host": McpToolParam(
                    type="string",
                    description="Target host",
                    required=True,
                ),
                "limit": McpToolParam(
                    type="integer",
                    description="Max items",
                    required=False,
                ),
            },
        )
        preview = build_mcp_tool_contract_preview(req, template_service=TemplateService())
        self.assertIsNotNone(preview)
        self.assertEqual(preview.tool_name, "echo_tool")
        self.assertEqual(preview.description, "Echo response")
        self.assertEqual(preview.input_schema["properties"]["host"]["type"], "string")
        self.assertEqual(preview.input_schema["required"], ["host"])

    def test_preview_lists_hidden_and_env_only_exclusions(self):
        req = RequestData(
            name="Auth",
            expose_as_mcp=True,
            method="GET",
            url="{{ base_url }}/items",
            headers={"Authorization": "Bearer {{ api_key }}"},
            mcp_params={
                "api_key": McpToolParam(type="string", required=True),
                "page": McpToolParam(type="integer", required=False),
            },
        )
        preview = build_mcp_tool_contract_preview(
            req,
            hidden_keys={"api_key"},
            template_service=TemplateService(),
        )
        self.assertIsNotNone(preview)
        self.assertNotIn("api_key", preview.input_schema.get("properties", {}))
        self.assertNotIn("base_url", preview.input_schema.get("properties", {}))
        excluded = {item.name: item.reason for item in preview.exclusions}
        self.assertEqual(excluded.get("api_key"), "hidden")
        self.assertEqual(excluded.get("base_url"), "env-only")

    def test_format_includes_schema_json_and_policy(self):
        req = RequestData(
            name="Auth",
            expose_as_mcp=True,
            method="GET",
            url="{{ base_url }}/items",
            headers={"Authorization": "Bearer {{ api_key }}"},
        )
        preview = build_mcp_tool_contract_preview(
            req,
            hidden_keys={"api_key"},
            template_service=TemplateService(),
        )
        text = format_mcp_tool_contract_preview(preview)
        self.assertIn("Tool name: auth", text)
        self.assertIn("inputSchema:", text)
        self.assertIn(json.dumps(preview.input_schema, indent=2, sort_keys=True), text)
        self.assertIn("api_key (hidden env key)", text)
        self.assertIn("base_url (env-only)", text)

    def test_preview_generates_schema_for_wrapped_variables_without_mcp_params(self):
        req = RequestData(
            name="Get Board Sprints",
            mcp_description="Fetch sprints for a board",
            expose_as_mcp=True,
            method="GET",
            url="http://api.example/boards/{{ to_int(mcp.request.board_id) }}",
            body='{"name": "{{ upper(mcp.request.board_name) }}"}',
            mcp_params={},
        )
        preview = build_mcp_tool_contract_preview(
            req,
            template_service=TemplateService(),
        )
        self.assertIsNotNone(preview)
        self.assertIn("board_id", preview.input_schema["properties"])
        self.assertIn("board_name", preview.input_schema["properties"])
        self.assertIn("board_id", preview.input_schema["required"])
        self.assertIn("board_name", preview.input_schema["required"])

    def test_runtime_predicate_accepts_all_declared_types(self) -> None:
        predicate = getattr(mcp_tool_contract, "is_mcp_runtime_value_compatible", None)
        self.assertTrue(
            callable(predicate),
            "Step 4 must provide the strict MCP runtime compatibility predicate",
        )
        accepted_values = {
            "string": "plain text",
            "integer": 7,
            "integer_or_string": "+007",
            "number": 3.14,
            "boolean": False,
            "array": ["item"],
            "object": {"key": "value"},
        }

        for param_type, value in accepted_values.items():
            with self.subTest(param_type=param_type):
                self.assertTrue(predicate(param_type, value))

    def test_runtime_predicate_rejects_numeric_bools_and_coercion(self) -> None:
        predicate = getattr(mcp_tool_contract, "is_mcp_runtime_value_compatible", None)
        self.assertTrue(callable(predicate))

        for param_type in ("integer", "integer_or_string", "number"):
            with self.subTest(param_type=param_type):
                self.assertFalse(predicate(param_type, True))

        non_coercible_values = (
            ("integer", "7"),
            ("number", "3.14"),
            ("boolean", 1),
            ("array", ("item",)),
            ("object", [("key", "value")]),
        )
        for param_type, value in non_coercible_values:
            with self.subTest(param_type=param_type, value=value):
                self.assertFalse(predicate(param_type, value))

    def test_runtime_predicate_accepts_only_integer_or_string_decimal_forms(self) -> None:
        predicate = getattr(mcp_tool_contract, "is_mcp_runtime_value_compatible", None)
        self.assertTrue(callable(predicate))

        for value in (42, "-42", "+42"):
            with self.subTest(value=value):
                self.assertTrue(predicate("integer_or_string", value))

        for value in (42.0, "3.14", "1e3", "arbitrary text", " 42", "+ 42"):
            with self.subTest(value=value):
                self.assertFalse(predicate("integer_or_string", value))

    def test_runtime_validator_uses_safe_named_diagnostics_without_mutation(self) -> None:
        validator = getattr(mcp_tool_contract, "validate_mcp_argument_values", None)
        self.assertTrue(callable(validator))
        error_type = getattr(mcp_tool_contract, "McpArgumentValidationError", None)
        self.assertIsInstance(error_type, type)

        raw_value = "sensitive-raw-argument"
        arguments = {"account_id": raw_value}
        original_arguments = dict(arguments)
        specs = {"account_id": McpToolParam(type="integer", required=True)}

        with self.assertRaises(error_type) as raised:
            validator(arguments, specs)

        message = str(raised.exception)
        self.assertIn("account_id", message)
        self.assertIn("integer", message)
        self.assertNotIn(raw_value, message)
        self.assertEqual(arguments, original_arguments)

    def test_legacy_integer_or_string_default_compatibility_remains_unchanged(self) -> None:
        param = McpToolParam(type="integer_or_string", default="legacy-id")
        self.assertEqual(param.default, "legacy-id")


# ---------------------------------------------------------------------------
# PYPOST-1089 — Step 3: Failing repro tests for McpToolParam.default validation
# ---------------------------------------------------------------------------


def test_boolean_default_string_raises():
    """McpToolParam(type='boolean', default='fifty') must raise pydantic.ValidationError.

    Currently fails because model_post_init does not cross-check default type.
    """
    import pydantic

    with pytest.raises(pydantic.ValidationError):
        McpToolParam(type="boolean", default="fifty")


def test_integer_default_float_raises():
    """McpToolParam(type='integer', default=3.14) must raise pydantic.ValidationError.

    Currently fails because model_post_init does not cross-check default type.
    """
    import pydantic

    with pytest.raises(pydantic.ValidationError):
        McpToolParam(type="integer", default=3.14)


def test_valid_defaults_accepted():
    """Valid type-compatible defaults must NOT raise.

    These should already work today and will continue to work after the fix.
    """
    # integer with int default
    p1 = McpToolParam(type="integer", default=5)
    assert p1.default == 5

    # string with str default
    p2 = McpToolParam(type="string", default="hello")
    assert p2.default == "hello"

    # boolean with bool default
    p3 = McpToolParam(type="boolean", default=True)
    assert p3.default is True

    # number with float default
    p4 = McpToolParam(type="number", default=3.14)
    assert p4.default == 3.14

    # No default (None) is always valid
    p5 = McpToolParam(type="integer", default=None)
    assert p5.default is None
