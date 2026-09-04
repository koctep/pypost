# PYPOST-1153: Observability Implementation

## Assessment

The parallel runner is a short-lived developer and CI command, so its durable observability
surface is structured stderr logging plus the existing `RunSummary` and optional JSON report.
Adding a Prometheus or OpenTelemetry exporter would introduce a process-lifecycle and dependency
contract that the runner does not need. The implementation therefore keeps metrics local to the
run and exposes scalar measurements in logs and result objects.

## Logging Implementation

### Added Logs

All events use the existing `EVENT key=value` format and are emitted by
`scripts.run_parallel_tests`:

- **EMERG / ALERT / CRIT**: N/A — the runner has no long-lived service or recovery action.
- **ERR**:
  - `coverage_aggregation_failed` identifies missing data or a failed `coverage combine` with
    the run ID, fragment count, exit code, and duration. Collection outcomes use
    `coverage_no_data` or `coverage_combine`.
  - `coverage_report_failed` identifies report or artifact failures without copying report
    output into the log. Its reason distinguishes `coverage_configuration`, `coverage_command`,
    `coverage_report`, and `coverage_artifact` failures.
  - Existing `test_file_failed` and `test_file_timed_out` events identify the affected file,
    exit code, and duration.
- **WARNING**:
  - `parallel_test_validation_failed` records the validation phase, stable error code, worker
    count, and whether a target was supplied. User-facing corrective text remains on stderr or
    in the result object rather than being duplicated in telemetry.
  - `worker_timeout` records the run ID, repository-relative file, configured timeout, measured
    duration, and kill exit code.
  - `coverage_threshold_failed` records the configured aggregate threshold, exit code, and
    duration when the threshold-bearing report rejects the combined result.
- **NOTICE**: Existing `slowest_test_file` events remain the performance signal for the top five
  slowest files.
- **INFO**:
  - `parallel_test_run_started` and `parallel_test_run_completed` provide correlated lifecycle
    events with worker, target-selection, aggregate target-count, coverage, outcome, and timing
    fields. Rejected pre-dispatch runs also emit completion with zero scheduled units,
    `outcome=failed`, and scalar failure phase/code fields. Raw pytest targets, node IDs, and
    parameter values are never logged.
  - `test_discovery_started` / `test_discovery_completed` and
    `test_worker_pool_started` / `test_worker_pool_completed` show where a run stopped or how
    long scheduling took.
  - `test_file_completed` records each file outcome and progress.
  - `coverage_collection_prepared`, `coverage_aggregation_started` / `completed`, and
    `coverage_report_started` / `completed` expose aggregate coverage lifecycle and counts.
- **DEBUG**: `test_file_started` records per-file dispatch context for troubleshooting without
  adding another default-level event for every file. Process-group cleanup events include the
  parent run ID and scalar error types so timeout diagnostics remain correlated and redacted.

### Log Structure

- Structured logs: Yes — stable event names followed by scalar `key=value` fields.
- Correlation: Yes — each run receives a short non-secret `run_id` shared by its parent lifecycle,
  discovery, pool, worker, timeout, and coverage events.
- Log levels: INFO, WARNING, ERROR, NOTICE, and DEBUG.
- Privacy: pytest argv, captured stdout/stderr, coverage report bodies, credentials, and
  environment contents are never copied into structured events. File and report paths remain
  limited to the existing operator-facing runner metadata, and startup telemetry contains only
  normalized selection state and aggregate counts.

## Metrics Implementation

### Performance Metrics

- **Per-file duration**: `RunResult.duration_seconds`, plus `test_file_completed` and timeout
  events.
- **Wall-clock duration**: `RunSummary.total_wall_clock_seconds` and the completion event.
- **Cumulative duration and speedup**: `RunSummary.cumulative_duration_seconds` and the
  `speedup` completion field.
- **Slow-file ranking**: `RunSummary.slowest_files` and existing NOTICE events.

### Outcome Metrics

- **Run outcome**: `parallel_test_run_completed` reports `outcome=passed|failed`.
- **File outcomes**: completion logs and `RunSummary` count passed, failed, timed-out, and
  skipped files.
- **Validation outcome**: `parallel_test_validation_failed` reports the stable error code and
  phase before any worker is scheduled; the terminal lifecycle event is emitted for the same
  rejection.
- **Coverage outcome**: aggregate lifecycle events report fragment count, report count,
  threshold, status, duration, and a distinct failure category. Threshold telemetry is emitted
  only when coverage output explicitly reports a threshold shortfall; all coverage failures still
  contribute to the final failed count.

### Monitoring Integration

- [ ] Prometheus metrics — not justified for a short-lived CLI process.
- [ ] Grafana dashboards — no long-lived runner endpoint exists.
- [x] CI alerting — non-zero Make/runner exit codes remain the actionable gate.
- [x] Log aggregation — key/value stderr events can be collected by CI logs without parsing
  test output.

## Make and CI Diagnostics

No additional Make or CI logging was added. The accepted Step 4 changes already provide the
necessary diagnostics: Make reports a missing runner and exits non-zero, while the CI coverage
summary reads the project-owned threshold. Duplicating shell output in Python logs would add noise
without improving diagnosis. Coverage setup removes stale root `.coverage.*` fragments and the
aggregate path cleans any fragments emitted during the run, keeping focused Make validation
artifacts scoped to the disposable coverage directory.

## Validation Results

- [x] Lifecycle events carry one run ID from start through completion.
- [x] Validation tests assert phase and stable error code without logging the full error text.
- [x] Timeout tests assert timeout, duration, kill exit code, and run ID fields.
- [x] Coverage tests assert preparation, aggregation, report, threshold, configuration, and
  command-failure outcomes.
- [x] Logs contain scalar context only; raw target/node-id values and captured subprocess output
  remain outside structured events.
- [x] Pre-dispatch validation/discovery rejection emits a correlated terminal completion event,
  and timeout process-group cleanup carries the same run ID.
- [x] Coverage setup and completion clean root fragment artifacts left by validation runs.
- [x] Focused Make tests, lint, typecheck, and AI-task verification passed.

## Notes

The existing human-readable progress and failure sections remain unchanged. Structured events are
diagnostic supplements, not a replacement for pytest output or the optional JSON report.
