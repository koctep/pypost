# PYPOST-750 — Observability

## Impact

**Documentation only.** No new log lines, metrics, or alert behavior.

## Deliverable

Complete operator catalog in `doc/prometheus_monitoring.md`:

- 32 instruments (30 counters, 1 gauge, 1 histogram) from `metrics_registry.py`
- Per-metric name, type, labels, and meaning
- Corrected prior statement that PyPost registers counters only

## Verification

`make check` — docs do not affect runtime observability.
