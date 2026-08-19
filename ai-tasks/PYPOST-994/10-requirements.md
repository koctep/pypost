# PYPOST-994: Deduplicate MCP catalog exclusion asserts

## Programming Language

Python is the implementation language for test suites and application code. English Markdown is used for workflow documentation.

## Goals

Follow-up from PYPOST-953. In `tests/test_agent_ui_actions_mcp.py` and `tests/test_mcp_server_impl.py`, both modules contained overlapping assertions verifying that `MCPServerImpl` does not expose `AGENT_UI_MCP_TOOL_NAMES`.

**Business goal:** Consolidate to a single authoritative catalog exclusion test in `tests/test_mcp_server_impl.py`, removing duplicate assertions from `tests/test_agent_ui_actions_mcp.py` and decoupling test responsibilities.

## Definition of Done

- [ ] `tests/test_mcp_server_impl.py` remains the single authoritative lock for MCP catalog exclusion (`test_list_tools_excludes_agent_ui_action_names`).
- [ ] Duplicate test function and unused `MCPServerImpl` import are removed from `tests/test_agent_ui_actions_mcp.py`.
- [ ] All tests pass cleanly.
