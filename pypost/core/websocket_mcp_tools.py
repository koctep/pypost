"""Tool schema generation, registration, and dispatch for WebSocket MCP tools.

PYPOST-1137 / WS-9 — All WebSocket MCP tool logic lives here so that
``mcp_server_impl.py`` can remain within its 325 LOC cap.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Any, Callable, Iterable, List, Optional, Protocol, Set

from mcp.types import TextContent

from pypost.core.mcp_activity_log import McpActivityEntry, McpActivityLog
from pypost.core.mcp_tool_contract import (
    McpToolContractPreview,
    build_tool_input_schema,
    normalize_mcp_tool_name,
)
from pypost.core.metrics_protocol import MetricsTrackerProtocol
from pypost.core.template_service import TemplateService
from pypost.core.websocket_probe import (
    WebSocketProbeConfig,
    WebSocketProbeResult,
    calculate_effective_probe_limits,
    format_probe_transcript,
)
from pypost.core.websocket_transport_protocol import HandshakeTarget
from pypost.models.models import McpToolParam
from pypost.models.settings import AppSettings
from pypost.models.websocket import WebSocketConnection

logger = logging.getLogger(__name__)

_MCP_REQUEST_VAR_PATTERN = re.compile(r"mcp\.request\.([a-zA-Z0-9_]+)")


class WebSocketProbeRunnerProtocol(Protocol):
    """Framework-neutral lifecycle used by the MCP probe orchestration."""

    result: WebSocketProbeResult | None

    def start(self) -> None: ...

    def isFinished(self) -> bool: ...

    def terminate(self) -> None: ...

    def wait(self, timeout_ms: int) -> bool: ...


WebSocketProbeRunnerFactory = Callable[
    [WebSocketProbeConfig], WebSocketProbeRunnerProtocol
]


def extract_websocket_mcp_variables(conn: WebSocketConnection) -> Set[str]:
    """Extract ``mcp.request.*`` placeholder names from a connection's template fields.

    Scans URL, all header values, all query-param values, and the designated probe
    preset payload.  Returns only the variable-name portion after ``mcp.request.``.

    Args:
        conn: WebSocket connection profile to scan.

    Returns:
        Set of variable names (e.g. ``{"market", "channel"}``).
    """
    found: set[str] = set()
    fields: list[str] = [conn.url] + list(conn.headers.values()) + list(conn.params.values())
    if conn.mcp_probe_preset_id:
        for preset in conn.presets:
            if preset.id == conn.mcp_probe_preset_id:
                fields.append(preset.payload)
                break
    for field_text in fields:
        if field_text:
            found.update(_MCP_REQUEST_VAR_PATTERN.findall(field_text))
    return found


def build_websocket_mcp_tool_schema(
    conn: WebSocketConnection,
    template_service: TemplateService | None,
    hidden_keys: Iterable[str],
) -> dict[str, Any]:
    """Build the JSON Schema ``inputSchema`` dict for a WebSocket probe MCP tool.

    Only ``mcp.request.*`` variables are included; hidden keys are stripped.
    The optional ``stop_when`` string parameter is always appended.

    Args:
        conn: WebSocket connection profile.
        template_service: Template service (unused — reserved for future expansion).
        hidden_keys: Key names that must be excluded from the published schema.

    Returns:
        JSON Schema dict suitable for ``Tool.inputSchema``.
    """
    specs = resolve_websocket_mcp_param_specs(conn)

    # Strip hidden keys from agent-visible schema
    hidden = set(hidden_keys)
    filtered = {name: spec for name, spec in specs.items() if name not in hidden}

    # Always expose the optional early-stop parameter
    if "stop_when" not in filtered:
        filtered["stop_when"] = McpToolParam(
            type="string",
            description="Stop probe early when an incoming message body contains this substring",
            required=False,
        )
    return build_tool_input_schema(filtered)


def resolve_websocket_mcp_param_specs(
    conn: WebSocketConnection,
) -> dict[str, McpToolParam]:
    """Return all discovered and explicit MCP specs used by a WebSocket tool."""
    discovered = extract_websocket_mcp_variables(conn)
    specs: dict[str, McpToolParam] = {
        name: conn.mcp_params.get(name, McpToolParam()) for name in discovered
    }
    for name, spec in conn.mcp_params.items():
        specs.setdefault(name, spec)
    specs.setdefault(
        "stop_when",
        McpToolParam(
            type="string",
            description="Stop probe early when an incoming message body contains this substring",
            required=False,
        ),
    )
    return specs


def resolve_websocket_mcp_call_specs(
    conn: WebSocketConnection, hidden_keys: Iterable[str]
) -> tuple[dict[str, McpToolParam], dict[str, McpToolParam]]:
    """Return complete and agent-visible parameter specs for one WebSocket call."""
    complete = resolve_websocket_mcp_param_specs(conn)
    hidden = set(hidden_keys)
    visible = {name: spec for name, spec in complete.items() if name not in hidden}
    return complete, visible


def build_websocket_mcp_preview(
    conn: WebSocketConnection,
    hidden_keys: Iterable[str] | None = None,
    template_service: TemplateService | None = None,
) -> McpToolContractPreview | None:
    """Build an agent-visible contract preview for an exposed WebSocket connection.

    Returns ``None`` if ``conn.expose_as_mcp`` is ``False``.

    Args:
        conn: WebSocket connection profile.
        hidden_keys: Keys to exclude from the preview schema.
        template_service: Template service (unused — reserved for future expansion).

    Returns:
        ``McpToolContractPreview`` instance, or ``None`` for unexposed profiles.
    """
    if not conn.expose_as_mcp:
        return None
    hidden = set(hidden_keys or ())
    schema = build_websocket_mcp_tool_schema(conn, template_service, hidden)
    tool_name = f"ws_{normalize_mcp_tool_name(conn.name)}"
    description = conn.mcp_description or f"Sample real-time stream from {conn.name}"
    return McpToolContractPreview(
        tool_name=tool_name,
        description=description,
        input_schema=schema,
        exclusions=(),
    )


def execute_websocket_probe(
    conn: WebSocketConnection,
    arguments: dict[str, Any],
    *,
    env_vars: dict[str, str],
    hidden_keys: Set[str],
    settings: Optional[AppSettings] = None,
    template_service: Optional[TemplateService] = None,
    metrics: Optional[MetricsTrackerProtocol] = None,
    activity_log: Optional[McpActivityLog] = None,
    runner_factory: WebSocketProbeRunnerFactory,
    process_events: Callable[[], None],
) -> List[TextContent]:
    """Resolve template variables, run the bounded probe, and return a sanitized transcript.

    Execution flow:
    1. Compute effective message/duration limits (clamped to global ceilings).
    2. Resolve template variables in URL, headers, params, and preset payload.
    3. Instantiate and run ``WebSocketProbeRunner`` (blocking ``runner.wait()``).
    4. Format and sanitize the transcript via ``format_probe_transcript``.
    5. Emit observability (metrics histogram, activity log entry).

    Args:
        conn: WebSocket connection profile with MCP configuration.
        arguments: Tool call arguments from the MCP client.
        env_vars: Active environment variable snapshot for variable resolution.
        hidden_keys: Keys whose values are redacted in the returned transcript.
        settings: Application settings providing global ceiling values.
        template_service: Template renderer for variable substitution.
        metrics: Metrics tracker for probe duration histogram.
        activity_log: Activity log for recording the tool invocation.

    Returns:
        ``List[TextContent]`` containing the single sanitized probe transcript.

    Raises:
        RuntimeError: If the runner terminates without producing a result.
    """
    # 1. Compute effective bounds
    eff_msgs, eff_dur = calculate_effective_probe_limits(conn, settings)

    # 2. Resolve template variables
    merged_vars: dict[str, Any] = {**env_vars, "mcp": {"request": arguments or {}}}
    svc = template_service or TemplateService()
    resolved_url = svc.render_string(conn.url, merged_vars)
    resolved_headers = {k: svc.render_string(v, merged_vars) for k, v in conn.headers.items()}

    initial_payload: str | None = None
    if conn.mcp_probe_preset_id:
        for preset in conn.presets:
            if preset.id == conn.mcp_probe_preset_id:
                initial_payload = svc.render_string(preset.payload, merged_vars)
                break

    target = HandshakeTarget(
        url=resolved_url,
        headers=resolved_headers,
        subprotocols=tuple(conn.subprotocols),
    )
    stop_when = (arguments or {}).get("stop_when")

    tool_name = f"ws_{normalize_mcp_tool_name(conn.name)}"
    logger.info(
        "execute_websocket_probe_started tool=%s eff_msgs=%d eff_dur_ms=%d "
        "has_stop_when=%s has_preset=%s arg_count=%d",
        tool_name,
        eff_msgs,
        eff_dur,
        bool(stop_when),
        bool(conn.mcp_probe_preset_id),
        len(arguments or {}),
    )

    config = WebSocketProbeConfig(
        target=target,
        initial_payload=initial_payload,
        max_messages=eff_msgs,
        max_duration_ms=eff_dur,
        stop_when=stop_when,
    )

    # 3. Execute probe on a short-lived QThread
    runner = runner_factory(config)
    runner.start()

    # Pump the Qt event loop while we wait for the runner to finish.
    # runner.wait() without processEvents() would starve the echo-server/main-thread
    # Qt event loop, preventing socket callbacks from being delivered.
    wait_deadline_ms = eff_dur + 3000  # hard deadline + 3 s grace
    wait_started = time.monotonic()
    while not runner.isFinished():
        process_events()
        elapsed_ms = (time.monotonic() - wait_started) * 1000.0
        if elapsed_ms >= wait_deadline_ms:
            break
        time.sleep(0.01)  # 10 ms poll interval

    if not runner.isFinished():
        runner.terminate()
        runner.wait(1000)

    result = runner.result
    if result is None:
        logger.error("execute_websocket_probe_failed tool=%s reason=no_result", tool_name)
        raise RuntimeError("WebSocket probe runner terminated without producing a result")

    # 4. Format and sanitize transcript
    transcript = format_probe_transcript(result, env_vars=env_vars, hidden_keys=hidden_keys)

    # 5. Observability
    logger.info(
        "execute_websocket_probe_completed tool=%s outcome=%s duration_ms=%.1f "
        "messages_received=%d close_code=%s",
        tool_name,
        result.outcome.value,
        result.duration_ms,
        result.messages_received,
        result.close_code,
    )

    if metrics is not None:
        metrics.track_websocket_probe_duration(result.outcome.value, result.duration_ms / 1000.0)

    if activity_log is not None:
        activity_log.append(
            McpActivityEntry.new_call_tool(
                tool_name,
                outcome=result.outcome.value,
                mcp_arg_count=len(arguments or {}),
                detail=result.error_message,
                duration_ms=result.duration_ms,
            )
        )

    return [TextContent(type="text", text=transcript)]
