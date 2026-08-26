# PYPOST-1171: Code Cleanup

- Removed dead `_on_method_changed` MCP body placeholder branch.
- Removed `TestRequestServiceMCP` and unused `_mcp_run_headers` helper.
- Extracted `_insert_mcp_client_tab` shared by blank and legacy open paths.
- `make lint` clean on touched modules.
