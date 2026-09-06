"""Tests for McpSecretsPolicy (PYPOST-554)."""

import logging
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

    # -----------------------------------------------------------------
    # PYPOST-1283 review fix: direct coverage for the SSRF-prevention
    # override policy (previously exercised only indirectly via
    # tests/test_mcp_environment_override_policy.py).
    # -----------------------------------------------------------------

    def test_effective_overridable_keys_key_in_both_sets_is_not_overridable(self):
        """Hidden always wins: a key in both sets must be excluded."""
        effective = McpSecretsPolicy.effective_overridable_keys(
            mcp_overridable_keys={"jira_project_key", "api_key"},
            hidden_keys={"api_key"},
        )
        self.assertEqual(effective, {"jira_project_key"})
        self.assertNotIn("api_key", effective)

    def test_effective_overridable_keys_key_in_neither_set_is_absent(self):
        effective = McpSecretsPolicy.effective_overridable_keys(
            mcp_overridable_keys={"jira_project_key"},
            hidden_keys={"api_key"},
        )
        self.assertNotIn("base_url", effective)
        self.assertEqual(effective, {"jira_project_key"})

    def test_effective_overridable_keys_overridable_only_key_is_included(self):
        effective = McpSecretsPolicy.effective_overridable_keys(
            mcp_overridable_keys={"jira_project_key"},
            hidden_keys=set(),
        )
        self.assertEqual(effective, {"jira_project_key"})

    def test_effective_overridable_keys_computed_fresh_not_from_stored_flags(self):
        """Even if storage produced an inconsistent Environment (key marked
        both overridable and hidden), the function recomputes from the raw
        sets every call rather than trusting any cached/stored result."""
        first = McpSecretsPolicy.effective_overridable_keys(
            mcp_overridable_keys={"dual_flagged"}, hidden_keys={"dual_flagged"}
        )
        second = McpSecretsPolicy.effective_overridable_keys(
            mcp_overridable_keys={"dual_flagged"}, hidden_keys=set()
        )
        self.assertEqual(first, set())
        self.assertEqual(second, {"dual_flagged"})

    def test_apply_permitted_overrides_applies_only_effective_keys(self):
        env_vars = {
            "jira_project_key": "DEFAULT",
            "api_key": "secret-value",
            "base_url": "https://example.test",
        }
        arguments = {
            "jira_project_key": "AGENT_SUPPLIED",
            "api_key": "attacker-supplied",
            "base_url": "https://attacker.example",
        }
        merged = McpSecretsPolicy.apply_permitted_overrides(
            env_vars,
            arguments,
            mcp_overridable_keys={"jira_project_key", "api_key"},
            hidden_keys={"api_key"},
        )
        # Overridable-only key: agent value wins.
        self.assertEqual(merged["jira_project_key"], "AGENT_SUPPLIED")
        # In both sets (hidden wins): original value preserved, not overridden.
        self.assertEqual(merged["api_key"], "secret-value")
        # In neither set: original value preserved, not overridden.
        self.assertEqual(merged["base_url"], "https://example.test")

    def test_apply_permitted_overrides_ignores_arguments_not_in_env_vars(self):
        """An argument name that isn't a known env var must not be injected."""
        merged = McpSecretsPolicy.apply_permitted_overrides(
            env_vars={"jira_project_key": "DEFAULT"},
            arguments={"jira_project_key": "AGENT", "unrelated_key": "ignored"},
            mcp_overridable_keys={"jira_project_key", "unrelated_key"},
            hidden_keys=set(),
        )
        self.assertEqual(
            merged, {"jira_project_key": "AGENT"}
        )
        self.assertNotIn("unrelated_key", merged)

    def test_apply_permitted_overrides_returns_copy_not_mutating_input(self):
        env_vars = {"jira_project_key": "DEFAULT"}
        McpSecretsPolicy.apply_permitted_overrides(
            env_vars,
            {"jira_project_key": "AGENT"},
            mcp_overridable_keys={"jira_project_key"},
            hidden_keys=set(),
        )
        self.assertEqual(env_vars, {"jira_project_key": "DEFAULT"})

    def test_apply_permitted_overrides_logs_info_with_key_not_value(self):
        """PYPOST-1283: applying an override must log at INFO with only the
        key name, and the overriding value must never appear in the record."""
        logger_name = "pypost.core.mcp_secrets_policy"
        with self.assertLogs(logger_name, level=logging.INFO) as captured:
            merged = McpSecretsPolicy.apply_permitted_overrides(
                env_vars={"jira_project_key": "DEFAULT"},
                arguments={"jira_project_key": "AGENT_SUPPLIED_SECRET_LOOKING_VALUE"},
                mcp_overridable_keys={"jira_project_key"},
                hidden_keys=set(),
            )
        self.assertEqual(merged["jira_project_key"], "AGENT_SUPPLIED_SECRET_LOOKING_VALUE")
        applied_lines = [
            line for line in captured.output if "mcp_env_override_applied" in line
        ]
        self.assertEqual(len(applied_lines), 1)
        self.assertTrue(applied_lines[0].startswith("INFO:"))
        self.assertIn("key=jira_project_key", applied_lines[0])
        self.assertNotIn("AGENT_SUPPLIED_SECRET_LOOKING_VALUE", applied_lines[0])

    def test_apply_permitted_overrides_does_not_log_for_rejected_keys(self):
        """A key excluded by the effective-overridable policy must not emit
        the applied-override log at all (no key, no value)."""
        logger_name = "pypost.core.mcp_secrets_policy"
        with self.assertLogs(logger_name, level=logging.DEBUG) as captured:
            # assertLogs requires at least one record; log a sentinel so the
            # absence of mcp_env_override_applied is meaningfully asserted.
            logging.getLogger(logger_name).debug("sentinel")
            McpSecretsPolicy.apply_permitted_overrides(
                env_vars={"api_key": "secret-value"},
                arguments={"api_key": "attacker-supplied"},
                mcp_overridable_keys={"api_key"},
                hidden_keys={"api_key"},
            )
        self.assertFalse(
            any("mcp_env_override_applied" in line for line in captured.output)
        )


if __name__ == "__main__":
    unittest.main()
