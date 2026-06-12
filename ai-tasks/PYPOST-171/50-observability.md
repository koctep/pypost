# PYPOST-171: Observability

## Impact

Lock review does not change observability behavior:

| Surface | Unchanged |
| --- | --- |
| `metrics_server_listening` log | Emitted from worker after uvicorn startup |
| `metrics_server_start_failed` log | Bind/startup failures |
| `metrics_server_restarting` log | `MainWindow` before `restart_server` |
| Prometheus counters | Unaffected by lifecycle lock |

## Verification

- `tests/test_metrics_server_startup.py` — port listen, bind failure, pending failure replay
- `tests/test_metrics_server_integration.py` — HTTP/MCP scrape paths

No new logging or metrics added for this debt closure.
