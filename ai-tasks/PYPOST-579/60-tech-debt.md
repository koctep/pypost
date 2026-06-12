# PYPOST-579: Technical Debt (Step 6)

## Resolved in this task

- PYPOST-73 follow-up "No OpenTelemetry adapter" — `OtelMetricsTracker` implements
  `MetricsTrackerProtocol` with Prometheus-compatible names.

## Remaining / follow-up

| ID | Priority | Item | Notes |
| --- | --- | --- | --- |
| TD-1 | Low | Wire OTel adapter in production composition root | Requires operator OTLP config; desktop default stays Prometheus | [PYPOST-583](https://pypost.atlassian.net/browse/PYPOST-583) |
| TD-2 | Low | Shared instrument definition table | `MetricsRegistry` and `OtelMetricsTracker` duplicate instrument metadata | [PYPOST-584](https://pypost.atlassian.net/browse/PYPOST-584) |

## Blocker review

**SAFE TO CLOSE** — acceptance criteria met; remaining items are optional production wiring
and DRY convenience.
