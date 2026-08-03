# PYPOST-1029: Technical Debt Analysis

**Verdict:** Fixture + contract delivery matches architecture. Pagination
inputs are required (no template default filter). Empty-input allowlist is
current-user only. **SAFE TO CLOSE** for this story's DoD once Step 8 docs
land. No merge blockers.

Scope reviewed: `examples/collections/jira_mcp.json` (three list requests),
`tests/test_example_fixtures.py`, `tests/test_mcp_server_integration.py`
(pagination extras on path cases), `ai-tasks/PYPOST-1029/*`. Unrelated
working-tree noise ignored.

## Shortcuts Taken

- **Required maxResults/startAt instead of optional defaults** — PyPost
  templates have no allowed `| default(50)` / `| default(0)` path; omitting
  args would blank or fail `to_int`. Descriptions tell agents to use 50 / 0
  for the previous curated first page. Runtime defaulting for optional MCP
  query args is deferred (TD-1).
- **Offset pagination retained** — Classic Agile `startAt`/`maxResults` kept
  on the three curated routes. Some Agile *issue* list APIs are moving to
  `nextPageToken`; migrating the fixture is out of scope (TD-2).
- **Path-ID contract scoped to URL `to_int`** — PYPOST-1038 equality now
  ignores query-only `integer_or_string` pagination params. Intentional so
  path dual-form freeze stays meaningful.

## Code Quality Issues

- None material in application packages (no `pypost/` edits).
- Pagination `mcp_params` descriptions are slightly repetitive across the
  three requests; acceptable for fixture clarity.

## Missing Tests

| Scenario | Status |
| -------- | ------ |
| Three list tools declare/bind maxResults + startAt | Present |
| Empty mcp_params freeze = current-user only | Present |
| PYPOST-1028 env/auth/mcp_params/allowlist checkers | Present / still green |
| Integration path cases supply pagination args | Present |
| Optional omitted-arg default behavior | Missing by design (TD-1) |
| Token (`nextPageToken`) pagination | Missing (TD-2) |
| Live Jira paging e2e | Out of scope |

Timeout-marker review: **no blocker** — module/class timeouts already set.

## Performance Concerns

None. Offline contracts remain cheap; pagination only changes query template
bindings.

## Deviations from Architecture

None material. Delivered as designed: fixture parameterization with
`integer_or_string` + `to_int`, allowlist narrowed, docs in Step 8.

## Follow-up Tasks

### TD-1 — Low

- **Item:** Support safe defaults for optional MCP query args (e.g. curated
  `maxResults=50` / `startAt=0` when omitted) without blank query params or
  `to_int` failures — likely a template/defaulting feature, not fixture-only.
- **Notes:** Would restore “omit to get previous default” agent UX.
- **Jira:** [PYPOST-1054](https://pypost.atlassian.net/browse/PYPOST-1054)

### TD-2 — Low

- **Item:** Evaluate migrating curated Agile issue/sprint list pagination from
  `startAt` to `nextPageToken` where Atlassian deprecates offset pagination.
- **Notes:** Keep `maxResults`; document agent paging loop. Separate from this
  story's offset parameterization.
- **Jira:** [PYPOST-1055](https://pypost.atlassian.net/browse/PYPOST-1055)
