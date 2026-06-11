# PYPOST-180: Technical Debt (Step 6)

## Resolved in this task

- PYPOST-25 follow-up "No automated tests that use this collection" — groundwork added via
  shared loaders and validation tests (closes PYPOST-180 scope).

## Remaining / follow-up

| ID | Priority | Item | Notes |
| --- | --- | --- | --- |
| TD-1 | Medium | Live MCP execution using collection tools | [PYPOST-181](https://pypost.atlassian.net/browse/PYPOST-181) |
| TD-2 | Low | No pytest fixture in `conftest.py` yet | Add when PYPOST-181 needs session-scoped collection |
| TD-3 | Low | SSE probe URLs still `/sse` | By design — HTTPClient SSE-probe heuristic (PYPOST-430/552) |

## Blocker review

**SAFE TO CLOSE** — acceptance criteria met; remaining items are deferred follow-ups.
