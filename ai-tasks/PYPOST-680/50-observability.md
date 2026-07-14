# PYPOST-680: Observability (Step 5)

## Scope

No new metrics or log statements. Task documents how agents should read existing envelope
fields that align with `track_mcp_response_sent` outcomes.

## Existing signals (unchanged)

| Signal | Location | Agent mapping |
| --- | --- | --- |
| `mcp_requests_received_total` | Prometheus :9080 | Unchanged — operator metric |
| Envelope `error` flag | `TextContent.text` JSON | `true` → PyPost execution failure |
| Envelope `status` | `TextContent.text` JSON | Upstream HTTP status; `0` on dispatch failure |
| Integration tests | `test_mcp_server_integration.py` | Parses envelope via `json.loads` |

## Operator guidance

Agents should treat `payload["error"]` as the PyPost execution outcome (not upstream 4xx/5xx).
Use `payload["status"]` for HTTP status and `payload["body"]` for upstream response text.
Optional `payload["logs"]` holds post-request script output.
