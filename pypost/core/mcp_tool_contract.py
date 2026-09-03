"""Agent-visible MCP tool contract helpers and preview (PYPOST-553/555)."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Iterable

from pypost.core.mcp_secrets_policy import McpSecretsPolicy
from pypost.core.template_service import TemplateService
from pypost.models.models import _MCP_PARAM_TYPES, McpToolParam, RequestData


_INTEGER_OR_STRING_PATTERN = re.compile(r"^[+-]?[0-9]+$")


class McpArgumentValidationError(ValueError):
    """Safe validation error for an MCP argument without exposing its value."""

    def __init__(self, parameter_name: str, expected_type: str, kind: str) -> None:
        self.parameter_name = parameter_name
        self.expected_type = expected_type
        self.kind = kind
        if kind == "missing":
            message = (
                f"Missing required MCP argument '{parameter_name}' "
                f"(expected {expected_type})"
            )
        else:
            message = (
                f"Invalid MCP argument '{parameter_name}': "
                f"expected {expected_type}"
            )
        super().__init__(message)


def is_mcp_runtime_value_compatible(param_type: str, value: Any) -> bool:
    """Return whether a caller value matches an MCP type without coercion."""
    if param_type not in _MCP_PARAM_TYPES or isinstance(value, bool):
        return param_type == "boolean" and isinstance(value, bool)
    if param_type == "string":
        return isinstance(value, str)
    if param_type == "integer":
        return isinstance(value, int)
    if param_type == "integer_or_string":
        return isinstance(value, int) or (
            isinstance(value, str) and _INTEGER_OR_STRING_PATTERN.fullmatch(value) is not None
        )
    if param_type == "number":
        return isinstance(value, (int, float))
    if param_type == "array":
        return isinstance(value, list)
    if param_type == "object":
        return isinstance(value, dict)
    return False


def validate_mcp_required_arguments(
    arguments: Mapping[str, Any], required_specs: Mapping[str, McpToolParam]
) -> None:
    """Reject omitted names from the published required MCP parameter set."""
    for name, spec in required_specs.items():
        if spec.required and name not in arguments:
            raise McpArgumentValidationError(name, spec.type, "missing")


def validate_mcp_argument_values(
    arguments: Mapping[str, Any], specs: Mapping[str, McpToolParam]
) -> None:
    """Reject declared caller values whose runtime types do not match exactly."""
    for name, value in arguments.items():
        spec = specs.get(name)
        if spec is None or value is None:
            continue
        if not is_mcp_runtime_value_compatible(spec.type, value):
            raise McpArgumentValidationError(name, spec.type, "invalid")


def normalize_mcp_tool_name(name: str) -> str:
    """Normalize request display name to MCP tool name."""
    return "".join(c if c.isalnum() else "_" for c in name.lower())


def tool_description(req: RequestData) -> str:
    """Return agent-visible tool description, falling back to request name."""
    text = (req.mcp_description or "").strip()
    if text:
        return text
    return req.name or "No description"


def resolve_mcp_param_specs(
    req: RequestData, discovered: set[str]
) -> dict[str, McpToolParam]:
    """Merge template-discovered params with explicit ``mcp_params`` metadata."""
    specs: dict[str, McpToolParam] = {}
    for name in discovered:
        specs[name] = req.mcp_params.get(name, McpToolParam())
    for name, spec in req.mcp_params.items():
        if name not in specs:
            specs[name] = spec
    return specs


def resolve_mcp_call_param_specs(
    req: RequestData,
    template_service: TemplateService | None,
    hidden_keys: Iterable[str],
) -> tuple[dict[str, McpToolParam], dict[str, McpToolParam]]:
    """Return complete and agent-visible parameter specs for one HTTP tool call."""
    discovered = McpSecretsPolicy.extract_mcp_request_variables(req)
    complete = resolve_mcp_param_specs(req, discovered)
    visible = McpSecretsPolicy.filter_agent_param_specs(
        complete, req, template_service, hidden_keys
    )
    return complete, visible


def validate_mcp_execution_arguments(
    req: RequestData, arguments: Mapping[str, Any]
) -> None:
    """Validate effective HTTP arguments after omitted/null defaults are applied."""
    discovered = McpSecretsPolicy.extract_mcp_request_variables(req)
    validate_mcp_argument_values(arguments, resolve_mcp_param_specs(req, discovered))


def build_tool_input_schema(specs: dict[str, McpToolParam]) -> dict:
    """Build JSON Schema for MCP tool arguments from parameter metadata."""
    properties: dict[str, dict[str, Any]] = {}
    required: list[str] = []
    for name in sorted(specs):
        spec = specs[name]
        if spec.type == "integer_or_string":
            prop: dict[str, Any] = {
                "anyOf": [
                    {"type": "integer"},
                    {"type": "string", "pattern": "^[+-]?[0-9]+$"},
                ]
            }
        else:
            prop = {"type": spec.type}
        if spec.description:
            prop["description"] = spec.description
        if spec.default is not None:
            prop["default"] = spec.default
        properties[name] = prop
        if spec.required:
            required.append(name)
    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


@dataclass(frozen=True)
class McpPolicyExclusion:
    """Variable excluded from agent-visible tool contract."""

    name: str
    reason: str  # "hidden" | "env-only"


@dataclass(frozen=True)
class McpToolContractPreview:
    """What ``list_tools`` exposes to MCP clients for one request."""

    tool_name: str
    description: str
    input_schema: dict[str, Any]
    exclusions: tuple[McpPolicyExclusion, ...] = ()


def _exclusion_reason(
    name: str,
    mcp_vars: set[str],
    env_names: set[str],
    hidden_keys: set[str],
) -> str:
    if name in hidden_keys and name not in mcp_vars:
        return "hidden"
    if name in env_names and name not in mcp_vars:
        return "env-only"
    return "hidden"


def collect_policy_exclusions(
    request: RequestData,
    template_service: TemplateService | None,
    hidden_keys: Iterable[str],
) -> tuple[McpPolicyExclusion, ...]:
    """Names withheld from agent contract per PYPOST-554 policy."""
    hidden = set(hidden_keys)
    mcp_vars = McpSecretsPolicy.extract_mcp_request_variables(request)
    env_names = McpSecretsPolicy.extract_environment_variable_names(
        request, template_service
    )
    forbidden = sorted((env_names | hidden) - mcp_vars)
    return tuple(
        McpPolicyExclusion(
            name=name,
            reason=_exclusion_reason(name, mcp_vars, env_names, hidden),
        )
        for name in forbidden
    )


def build_mcp_tool_contract_preview(
    request: RequestData,
    hidden_keys: Iterable[str] | None = None,
    template_service: TemplateService | None = None,
) -> McpToolContractPreview | None:
    """Build agent-visible contract matching ``MCPServerImpl.list_tools`` output."""
    if not request.expose_as_mcp:
        return None

    hidden = set(hidden_keys or ())
    discovered = McpSecretsPolicy.extract_mcp_request_variables(request)
    specs = resolve_mcp_param_specs(request, discovered)
    filtered = McpSecretsPolicy.filter_agent_param_specs(
        specs, request, template_service, hidden
    )
    exclusions = collect_policy_exclusions(request, template_service, hidden)
    return McpToolContractPreview(
        tool_name=normalize_mcp_tool_name(request.name),
        description=tool_description(request),
        input_schema=build_tool_input_schema(filtered),
        exclusions=exclusions,
    )


def format_mcp_tool_contract_preview(preview: McpToolContractPreview) -> str:
    """Human-readable preview text for the request editor MCP tab."""
    lines = [
        f"Tool name: {preview.tool_name}",
        "",
        "Description:",
        preview.description,
        "",
        "inputSchema:",
        json.dumps(preview.input_schema, indent=2, sort_keys=True),
    ]
    if preview.exclusions:
        lines.extend(["", "Hidden variable policy (excluded from agent contract):"])
        for item in preview.exclusions:
            label = "hidden env key" if item.reason == "hidden" else "env-only"
            lines.append(f"  - {item.name} ({label})")
        lines.append("")
        lines.append(
            "Excluded variables still resolve at execution from the active environment."
        )
    else:
        lines.extend(
            [
                "",
                "Hidden variable policy: no exclusions for current request and environment.",
            ]
        )
    return "\n".join(lines)
