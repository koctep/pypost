# PYPOST-73: Observability

## Impact

No change to Prometheus metric names, labels, scrape paths, or tracking call behavior.

## Type-level only

- Protocol documents the existing tracking API surface.
- Runtime metrics flow unchanged: `MetricsManager` still delegates to `MetricsRegistry`.

## Tests

- `tests/test_metrics_protocol.py` — protocol satisfaction
- Existing metrics tests (`test_metrics_manager.py`, integration tests) unchanged
