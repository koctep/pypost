# PYPOST-153: Observability

## Logging

| Event | Level | Fields |
| --- | --- | --- |
| Metrics server starting | INFO | host, port |
| Metrics listening | INFO | `metrics_server_listening` host, port |
| Metrics start failed | ERROR | `metrics_server_start_failed` host, port, message |
| Metrics unexpected exit | WARNING | `metrics_server_unexpected_exit` |
| UI metrics failure | ERROR | `metrics_server_start_failed_ui` message |

## Metrics

No new Prometheus counters.

## Worklog

role: execution, step: 5, step_name: Observability, tokens_used: 800
