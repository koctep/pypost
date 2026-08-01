# PYPOST-952: Dev Docs (Step 8)

## Files updated

| File | Change |
| --- | --- |
| `doc/dev/agent_ui_actions_mcp.md` | New — sidecar overview, entry points, tools, client config |
| `doc/dev/ui_actions.md` | Packaging section: live PYPOST-952 entry + cross-link |
| `doc/dev/mcp_integration.md` | Point to sidecar doc instead of path-only wording |

## Discoverability

- Operators: `make help` includes `run-agent-ui-mcp`
- Maintainers: ui_actions packaging section links to dedicated doc
- Product MCP readers: mcp_integration UI-action paragraph links sidecar

## Test commands documented

```bash
make test PYTEST_ARGS='tests/test_agent_ui_actions_mcp.py -v'
make test-agent-e2e PYTEST_ARGS='tests/test_agent_ui_actions_mcp.py::test_stdio_sidecar_lists_ui_action_tools -v'
```
