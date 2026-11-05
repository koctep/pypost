# PYPOST-1358: Observability Implementation

## Decision

**No production logging or metrics change.** PYPOST-1358 remediates a test-harness
lifetime gap: `_created_widgets` registry + autouse `_cleanup_widgets` calling
`dispose_qt_root` in `tests/test_environment_list_widget.py`, with the R-dispose
contract driven by `tests/test_environment_list_widget_teardown_repro.py`. Production
modules under `pypost/` are unchanged. Architecture Steps 5–8 guidance for this task
is explicit: observability only if durable diagnostics are added — likely thin / N/A
for harness-only work. Completion Criteria are met by documenting that production
observability is out of scope and that existing CI / runner signals plus the list
dispose contract already cover the failure class.

## Observability Requirements Analysis

| Path | Production relevance | Monitoring need |
| --- | --- | --- |
| `_created_widgets` + autouse `_cleanup_widgets` | Test-only; pytest worker teardown | None — silent, idempotent safety net |
| `dispose_qt_root` | Test helper only (reuse from PYPOST-1315) | None — success proven by contract asserts |
| Environment list / import UI product flows | Unchanged | Existing product logs/metrics unchanged (suite already asserts import INFO via `caplog` where applicable) |
| Post-PASS worker SIGSEGV/SIGBUS (`exit_code=-11` / `-7`) | Observed only under `make test` / `make check` | Already surfaced by `scripts/run_parallel_tests.py` as file failure |

Critical execution path for this bug is **worker finalization after green assertions**
(close-only survivors of unparented `EnvironmentListWidget` roots), not a user-facing
product operation. Adding structured logs or metrics inside the autouse fixture or
dispose helper would not improve production monitoring: those paths never run in the
shipped app, and per-test DEBUG noise would not help operators diagnose a native crash
that already kills the worker before Python logging can report process exit.

Cause fork for this ticket (**R-dispose** / H1, with registry/autouse hardening H2):
remediation is harness dispose completeness for the list/import suite (mirroring env
export PYPOST-1315), not a new production telemetry surface. B’s zero-crash diagnostic
matrix on this host is evidence archived in the repro test pass path, not a production
metric series.

## Logging Implementation

### Added Logs

No logging added to `tests/helpers/qt_widget_dispose.py`,
`tests/test_environment_list_widget.py`, or
`tests/test_environment_list_widget_teardown_repro.py` for this step.

- **EMERG**: N/A
- **ALERT**: N/A
- **CRIT**: N/A
- **ERR**: N/A
- **WARNING**: N/A
- **NOTICE**: N/A
- **INFO**: N/A — no new product INFO; existing import-path `caplog` assertions in the
  list suite are pre-existing product coverage, not dispose telemetry
- **DEBUG**: N/A

### Why not add test-helper logs

- Registry/autouse dispose is synchronous and idempotent; success is proven by contract
  assertions (`shiboken6.isValid` false / desired end-state in A-complete and R-dispose;
  A-incomplete remains the close-only residual-liveness negative control) — not by log
  lines.
- Native SIGSEGV/SIGBUS after PASS cannot be caught with Python logging in the dying
  worker; the parallel runner already records `exit_code=-11` / `-7`.
- Logging every registry dispose would add volume across the thirteen environment list
  widget tests (plus repro members) without a production consumer.

### Existing signals that cover this class (unchanged)

- Parallel orchestrator: non-zero worker exit (including `exit_code=-11` / `-7`) recorded
  as file failure — see `doc/dev/parallel_test_runner.md` / PYPOST-1212 patterns.
- Step 3/4 list dispose contract: `tests/test_environment_list_widget_teardown_repro.py`
  (A-complete desired end-state, A-incomplete residual-liveness, R-dispose suite dispose
  path, B bounded subprocess / diagnostic matrix).
- Shared dispose helper and env-export / collections sibling signals from PYPOST-1315 /
  PYPOST-1357 remain the lifetime/teardown family documentation path
  (`doc/dev/export_ui_qt_dispose.md`; list/import suite coverage is a Step 8 doc note).

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

- N/A — no product environment-list / import behavior change

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
- [x] Dispose helper and list-suite autouse fixtures remain silent (source inspection of
  `qt_widget_dispose.py` and environment list widget / teardown repro modules)
- [x] Large data structures are not logged (no logging added)
- [ ] Metrics are collected correctly (N/A)
- [ ] Metrics are available for monitoring (N/A)
- [x] Failure observability retained via existing parallel-runner exit codes and list
  dispose contract assertions (documented; no code change in this step)

## Notes

- This step changes task documentation only (`50-observability.md` + roadmap Step 6 notes).
- No `pypost/`, `tests/`, or Makefile edits in Step 6.
- Follow-up candidates (if any) for harness polish or export-doc asymmetry belong in
  Step 7 / Step 8, not production telemetry.
- Same N/A conclusion as PYPOST-1315 / PYPOST-1357 for production observability; scope
  here is the environment **list/import** suite R-dispose + registry/autouse wiring.
