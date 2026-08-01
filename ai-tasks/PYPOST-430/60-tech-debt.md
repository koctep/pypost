# PYPOST-430: Technical Debt (Step 6)

## Resolved in this task

- `HTTPClient` no longer uses `"/sse" in url` for SSE classification (PYPOST-403 review item,
  PYPOST-551 TD-2).

## Remaining / follow-up

| ID | Priority | Item | Notes |
| --- | --- | --- | --- |
| TD-1 | Low | Dual SSE + Streamable HTTP maintenance | Legacy `/sse` mounts (PYPOST-551 TD-1). [PYPOST-653](https://pypost.atlassian.net/browse/PYPOST-653) |
| TD-2 | Low | Broad HTTPClient content-type handling | [PYPOST-203](https://pypost.atlassian.net/browse/PYPOST-203) |
| TD-3 | Low | SSE probe without explicit Accept uses default timeout until headers | Acceptable; probe timeouts apply when user sets Accept. [PYPOST-616](https://pypost.atlassian.net/browse/PYPOST-616) |

## Blocker review

**Verdict: SAFE TO CLOSE** — acceptance criteria met; no blocking debt introduced.
