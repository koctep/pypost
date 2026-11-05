# PYPOST-1315: Observability Implementation

## Decision

**No production logging or metrics change.** PYPOST-1315 adds a test-only Qt dispose
helper (`tests/helpers/qt_widget_dispose.py`) and wires it into export UI test fixtures /
`finally` paths. Production modules under `pypost/` are unchanged. Architecture Step 6
guidance for this task is explicit: observability only if new durable diagnostics are
added — likely thin or N/A for test-harness-only work. Completion Criteria are met by
documenting that production observability is out of scope and that existing CI / runner
signals plus deterministic contract assertions already cover the failure class.

## Observability Requirements Analysis

| Path | Production relevance | Monitoring need |
| --- | --- | --- |
| `dispose_qt_root` / `dispose_collections_export_fixture` | Test helper only; runs inside pytest workers | None — silent, idempotent teardown |
| Environment / collection export UI product flows | Unchanged | Existing product logs/metrics unchanged |
| Post-PASS worker SIGSEGV (`exit_code=-11`) | Observed only under `make test` / `make check` | Already surfaced by `scripts/run_parallel_tests.py` as file failure |

Critical execution path for this bug is **worker finalization after green assertions**, not a
user-facing product operation. Adding structured logs or metrics inside the dispose helper
would not improve production monitoring: the helper never runs in the shipped app, and per-
test DEBUG noise would not help operators diagnose a native crash that already kills the
worker before Python logging can report process exit.

## Logging Implementation

### Added Logs

No logging added to `tests/helpers/qt_widget_dispose.py` or the export UI test modules.

- **EMERG**: N/A
- **ALERT**: N/A
- **CRIT**: N/A
- **ERR**: N/A
- **WARNING**: N/A
- **NOTICE**: N/A
- **INFO**: N/A
- **DEBUG**: N/A

### Why not add test-helper logs

- Dispose is synchronous and idempotent; success is proven by contract assertions
  (`shiboken6.isValid` false, no leftover export UI roots in `topLevelWidgets()`), not by
  log lines.
- Native SIGSEGV after PASS cannot be caught with Python logging in the dying worker; the
  parallel runner already records `exit_code=-11` / `-7`.
- Logging every dispose would add volume on the eight environment + many collection export
  UI tests without a production consumer.

### Existing signals that cover this class (unchanged)

- Parallel orchestrator: `ERROR test_file_failed … exit_code=-11` (and signal decoding for
  SIGSEGV / SIGBUS) — see `doc/dev/parallel_test_runner.md` / PYPOST-1212 patterns.
- Step 3/4 contract repro: `tests/test_environment_export_ui_teardown_repro.py` fails if
  disposal leaves live roots.
- Bounded subprocess matrix archives child return codes (evidence when host can reproduce
  native death).

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

- N/A — no product request/export behavior change

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
- [x] Dispose helper remains silent (source inspection of `qt_widget_dispose.py`)
- [x] Large data structures are not logged (no logging added)
- [ ] Metrics are collected correctly (N/A)
- [ ] Metrics are available for monitoring (N/A)
- [x] Failure observability retained via existing parallel-runner exit codes and contract
  assertions (documented; no code change in this step)

## Notes

- This step changes task documentation only (`50-observability.md` + roadmap Step 6 notes).
- No `pypost/`, `tests/`, or Makefile edits in Step 6.
- Follow-up candidates (if any) for harness-level session topLevelWidgets purge belong in
  Step 7 tech debt, not production telemetry.
