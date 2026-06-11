# PYPOST-177: Observability

## Verification

Tests assert the existing Prometheus counters used for MCP observability:

| Counter | Labels | Covered by |
| --- | --- | --- |
| `mcp_requests_received_total` | `method` | `test_metrics_registry.py`, `test_metrics_server_endpoint.py` |
| `mcp_responses_sent_total` | `method`, `status` | same |

HTTP `/metrics` scrape path verified via Starlette `TestClient` without uvicorn.

## Logging

No new log statements — test-only task.
