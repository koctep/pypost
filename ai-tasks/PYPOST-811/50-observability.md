# PYPOST-811: Observability

## Scope

Optional import guard only — no new metrics instruments, log lines, or tracing spans.

## Runtime impact

| Scenario | Behavior |
| --- | --- |
| Production install (no OTel) | Module import succeeds; tracker construction fails fast with `ImportError` |
| OTel overlay installed | Unchanged — `OtelMetricsTracker` records the same instruments as before |

## Test coverage

| Test | Signal |
| --- | --- |
| `test_metrics_otel_importable_without_otel_packages` | Module loads when OTel blocked |
| `test_otel_tracker_requires_otel_when_missing` | Runtime guard on tracker init |
| `test_create_otel_metrics_tracker_requires_otel_when_missing` | Runtime guard on factory |
| `tests/test_metrics_otel.py` | Full instrument parity when OTel present |

## N/A

- No new Prometheus or OTel metric names
- No application logging changes
