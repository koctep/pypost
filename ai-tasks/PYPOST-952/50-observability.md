# PYPOST-952: Observability Implementation

## Logging Implementation

### Added Logs

- **INFO** `pypost.agent.ui_actions_mcp` — `agent_ui_mcp_session_ready` after
  AgentAppSession start; `agent_ui_mcp_stdio_listening` when stdio transport
  begins.
- **INFO** — `agent_ui_mcp_tool_failed` on `UiActionError` (tool name + exception
  type only).
- **DEBUG** — `agent_ui_mcp_call_tool` with `tool`, `widget_id`, `in_current_tab`
  (fill text never logged — aligns with `ui_action_applied` policy).

### Log Structure

- Structured key=value fields in message text
- Log levels: INFO for lifecycle/failures, DEBUG for per-tool dispatch
- Sidecar logs to **stderr** so stdin/stdout remain MCP transport

## Metrics Implementation

N/A — agent-UI MCP sidecar does not integrate with Prometheus product metrics.
Session metrics port from AgentAppSession unchanged.

## Monitoring Integration

- [ ] Prometheus metrics — N/A for stdio sidecar v1
- [x] CI / test gate — `tests/test_agent_ui_actions_mcp.py`

## Validation Results

- [x] Logs do not include fill text
- [x] stderr used for logging in `main()`
- [x] Existing `ui_action_applied` DEBUG from ui_actions unchanged

## Notes

- Product MCP activity log and metrics paths untouched by design.
