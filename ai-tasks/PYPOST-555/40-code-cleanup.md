# PYPOST-555: Code Cleanup

## Lint and format

- No new linter issues in `mcp_tool_contract.py`, `request_editor.py`, or `tabs_presenter.py`.
- Shared schema helpers consolidated into `mcp_tool_contract.py` to avoid circular imports
  with `mcp_server_impl.py`.

## Refactoring

- Moved `tool_description`, `resolve_mcp_param_specs`, `build_tool_input_schema`, and
  `normalize_mcp_tool_name` from `mcp_server_impl.py` into `mcp_tool_contract.py`.
- Updated `mcp_tools_overview.py` and tests to import from the shared module.

## Scope check

- No unrelated files modified beyond MCP contract sharing and UI preview wiring.
