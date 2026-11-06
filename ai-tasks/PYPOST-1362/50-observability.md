# PYPOST-1362: Observability

## Requirements Analysis

- Critical path: MCP bind failure → `start_failed` → registry `failed` → worker exit /
  thread-ref clear → callers observe `is_running() == False`.
- Isolation path: peer instances must remain `running` while one instance fails to bind.
- Existing ERROR/INFO events already cover the failure signal; this task does not add new
  high-volume logs.

## Logging Added / Retained

| Event | Level | When | Notes |
| --- | --- | --- | --- |
| `mcp_server_start_failed` | ERROR | Bind/start failure in worker | Existing; host/port/message only |
| `mcp_registry_status` | INFO | Status transitions including `failed` | Existing; `message_present` flag |
| `MCP server starting on …` | INFO | Thread start | Existing |
| `MCP server stopped` | INFO | `stop_server` completion | Existing |

No new log lines for thread-ref clear (hot path / expected after every worker exit). Clearing
is covered by deterministic tests rather than DEBUG spam.

## Metrics

- Existing registry instance-count gauges via `_publish_instance_metrics` on status change
  (including `failed`) — unchanged.
- No new Prometheus/OTel series required for this debt fix.

## Validation

- Failed-bind tests exercise `mcp_server_start_failed` and `mcp_registry_status … state=failed`
  under occupied-port scenarios.
- Peer isolation asserts alpha remains running / listable after beta fails.

## Checklist

- [x] Key failure path already logged at ERROR with host/port/message
- [x] No large structures logged
- [x] No new noisy DEBUG on every thread exit
- [x] Metrics for failed/running counts remain published through status updates
