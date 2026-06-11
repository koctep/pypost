"""Agent-visible MCP tool contract helpers and preview (PYPOST-553/555)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable

from pypost.core.mcp_secrets_policy import McpSecretsPolicy
from pypost.core.template_service import TemplateService
from pypost.models.models import McpToolParam, RequestData


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


def build_tool_input_schema(specs: dict[str, McpToolParam]) -> dict:
    """Build JSON Schema for MCP tool arguments from parameter metadata."""
    properties: dict[str, dict[str, Any]] = {}
    required: list[str] = []
    for name in sorted(specs):
        spec = specs[name]
        prop: dict[str, Any] = {"type": spec.type}
        if spec.description:
            prop["description"] = spec.description
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
