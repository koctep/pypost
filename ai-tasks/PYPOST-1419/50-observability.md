# PYPOST-1419: Observability Implementation

## Logging Implementation

### Scope and Context

`tests/helpers/shared_venv_manager.py` (`SharedVenvManager`) and the thin facades in
`tests/makefile_test_helpers.py` are **test harness infrastructure**, not a deployed
production service. This ticket only encapsulates the shared virtualenv lifecycle already
hardened in PYPOST-1413; it does not introduce a new runtime component under `pypost/`.

Per repository test standards and the `do-testing` contract, fixture helpers must avoid
writing uncontrolled log records to root loggers or `sys.stderr` during healthy operation.
Unstructured logging would pollute pytest `log_cli` output and can conflict with
test-level `caplog` assertions. Therefore observability for this encapsulation is
**intentionally minimal** and is realized through:

1. Fail-loud, stage-scoped `RuntimeError` diagnostics (FR5 preserved).
2. Captured subprocess streams attached to exception objects (via the injectable
   `preparation_runner`, defaulting to `_run_preparation_command`).
3. Bounded monotonic preparation budgets and readiness markers already validated by
   `tests/test_makefile_shared_readiness.py` and `tests/test_shared_venv_manager.py`.

No new `logging` / OpenTelemetry / Prometheus instrumentation was added to the manager.

### Added Logs

Mapped syslog-compatible levels to existing diagnostic surfaces:

- **EMERG**: N/A — Test harness does not manage host/kernel emergencies.
- **ALERT**: N/A — Test harness does not own operator paging or on-call alerts.
- **CRIT**: N/A — Critical production alerts do not apply to local/CI fixture code.
- **ERR**: Contextual exceptions in `tests/helpers/shared_venv_manager.py`:
  - `SharedVenvManager._run` — `RuntimeError` when `preparation_runner` is not configured.
  - `SharedVenvManager.ensure_ready` — `RuntimeError` on stage deadline expiration
    (`lock`, `creation`, `installation`, `validation`, `publication`), identifying the
    failing stage, shared venv path, and configured preparation budget.
  - `SharedVenvManager.ensure_ready` — `RuntimeError` on bootstrap stage failure, including
    stage name, venv path, preparation budget, inner exception, and captured
    `stderr`/`output` when present.
  - `SharedVenvManager.ensure_ready` — `RuntimeError` when validation finds a missing
    interpreter under the shared base.
  - `SharedVenvManager.materialize` — `RuntimeError` on copy failure with target path and
    subprocess exception context; partial `workspace/.venv` is removed before re-raise.
  - Default runner (`_run_preparation_command` in `tests/makefile_test_helpers.py`) —
    `subprocess.TimeoutExpired` / `CalledProcessError` with command vector, timeout,
    and captured streams (unchanged from PYPOST-1413).
- **WARNING**: N/A at manager scope — no soft-degraded paths that continue after a
  preparation fault; failures fail closed. Runner-level warnings for parallel fixture
  preparation remain owned by `scripts/run_parallel_tests.py` (documented under
  PYPOST-1413; unchanged by this encapsulation).
- **NOTICE**: N/A — No significant operational notices beyond exception diagnostics;
  readiness is expressed via on-disk markers and owned `resolved_base` state.
- **INFO**: N/A — Healthy bootstrap/materialization is silent by design (avoid pytest
  log noise). Success is observable via returned paths, ready markers, and green tests.
- **DEBUG**: Subprocess `stdout`/`stderr` retained on exception objects and surfaced in
  pytest failure reports / CI console output when a stage fails.

### Log Structure

Log format used:
- Structured logs: Yes (exception messages use stable stage/path/budget fields; no free-form
  print noise). Structured runner key=value events remain at the parallel runner boundary.
- Includes context: Yes (stage name, shared/workspace paths, preparation budget,
  remaining deadline semantics, nested subprocess detail).
- Log levels: Exception-equivalent `ERR` (+ `DEBUG` stream attachment on failure). No
  production logger hierarchy introduced for this helper.
- Sanitization: Large venv trees and full pip install trees are **not** dumped into logs;
  only stage identifiers, paths, budgets, and captured failing-command streams are retained.

## Metrics Implementation (if applicable)

### Performance Metrics

No production metrics exporters were added. Existing harness/test telemetry remains sufficient:

- **Response time**: Monotonic preparation budget countdown inside
  `SharedVenvManager.ensure_ready` (`remaining(stage)`); materialization wall-clock covered by
  `tests/test_makefile_shared_readiness.py::test_parallel_workspace_materialization_under_load_budget`.
- **Throughput**: Concurrent workspace materialization under load remains asserted by the
  readiness suite (NFR1 preserved; encapsulation must not regress timing).
- **Error rate**: Fail-closed — any preparation/materialization error raises immediately after
  cleanup of partial targets.

### Business Metrics

Business metrics:
- N/A for production business KPIs — this is test infrastructure. The business outcome is
  reliable CI/Makefile workspace preparation without flaky stale-cache failures, measured by
  green readiness and manager suites rather than product counters.

### System Health Metrics

System health metrics:
- **Resource usage**: N/A for Prometheus-style host metrics. Skeleton + `.pth` materialization
  continues to limit per-workspace filesystem copy cost (behavior owned since PYPOST-1413).
- **Component status**: Readiness markers (`.initialized-<PYTHON_VERSION>` on base, skeleton,
  and workspace) plus `SharedVenvManager.resolved_base` / `is_ready()` as the owned readiness
  source of truth (replacing module-level path-cache SoT).

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics (N/A — transient pytest/Make fixture helper, not a long-lived service)
- [ ] Grafana dashboards (N/A — durations and failures reported via pytest / CI / parallel runner)
- [x] Alerting rules (CI fails on nonzero `make` / pytest exit codes when preparation raises)
- [x] Log aggregation (pytest failure output and CI console capture stage-scoped diagnostics)

## Validation Results

Validation results:
- [x] Logs are correctly formatted — stage-scoped `RuntimeError` messages retain actionable
  fields without dumping large data structures
- [x] Metrics are collected correctly — monotonic budgets and load-budget assertions remain the
  timing telemetry surface (no new exporter required)
- [x] Logging works in error scenarios — lock deadline, bootstrap stage failure, missing
  interpreter, and materialization failure paths raise with context (covered by
  `tests/test_shared_venv_manager.py` and readiness suite)
- [x] Large data structures are not logged — only scalar stage/path/budget fields and failing
  command streams
- [x] Metrics are available for monitoring — via CI exit status, pytest reports, and existing
  readiness/load-budget assertions

## Notes

- **Intentional minimalism**: Adding `logging.getLogger(__name__)` INFO/DEBUG noise to
  `SharedVenvManager` would violate the harness observability philosophy established for
  Makefile fixtures (PYPOST-1413) and sibling helper encapsulation (PYPOST-1429): silent
  success, fail-loud diagnostics, no stdout pollution.
- **FR5 continuity**: Encapsulation preserves identifiable failure stages (`lock`,
  `creation`, `installation`, `validation`, `publication`, materialization) for CI triage.
- **Production gap**: If a future ticket promotes shared-venv preparation into a long-lived
  host service, revisit this step to add structured logging and duration histograms. That is
  out of scope for PYPOST-1419.
