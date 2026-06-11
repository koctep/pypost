# PYPOST-140: Technical Debt Review

## Blocker Review: SAFE TO CLOSE

| Item | Verdict |
| --- | --- |
| MCP tools accept agent arguments | **Confirmed** — `mcp.request.*` + `McpToolParam` pipeline |
| Schema generation for tool inputs | **Confirmed** — `list_tools` inputSchema |
| Execution-time substitution | **Confirmed** — `_merge_execution_variables` + `RequestService` |
| Test coverage | **Confirmed** — MCP unit tests pass (49/49 non-network tests) |
| Developer documentation | **Confirmed** — `doc/dev/mcp_integration.md` |

## Resolved Concern (PYPOST-16 item)

Original note in `ai-tasks/PYPOST-16/40-tech-debt.md`:

> Implement argument parsing for tools.

Resolved by PYPOST-550 (execution merge), PYPOST-553 (metadata and schema), and PYPOST-554
(secrets policy). This ticket closes the original debt item with traceability.

## Follow-up Tasks

No new Jira issues required.

| Item | Action |
| --- | --- |
| PYPOST-16 tech-debt bullet | Marked resolved in `ai-tasks/PYPOST-16/40-tech-debt.md` |

## Test Results

```
MCP unit tests (2026-06-12):
  test_mcp_server_impl.py       — 37 passed
  test_mcp_tool_contract.py     — 5 passed
  test_mcp_secrets_policy.py    — 7 passed
  (integration tests require network bind; skipped in sandbox)
```

Key argument-parsing tests:

- `test_call_tool_invokes_request_service_with_mcp_context`
- `test_call_tool_passes_merged_env_and_mcp_context`
- `test_merge_execution_variables_combines_env_and_mcp_args`
- `test_list_tools_builds_input_schema_from_mcp_request_placeholders`
