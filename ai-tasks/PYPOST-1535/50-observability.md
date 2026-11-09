# PYPOST-1535: Observability

## Analysis

This debt fix restores object identity in `MCPServerImpl.register_tools` without
changing the tool-call execution path, metrics, or logging. Existing MCP
observability remains sufficient:

- `mcp_param_default_applied` INFO logs on default application
- `track_mcp_request_received` / `track_mcp_response_sent` /
  `track_mcp_tool_call_duration` on tool calls
- Registry/worker refresh logs for `UPDATE_TOOLS` (`mcp_worker_ipc_ack`, failure
  markers)

No new log lines or metrics were required: identity preservation is verified by
unit `assertIs` contracts, not by runtime telemetry.

## Changes

- N/A — no observability code changes.

## Validation

- Existing identity and call-tool tests exercise the registration path without
  needing new log assertions.
