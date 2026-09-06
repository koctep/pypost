"""Secrets and hidden-variable policy for network MCP (PYPOST-554)."""

from __future__ import annotations

import logging
import re
from typing import Any, Iterable, Mapping, Set

from jinja2 import meta

from pypost.core.template_service import TemplateService
from pypost.models.models import McpToolParam, RequestData

logger = logging.getLogger(__name__)

_MCP_REQUEST_VAR_PATTERN = re.compile(r"mcp\.request\.([a-zA-Z0-9_]+)")


def _iter_request_template_fields(request: RequestData) -> list[str]:
    fields: list[str] = [request.url, request.body]
    fields.extend(request.headers.values())
    fields.extend(request.params.values())
    return [field for field in fields if field]


class McpSecretsPolicy:
    """Rules for agent-visible MCP tool contracts vs execution-time secrets."""

    @staticmethod
    def extract_mcp_request_variables(request: RequestData) -> Set[str]:
        """Placeholders matching ``mcp.request.VAR`` (bare or wrapped) become agent tool inputs."""
        found: set[str] = set()
        for content in _iter_request_template_fields(request):
            found.update(_MCP_REQUEST_VAR_PATTERN.findall(content))
        return found

    @staticmethod
    def extract_environment_variable_names(
        request: RequestData,
        template_service: TemplateService | None,
    ) -> Set[str]:
        """Top-level Jinja placeholders resolved from the active environment."""
        if template_service is None:
            return set()
        names: set[str] = set()
        for content in _iter_request_template_fields(request):
            try:
                ast = template_service.parse(content)
                for var in meta.find_undeclared_variables(ast):
                    if var != "mcp":
                        names.add(var)
            except Exception:
                continue
        return names

    @staticmethod
    def build_agent_input_schema(
        mcp_request_vars: Iterable[str],
        env_var_names: Iterable[str],
        hidden_keys: Iterable[str],
    ) -> dict:
        """Build ``list_tools`` inputSchema without env or hidden secrets."""
        mcp_vars = set(mcp_request_vars)
        env_names = set(env_var_names)
        hidden = set(hidden_keys)

        agent_props = {name: {"type": "string"} for name in sorted(mcp_vars)}
        agent_required = sorted(mcp_vars)

        forbidden = (env_names | hidden) - mcp_vars
        for key in forbidden:
            agent_props.pop(key, None)
            if key in agent_required:
                agent_required.remove(key)

        return {
            "type": "object",
            "properties": agent_props,
            "required": agent_required,
        }

    @staticmethod
    def filter_agent_param_specs(
        specs: dict[str, McpToolParam],
        request: RequestData,
        template_service: TemplateService | None,
        hidden_keys: Iterable[str],
    ) -> dict[str, McpToolParam]:
        """Drop env-only and hidden keys from agent-visible MCP param metadata."""
        mcp_vars = McpSecretsPolicy.extract_mcp_request_variables(request)
        env_names = McpSecretsPolicy.extract_environment_variable_names(
            request, template_service
        )
        forbidden = (set(env_names) | set(hidden_keys)) - mcp_vars
        return {name: spec for name, spec in specs.items() if name not in forbidden}

    @staticmethod
    def build_input_schema_for_request(
        request: RequestData,
        template_service: TemplateService | None,
        hidden_keys: Iterable[str],
    ) -> dict:
        mcp_vars = McpSecretsPolicy.extract_mcp_request_variables(request)
        env_names = McpSecretsPolicy.extract_environment_variable_names(
            request, template_service
        )
        return McpSecretsPolicy.build_agent_input_schema(
            mcp_vars, env_names, hidden_keys
        )

    @staticmethod
    def effective_overridable_keys(
        mcp_overridable_keys: Iterable[str], hidden_keys: Iterable[str]
    ) -> Set[str]:
        """Keys an agent may override right now: overridable minus Hidden.

        Computed fresh from the two raw sets on every call so Hidden always
        wins even if storage/import ever produced an inconsistent
        ``Environment`` where a key is present in both sets.
        """
        return set(mcp_overridable_keys) - set(hidden_keys)

    @staticmethod
    def apply_permitted_overrides(
        env_vars: Mapping[str, str],
        arguments: Mapping[str, Any],
        mcp_overridable_keys: Iterable[str],
        hidden_keys: Iterable[str],
    ) -> dict:
        """Return a copy of ``env_vars`` with only permitted overrides applied."""
        effective = McpSecretsPolicy.effective_overridable_keys(
            mcp_overridable_keys, hidden_keys
        )
        merged = dict(env_vars)
        for name, value in arguments.items():
            if name in env_vars and name in effective:
                merged[name] = value
                logger.info("mcp_env_override_applied key=%s", name)
        return merged

    @staticmethod
    def execution_environment_variables(
        env_vars: Mapping[str, str],
    ) -> dict[str, str]:
        """Return real env values for ``call_tool``, including hidden keys."""
        return dict(env_vars)

    @staticmethod
    def safe_execution_log_fields(
        env_var_count: int,
        hidden_key_count: int,
        mcp_arg_count: int,
    ) -> dict[str, int]:
        """Diagnostic counts only — no variable names or values."""
        return {
            "env_var_count": env_var_count,
            "hidden_key_count": hidden_key_count,
            "mcp_arg_count": mcp_arg_count,
        }
