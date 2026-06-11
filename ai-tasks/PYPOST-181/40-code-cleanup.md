# PYPOST-181: Code Cleanup (Step 4)

## Actions

- New integration module follows project conventions: UTF-8, LF, max 100 columns.
- Explicit `pytestmark = pytest.mark.timeout(120)` per integration tier in `do-testing.md`.
- Reused PYPOST-180 helpers (`load_mcp_test_collection`, `mcp_exposed_requests`,
  `EXPECTED_MCP_TOOL_NAMES`) and `collect_mcp_tool_overview` for tool-name assertions.
- Live server harness mirrors `tests/test_mcp_server_integration.py` without modifying it.

## Verification

```bash
.venv/bin/python -m pytest tests/test_mcp_test_collection_integration.py -v
```
