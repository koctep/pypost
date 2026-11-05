# PYPOST-1357: Observability Implementation

## Decision

**No production logging or metrics change.** PYPOST-1357 remediates a test-harness
lifetime gap: registry + autouse dispose for collection export UI presenters
(`tests/test_collection_export_ui.py`, `tests/test_collection_export_ui_teardown_repro.py`)
so a missed `finally` still reaches `dispose_collections_export_fixture`. Production
modules under `pypost/` are unchanged. Architecture Step 6 guidance for this task is
explicit: observability only if durable diagnostics are added — likely thin / N/A for
harness-only work. Completion Criteria are met by documenting that production
observability is out of scope and that existing CI / runner signals plus the
collections dispose contract already cover the failure class.

## Observability Requirements Analysis

| Path | Production relevance | Monitoring need |
| --- | --- | --- |
| `_created_presenters` + autouse `_cleanup_collections_export_presenters` | Test-only; pytest worker teardown | None — silent, idempotent safety net |
| `dispose_collections_export_fixture` / `dispose_qt_root` | Test helper only (reuse from PYPOST-1315) | None — success proven by contract asserts |
| Collection export UI product flows | Unchanged | Existing product logs/metrics unchanged |
| Post-PASS worker SIGSEGV (`exit_code=-11`) | Observed only under `make test` / `make check` | Already surfaced by `scripts/run_parallel_tests.py` as file failure |

Critical execution path for this bug is **worker finalization after green assertions**
(and missed-`finally` dispose coverage), not a user-facing product operation. Adding
structured logs or metrics inside the autouse fixture or dispose helper would not improve
production monitoring: those paths never run in the shipped app, and per-test DEBUG noise
would not help operators diagnose a native crash that already kills the worker before
Python logging can report process exit.

Cause fork for this ticket (**R-autouse**): remediation is harness dispose completeness,
not a new production telemetry surface. B’s zero-crash diagnostic matrix on the restored
host (PySide6 / shiboken6 / pydantic versions) is evidence archived in the repro test
pass path, not a production metric series.

## Logging Implementation

### Added Logs

No logging added to `tests/helpers/qt_widget_dispose.py`,
`tests/test_collection_export_ui.py`, or
`tests/test_collection_export_ui_teardown_repro.py`.

- **EMERG**: N/A
- **ALERT**: N/A
- **CRIT**: N/A
- **ERR**: N/A
- **WARNING**: N/A
- **NOTICE**: N/A
- **INFO**: N/A
- **DEBUG**: N/A

### Why not add test-helper logs

- Autouse dispose is synchronous and idempotent; success is proven by contract assertions
  (`shiboken6.isValid` false, no leftover collections export UI roots in
  `topLevelWidgets()`), including the R-autouse missed-`finally` guard — not by log lines.
- Native SIGSEGV after PASS cannot be caught with Python logging in the dying worker; the
  parallel runner already records `exit_code=-11` / `-7`.
- Logging every registry dispose would add volume across the nineteen collection export UI
  tests (plus repro members) without a production consumer.

### Existing signals that cover this class (unchanged)

- Parallel orchestrator: non-zero worker exit (including `exit_code=-11`) recorded as file
  failure — see `doc/dev/parallel_test_runner.md` / PYPOST-1212 patterns.
- Step 3/4 collections contract: `tests/test_collection_export_ui_teardown_repro.py`
  (A-complete desired end-state, A-incomplete residual-liveness, R-autouse missed-finally,
  B bounded subprocess / diagnostic matrix).
- Shared dispose helper and env-export sibling signals from PYPOST-1315 remain the
  lifetime/teardown family documentation path (`doc/dev/export_ui_qt_dispose.md`).

### Log Structure

- Structured logs: N/A (no new logging)
- Includes context: N/A
- Log levels: N/A

## Metrics Implementation (if applicable)

### Performance Metrics

- **Response time**: N/A
- **Throughput**: N/A
- **Error rate**: N/A — worker native crashes remain CI exit-code failures, not Prometheus
  series

### Business Metrics

- N/A — no product collection-export behavior change

### System Health Metrics

- **Resource usage**: N/A
- **Component status**: N/A

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics (N/A — test harness only)
- [ ] Grafana dashboards (N/A)
- [ ] Alerting rules (N/A — CI fails the Make gate when a worker exits non-zero)
- [ ] Log aggregation (ELK, Loki, etc.) (N/A — no new log events)

## Validation Results

Validation results:

- [x] No new production logs or metrics required for this change set
- [x] Dispose helper and autouse fixtures remain silent (source inspection of
  `qt_widget_dispose.py` and collection export UI / teardown repro modules)
- [x] Large data structures are not logged (no logging added)
- [ ] Metrics are collected correctly (N/A)
- [ ] Metrics are available for monitoring (N/A)
- [x] Failure observability retained via existing parallel-runner exit codes and
  collections dispose contract assertions (documented; no code change in this step)

## Notes

- This step changes task documentation only (`50-observability.md` + roadmap Step 6 notes).
- No `pypost/`, `tests/`, or Makefile edits in Step 6.
- Follow-up candidates (if any) for harness polish or env-only remainder belong in Step 7
  tech debt, not production telemetry.
- Distinct from PYPOST-1315’s observability note only in scope (collections R-autouse /
  missed-finally safety net); same N/A conclusion for production observability.
