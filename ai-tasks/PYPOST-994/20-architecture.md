# PYPOST-994: Architecture Design

## Test Architecture Separation

1. **`tests/test_mcp_server_impl.py`**:
   - Authoritative unit test suite for `MCPServerImpl`.
   - Owns `test_list_tools_excludes_agent_ui_action_names`: tests tool registration, `AGENT_UI_MCP_TOOL_NAMES` disjointness, and `ui_*` prefix exclusion.

2. **`tests/test_agent_ui_actions_mcp.py`**:
   - Dedicated test suite for the out-of-process stdio sidecar bridge (`pypost.agent.ui_actions_mcp`).
   - Owns sidecar tool name exports, distinct server naming, `pyproject.toml` console script entry, source import isolation (`mcp_server_impl.py` must not reference `ui_actions_mcp`), and e2e subprocess stdio protocol execution.
