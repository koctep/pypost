"""Tests for McpSecretsPolicy (PYPOST-554)."""

import unittest

import pytest

from pypost.core.mcp_secrets_policy import McpSecretsPolicy
from pypost.core.template_service import TemplateService
from pypost.models.models import McpToolParam, RequestData

pytestmark = pytest.mark.timeout(30)


class TestMcpSecretsPolicy(unittest.TestCase):
    def test_build_agent_input_schema_excludes_env_and_hidden_keys(self):
        schema = McpSecretsPolicy.build_agent_input_schema(
            mcp_request_vars={"user_id"},
            env_var_names={"api_key", "base_url"},
            hidden_keys={"api_key"},
        )
        self.assertEqual(set(schema["properties"]), {"user_id"})
        self.assertEqual(schema["required"], ["user_id"])

    def test_filter_agent_param_specs_removes_hidden_env_only_params(self):
        req = RequestData(
            method="GET",
            url="{{ base_url }}/items",
            headers={"Authorization": "Bearer {{ api_key }}"},
            mcp_params={
                "api_key": McpToolParam(type="string", required=True),
                "user_id": McpToolParam(type="string", required=True),
            },
        )
        specs = {
            "api_key": McpToolParam(type="string", required=True),
            "user_id": McpToolParam(type="string", required=True),
        }
        filtered = McpSecretsPolicy.filter_agent_param_specs(
            specs,
            req,
            TemplateService(),
            hidden_keys={"api_key"},
        )
        self.assertNotIn("api_key", filtered)
        self.assertIn("user_id", filtered)

    def test_filter_agent_param_specs_keeps_mcp_request_vars(self):
        req = RequestData(
            method="GET",
            url="http://{{ mcp.request.host }}/p",
            mcp_params={"host": McpToolParam(type="string", required=True)},
        )
        specs = {"host": McpToolParam(type="string", required=True)}
        filtered = McpSecretsPolicy.filter_agent_param_specs(
            specs,
            req,
            TemplateService(),
            hidden_keys=set(),
        )
        self.assertEqual(filtered, specs)

    def test_execution_environment_variables_returns_real_values(self):
        env = {"api_key": "secret-token", "base_url": "http://api"}
        self.assertEqual(
            McpSecretsPolicy.execution_environment_variables(env),
            env,
        )

    def test_safe_execution_log_fields_contains_counts_only(self):
        fields = McpSecretsPolicy.safe_execution_log_fields(3, 1, 2)
        self.assertEqual(
            fields,
            {
                "env_var_count": 3,
                "hidden_key_count": 1,
                "mcp_arg_count": 2,
            },
        )

    def test_extract_mcp_request_variables_from_request_fields(self):
        req = RequestData(
            method="GET",
            url="http://{{ mcp.request.host }}/p",
            body='{"q": "{{ mcp.request.query }}"}',
        )
        self.assertEqual(
            McpSecretsPolicy.extract_mcp_request_variables(req),
            {"host", "query"},
        )

    def test_extract_mcp_request_variables_discovers_function_wrapped_placeholders(self):
        req = RequestData(
            method="POST",
            url=(
                "http://api.example/boards/{{ to_int(mcp.request.board_id) }}"
                "/sprints/{{ to_int(mcp.request.sprint_id) }}"
            ),
            headers={
                "Authorization": "Basic {{ base64(mcp.request.auth_token) }}",
                "X-Custom": "{{ upper(mcp.request.custom_header) }}",
            },
            params={
                "query": "{{ urlencode(mcp.request.search_term) }}",
                "filter": "{{ mcp.request.filter_type }}",
            },
            body=(
                '{"id": {{ to_int(mcp.request.item_id) }}, '
                '"data": "{{ base64(mcp.request.raw_data) }}"}'
            ),
        )
        self.assertEqual(
            McpSecretsPolicy.extract_mcp_request_variables(req),
            {
                "board_id",
                "sprint_id",
                "auth_token",
                "custom_header",
                "search_term",
                "filter_type",
                "item_id",
                "raw_data",
            },
        )

    def test_extract_mcp_request_variables_discovers_nested_and_concatenated_expressions(self):
        req = RequestData(
            method="GET",
            url=(
                "http://example.com/{{ base64(urlencode(mcp.request.nested_var)) }}"
                "/{{ mcp.request.prefix ~ mcp.request.suffix }}"
            ),
        )
        self.assertEqual(
            McpSecretsPolicy.extract_mcp_request_variables(req),
            {"nested_var", "prefix", "suffix"},
        )

    def test_extract_environment_variable_names_excludes_mcp_namespace(self):
        req = RequestData(
            method="GET",
            url="{{ base_url }}/{{ mcp.request.id }}",
        )
        names = McpSecretsPolicy.extract_environment_variable_names(
            req, TemplateService()
        )
        self.assertEqual(names, {"base_url"})


if __name__ == "__main__":
    unittest.main()
