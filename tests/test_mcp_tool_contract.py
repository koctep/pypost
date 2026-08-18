"""Tests for MCP tool contract preview (PYPOST-555)."""

import json
import unittest

import pytest

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
