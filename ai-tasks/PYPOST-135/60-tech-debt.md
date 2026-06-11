# PYPOST-135: Technical Debt Review

## Blocker Review: SAFE TO CLOSE

| Item | Verdict |
| --- | --- |
| MCP tools accept agent arguments | **Confirmed** — `mcp.request.*` + `McpToolParam` pipeline |
| Schema generation for tool inputs | **Confirmed** — `list_tools` inputSchema |
| Execution-time substitution | **Confirmed** — `_merge_execution_variables` + `RequestService` |
| Test coverage | **Confirmed** — MCP unit and integration tests pass |
| Developer documentation | **Confirmed** — `doc/dev/mcp_integration.md` |

## Resolved Concern (PYPOST-16 item)

Original note in `ai-tasks/PYPOST-16/40-tech-debt.md`:

> Tools exposed via MCP do not accept arguments.

Resolved by PYPOST-550 (execution merge), PYPOST-553 (metadata and schema), and PYPOST-554
(secrets policy). This ticket verifies and closes for traceability.

## Follow-up Tasks

| Item | Action |
| --- | --- |
| PYPOST-140 — Implement argument parsing for tools | **Duplicate** — superseded; recommend closing as duplicate of PYPOST-135 / PYPOST-553 |
| PYPOST-16 tech-debt bullet | Update parent debt doc when PYPOST-16 is next touched |

No new Jira issues required.

## Test Results

```
make test → 1002 passed, 39 subtests passed (2026-06-11)
```

MCP-focused modules exercised: `test_mcp_server_impl.py`, `test_mcp_tool_contract.py`,
`test_mcp_secrets_policy.py`, `test_mcp_server_integration.py`.
