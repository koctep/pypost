# PYPOST-1420: Observability Implementation

## Logging Implementation

### Scope and Context

This ticket changes only the **workspace population** path inside
`tests/helpers/shared_venv_manager.py` (`SharedVenvManager.materialize` /
`tree_copier`). That helper remains **test harness infrastructure**, not a
deployed production service under `pypost/`.

Per repository test standards and the `do-testing` contract (and continuity
with PYPOST-1419), fixture helpers must avoid uncontrolled root-logger /
`sys.stderr` noise on the healthy path. Unstructured INFO/DEBUG logging would
pollute pytest `log_cli` output and can conflict with `caplog` assertions.
Observability for in-process materialization therefore stays **intentionally
minimal** and is realized through:

1. Fail-loud, stage-scoped `RuntimeError` diagnostics (FR5 preserved).
2. Soft post-copy deadline via injected `_clock` (API-compatible `copy_timeout`).
3. Source-kind tagging (`skeleton` vs `base`) on failure messages for CI triage.
4. Existing readiness markers and load-budget assertions in
   `tests/test_makefile_shared_readiness.py` /
   `tests/test_shared_venv_manager.py`.

No `logging` / OpenTelemetry / Prometheus instrumentation was added to the
manager for this ticket.

### Added Logs

Mapped syslog-compatible levels to diagnostic surfaces:

- **EMERG**: N/A — Test harness does not manage host/kernel emergencies.
- **ALERT**: N/A — Test harness does not own operator paging.
- **CRIT**: N/A — Critical production alerts do not apply to local/CI fixtures.
- **ERR**: Contextual exceptions in `SharedVenvManager.materialize`:
  - Soft deadline: `TimeoutError` when post-copy elapsed time exceeds
    `copy_timeout`, including `elapsed` (seconds) and `source` kind
    (`skeleton`|`base`); cleaned/wrapped as
    `RuntimeError("shared venv materialization failed: <target> (source=<kind>): …")`.
  - Copy failures: `OSError` / `shutil.Error` (and injected `tree_copier`
    faults such as simulated `TimeoutError`) remove partial `workspace/.venv`
    then raise the same stage-aware `RuntimeError` with `source=` context.
  - Bootstrap / lock / publication errors remain as documented under PYPOST-1419
    (`ensure_ready` / `_run`); population no longer routes through
    `preparation_runner` / `cp`.
- **WARNING**: N/A at materialize scope — no soft-degraded continue-after-fault
  path; failures fail closed after partial cleanup.
- **NOTICE**: N/A — Readiness is expressed via on-disk markers and owned
  `resolved_base` / `is_ready()` state, not notice-level logs.
- **INFO**: N/A — Healthy in-process materialization is silent by design
  (avoid pytest log noise). Success is observable via ready workspace markers
  and green suites.
- **DEBUG**: Nested exception cause (`from error`) retains the original
  `TimeoutError` / `OSError` / `shutil.Error` detail in pytest failure reports
  and CI console output. No tree listings or full venv contents are emitted.

### Log Structure

Log format used:
- Structured logs: Yes (exception messages use stable target/source/elapsed/
  budget fields; no free-form print noise).
- Includes context: Yes (target path, `source=skeleton|base`, copy timeout /
  elapsed on soft deadline, nested copy error).
- Log levels: Exception-equivalent `ERR` (+ nested cause as debug detail on
  failure). No production logger hierarchy introduced for this helper.
- Sanitization: Large venv trees are **not** dumped; only scalar
  path/kind/timing fields and the failing exception text are retained.

## Metrics Implementation (if applicable)

### Performance Metrics

No production metrics exporters were added. Harness/test telemetry remains:

- **Response time**: Soft `copy_timeout` monotonic check after `tree_copier`
  returns; parallel wall-clock covered by
  `tests/test_makefile_shared_readiness.py::test_parallel_workspace_materialization_under_load_budget`
  (NFR1 — may improve vs prior `cp -a` fork/exec).
- **Throughput**: Concurrent workspace materialization under load remains
  asserted by the readiness suite; in-process copy removes per-workspace
  process-spawn overhead.
- **Error rate**: Fail-closed — any materialization error raises immediately
  after cleanup of partial targets.

### Business Metrics

Business metrics:
- N/A for production KPIs — this is test infrastructure. The outcome is lower
  parallel Makefile preparation overhead with unchanged isolation/readiness
  guarantees, measured by green readiness/manager suites rather than product
  counters.

### System Health Metrics

System health metrics:
- **Resource usage**: N/A for Prometheus-style host metrics. Skeleton + `.pth`
  population continues to limit per-workspace filesystem cost; in-process
  `copytree(..., symlinks=True)` avoids fork/exec.
- **Component status**: Readiness markers on base/skeleton/workspace plus
  `is_ready()` / `resolved_base`; materialize early-returns when the target is
  already ready.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics (N/A — transient pytest/Make fixture helper)
- [ ] Grafana dashboards (N/A — durations/failures via pytest / CI / parallel runner)
- [x] Alerting rules (CI fails on nonzero `make` / pytest exit when materialize raises)
- [x] Log aggregation (pytest failure output and CI console capture stage-scoped diagnostics)

## Validation Results

Validation results:
- [x] Logs are correctly formatted — materialization `RuntimeError` messages
  retain target, `source=` kind, and nested cause without dumping trees
- [x] Metrics are collected correctly — soft timeout + load-budget assertions
  remain the timing telemetry surface (no new exporter)
- [x] Logging works in error scenarios — FR5 timeout/partial cleanup covered by
  `test_materialize_timeout_cleans_partial_target_and_identifies_stage` and
  readiness failure/retry case
- [x] Large data structures are not logged — only scalar path/kind/timing fields
- [x] Metrics are available for monitoring — via CI exit status, pytest reports,
  and existing readiness/load-budget assertions
- [x] Focused suites green after diagnostic message enrichment:
  `make test PYTEST_ARGS='tests/test_shared_venv_manager.py tests/test_makefile_shared_readiness.py -q --tb=short'`

## Notes

- **Intentional minimalism**: Adding `logging.getLogger(__name__)` INFO/DEBUG on
  every successful `materialize` would violate the harness observability
  philosophy (PYPOST-1413 / PYPOST-1419): silent success, fail-loud diagnostics,
  no stdout pollution.
- **FR5 continuity**: Failures still identify the materialization stage; new
  `source=skeleton|base` field improves triage when skeleton fallback occurs.
- **Soft timeout semantics**: Deadline is checked after `tree_copier` returns
  (cannot cancel an in-flight `copytree`). Preemptive cancellation would require
  a different copy collaborator — out of scope; see Step 7.
- **Production gap**: If shared-venv preparation becomes a long-lived host
  service, revisit structured logging and duration histograms. Out of scope for
  PYPOST-1420.
- Step 6 remains `[/]` pending independent review / acceptance gate.
