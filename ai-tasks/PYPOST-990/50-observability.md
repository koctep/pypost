# PYPOST-990 Observability

The optional HTTP entry emits lifecycle events through the existing stderr
logger:

| Event | Level | Meaning |
| --- | --- | --- |
| `agent_ui_mcp_http_starting` | INFO | Requested host and port |
| `agent_ui_mcp_http_listening` | INFO | Resolved `/mcp` endpoint is ready |
| `agent_ui_mcp_http_failed` | ERROR | Uvicorn startup/runtime failure |
| `agent_ui_mcp_http_stop_timeout` | ERROR | Listener exceeded bounded join |
| `agent_ui_mcp_http_stopped` | INFO | Listener thread ended |

The listening event is the operator discovery point when `--port 0` selects an
ephemeral port. Logs contain endpoint and lifecycle metadata only. Tool names,
widget ids, fill text, and raw HTTP arguments are not added to the new events.
Qt dispatch timeout and UI-action failures retain the existing MCP safe-error
response and are visible through the existing sidecar logger.

No Prometheus metric was added: this is a local optional sidecar lifecycle,
and the agent-UI surface is intentionally separate from product MCP metrics.
