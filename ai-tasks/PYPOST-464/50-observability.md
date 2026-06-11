# PYPOST-464: Observability Implementation

Test-only task: no new production logs or metrics were added. This step documents the new
**metric counter regression tests** and confirms production observability is unchanged.

## Logging Implementation

### Added Logs

None. This task adds test coverage for an existing PYPOST-446 metric only.

## Metrics Implementation

### Production metrics (unchanged)

| Metric | Labels | Emission rule |
| --- | --- | --- |
| `hidden_value_masks_applied_total` | `surface` | Incremented when `hidden_key_count > 0` at history write |

### New test coverage

`tests/test_history_masking_metrics.py` scrapes a real `MetricsManager` registry after
`RequestService.execute` and asserts:

- Counter **absent** when `hidden_keys` is `set()` or `None`.
- Counter **`1.0`** for `surface="history"` when `hidden_keys` is non-empty.

This complements mock-based checks in `tests/test_request_service.py` by validating Prometheus
output, not just method calls.

## Monitoring Integration

No new Prometheus/Grafana/alerting integration. Desktop app; tests use in-process registry scrape.

## Validation Results

- [x] Metric counter positive case verified via scrape
- [x] Metric counter negative cases verified via scrape (empty and None hidden_keys)
- [x] No production observability changes required

## Notes

- Traceability: closes the missing-coverage item in
  [PYPOST-446 technical-debt analysis](ai-tasks/PYPOST-446/60-tech-debt.md).
- Parent observability design:
  [PYPOST-446/50-observability.md](ai-tasks/PYPOST-446/50-observability.md).
