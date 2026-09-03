# PYPOST-992 Code Cleanup

- Reused the existing stdio subprocess setup and MCP client imports in
  `tests/test_agent_ui_actions_mcp.py`.
- Kept the test deterministic by targeting the stable URL input for both
  actions rather than a menu-opening control.
- Added bounded `anyio.fail_after` scopes around each `call_tool` request to
  prevent a protocol regression from hanging the test indefinitely.
- Preserved the existing list-tools test and all product/attach separation
  assertions.
- `make lint`, focused Make tests, and AI-task verification pass.
