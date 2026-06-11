# PYPOST-181: Technical Debt (Step 6)

## Resolved in this task

- PYPOST-25 / PYPOST-180 follow-up: live MCP integration tests load the committed
  collection and execute `list_tools` / `call_tool` over Streamable HTTP.
- PYPOST-180 TD-1 (live MCP execution using collection tools) — closed in this scope.

## Remaining / follow-up

| ID | Priority | Item | Notes |
| --- | --- | --- | --- |
| TD-1 | Low | Duplicate live-server harness | Extract shared `tests/helpers/mcp_live_server.py` from integration modules |
| TD-2 | Low | No `conftest.py` fixture | Session-scoped collection server if more collection tests are added |
| TD-3 | Medium | Real outbound HTTP to SSE probes | Requires local stub or running app on 1080/9080; deferred |

## Blocker review

**SAFE TO CLOSE** — acceptance criteria met; remaining items are deferred follow-ups.
