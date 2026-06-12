# PYPOST-167: Observability

## Impact

DI refactor (PYPOST-44) did not alter observability behavior:

| Surface | Unchanged |
| --- | --- |
| Prometheus counters | Same names and labels via `MetricsRegistry` |
| HTTP GET `/metrics` | Started from `main.py` via `metrics_manager.start_server()` |
| MCP `metrics://all` | Same resource URI |
| Default port | 9080 (settings) |

## Verification

- `tests/test_metrics_manager.py` — counter tracking via facade
- `tests/test_metrics_protocol.py` — `MetricsManager` satisfies `MetricsTrackerProtocol`
- `tests/test_metrics_server_startup.py` — server lifecycle from injected instance

No new logging or metrics added for this debt closure.
