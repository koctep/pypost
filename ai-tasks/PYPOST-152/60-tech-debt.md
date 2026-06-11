# PYPOST-152: Technical debt

## Resolved

- **Hardcoded routes (PYPOST-20)** — SSE and streamable HTTP paths now live in
  `mcp_transport_routes.py`.

## Follow-ups

| ID | Priority | Item | Notes |
| --- | --- | --- | --- |
| TD-1 | Low | Optional AppSettings override for custom MCP paths | Only if product needs per-install path prefix; constants suffice today. |
| TD-2 | Low | Metrics server flat `/messages` vs main nested `/sse/messages` | Pre-existing layout difference; document if unifying ever needed. |

## Worklog

role: execution, step: 6, step_name: Review, tokens_used: 800
