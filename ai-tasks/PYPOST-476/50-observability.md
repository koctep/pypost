# PYPOST-476: Observability

## Validation observability (unchanged)

Validation metrics and logging were implemented in PYPOST-163 and tuned in PYPOST-473:

| Signal | Scope | Performance note |
| --- | --- | --- |
| `gui_variable_validation_total` | Per attempt | Counter increment only; negligible |
| `gui_variable_validation_failures_total` | On invalid names | Counter increment only |
| DEBUG log | Failed attempts only | Single log line; negligible vs dialog |

## Performance verification

Micro-benchmark (local dev machine, CPython 3.x, 200k iterations):

| Scenario | Latency |
| --- | --- |
| Valid name (7 chars) | ~0.3 µs/call |
| Long valid name (500 chars) | ~8.6 µs/call |
| Mixed batch (6 names × validate + failure_reason) | ~1.6 µs/op |

Presenter wrapper adds two Prometheus increments and (on failure) one DEBUG log — still
microseconds total, dwarfed by `QInputDialog` and `_save_environments()`.

No additional metrics or logging recommended for performance monitoring.
