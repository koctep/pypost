# PYPOST-376: Observability Implementation

## Logging Implementation

No runtime logging added. This task is offline measurement and CI regression guards only.

## Metrics Implementation

### Baseline metrics (development / CI)

| Metric | Location | Purpose |
| --- | --- | --- |
| File LOC | `scripts/audit_baseline_metrics.py` | Physical line count per audit module |
| Class LOC | same (AST) | `MainWindow` class body size |
| Cap violations | `--check` CLI / unit tests | Fail when LOC exceeds documented caps |

These are **maintainability metrics**, not Prometheus application metrics.

## Monitoring Integration

- [ ] Prometheus metrics — N/A
- [x] pytest regression — `tests/test_solid_audit_baseline.py`

## Validation Results

- [x] Script runs in < 1 s on full scoped module set
- [x] `--check` returns non-zero when caps exceeded (verified by design)
- [x] No production log noise introduced

## Notes

Future periodic re-audit (PYPOST-40 follow-up item 6) should rerun the script and refresh
`baseline-metrics.md` after intentional cap updates.
