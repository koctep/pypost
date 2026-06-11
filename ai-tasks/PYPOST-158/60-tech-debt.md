# PYPOST-158: Technical Debt Analysis

## Resolved

- **SSE close + 405 on `/messages`** (PYPOST-21): Automated coverage in
  `tests/test_mcp_legacy_sse.py` — SSE closure contract via mocked transport; 405 guards on inner
  and mounted legacy paths.

## Remaining (non-blockers)

- **Live SSE stream disconnect in TestClient** — deferred; would need async timeout harness or
  uvicorn thread (see PYPOST-367). Mocked transport covers `handle_sse_get` Response contract.
- **Mount + direct ASGI for SSE stream** — [PYPOST-159](https://pypost.atlassian.net/browse/PYPOST-159):
  unchanged by this task.

## Blocker review

**SAFE TO CLOSE** — acceptance criteria met; no new blockers.

## Follow-up Tasks

None new.
