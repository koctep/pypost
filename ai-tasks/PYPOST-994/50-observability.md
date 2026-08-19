# PYPOST-994: Observability

## Test Execution Signals

- Test separation verified by pytest discovery and execution.
- `tests/test_mcp_server_impl.py` reliably reports catalog exclusion failures if any `AGENT_UI_MCP_TOOL_NAMES` or `ui_*` tools are accidentally registered.
