# PYPOST-1262: Observability Implementation

## Logging Implementation

### Added Logs

Observability in the test execution architecture is primarily driven by the parallel test
runner (`scripts/run_parallel_tests.py`) and test fixture orchestration in
`tests/makefile_test_helpers.py`. While no new runtime application loggers were required
for this test architecture refactoring, existing structured logs and logging points were
analyzed and validated against syslog-compatible log levels:

- **EMERG**: None (N/A) - No emergency system halts used in test orchestration.
- **ALERT**: None (N/A) - No immediate operational interventions required.
- **CRIT**: None (N/A) - No critical infrastructure failures defined in test runner.
- **ERR**: `scripts/run_parallel_tests.py` - emitted via `logger.error`:
  - `test_file_timed_out run_id=%s file=%s exit_code=%d duration_seconds=%.2f`:
    emitted when a worker subprocess exceeds the configured worker timeout (e.g. 120s limit).
  - `test_file_failed run_id=%s file=%s exit_code=%d duration_seconds=%.2f`:
    emitted when a test file fails with a non-zero exit code.
- **WARNING**: `scripts/run_parallel_tests.py` - emitted via `logger.warning`:
  - `parallel_test_validation_failed`: emitted on fail-closed CLI validation failure.
  - `coverage_threshold_failed`: emitted when coverage falls below configured `--cov-fail-under`.
  - `coverage_fragment_cleanup_failed`: emitted if unlinking coverage fragments fails.
- **NOTICE**: `scripts/run_parallel_tests.py` - emitted via `logger.log(NOTICE, ...)` (level 25):
  - `slowest_test_file rank=%d file=%s duration_seconds=%.2f`: emitted for the top 5 slowest
    test files, highlighting bottleneck candidates for optimization.
- **INFO**: `scripts/run_parallel_tests.py` - emitted via `logger.info`:
  - `test_file_completed run_id=%s file=%s status=%s exit_code=%d duration_seconds=%.2f`:
    emitted upon completion of each test worker with duration and progress metrics.
  - `test_worker_pool_completed run_id=%s completed_units=%d duration_seconds=%.2f`:
    emitted when all worker tasks complete.
  - `parallel_test_run_started` and `parallel_test_run_completed`: emitted at run start and finish.
- **DEBUG**: `scripts/run_parallel_tests.py` - emitted via `logger.debug`:
  - `test_file_started run_id=%s file=%s index=%d total=%d timeout_seconds=%s coverage_enabled=%s`:
    emitted when worker scheduling dispatches a file unit.

In `tests/makefile_test_helpers.py`, base virtual environment prewarming utilizes process-safe
file locking via `fcntl.flock` on a lockfile (`/tmp/pypost_shared_base_venv_<pyver>.lock`). To
avoid polluting pytest log streams during subprocess calls, cache initialization is silent,
while execution times and cache hit status are observable through test worker duration metrics.

### Log Structure

Log format used:
- Structured logs: yes (key=value attributes in message string)
- Includes context: yes (`run_id`, `file`, `status`, `exit_code`, `duration_seconds`, `progress`)
- Log levels: DEBUG, INFO, NOTICE (syslog 25), WARNING, ERROR (ERR)

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time**:
  - `duration_seconds` per test suite captured by `scripts/run_parallel_tests.py`.
  - Wall-clock runtime (`wall_clock_seconds`) and cumulative duration (`cumulative_duration`).
  - Strict duration budgets and module timeouts (`pytestmark = pytest.mark.timeout(...)`)
    enforced across decomposed test suites (<= 60s per file, reducing per-worker load from
    >120s to <15s).
  - Duration budget assertions verified in `tests/test_makefile_parallel_budget.py` and
    `tests/test_pypost_1262_failing_repro.py`.
- **Throughput**:
  - Parallel execution speedup factor (`speedup = cumulative_duration / wall_clock_seconds`).
  - Worker completion throughput tracked via `progress=%d/%d` in `test_file_completed`.
- **Error rate**:
  - Test failure and timeout rates (`failed_count`, `timed_out` count vs `total_files`).

### Business Metrics

Business metrics:
- **Quality Gate Success Rate**: Proportion of passed test files in CI (`RunSummary.passed_count`).
- **Test Integrity Preservation**: Verification of all 24 original Makefile lifecycle and target
  tests across modular files in `tests/test_pypost_1262_failing_repro.py`.

### System Health Metrics

System health metrics:
- **Resource usage**:
  - Worker process concurrency (`--workers` configuration in test runner).
  - Disk I/O and process contention reduced by prewarmed base venv (`_materialize_prewarmed_venv`)
    and atomic file locking (`fcntl.flock`).
- **Component status**:
  - Worker subprocess exit codes (`res.exit_code`).
  - Coverage aggregation health (`CoverageManager.combine()` status).

## Monitoring Integration

Integration with monitoring systems:
- [x] Machine-readable JSON summary artifact (`--report-json`) for CI telemetry
- [x] Structured progress and failure logging to `stderr`
- [x] Top 5 slowest test files notice reporting
- [x] Automated duration budget verification via `tests/test_makefile_parallel_budget.py`
- [ ] Prometheus metrics (N/A for offline build and test scripts)
- [ ] Grafana dashboards
- [ ] Alerting rules (CI build timeout alerts)
- [ ] Log aggregation (ELK, Loki, etc. ingesting CI stderr/stdout)

## Validation Results

Validation results:
- [x] Logs are correctly formatted (structured key=value format)
- [x] Metrics are collected correctly (durations, exit codes, worker progress)
- [x] Logging works in error scenarios (test timeouts and failure reporting)
- [x] Large data structures are not logged (full stdout/stderr excluded from structured logs)
- [x] Metrics are available for monitoring (via CLI output, stderr logs, and JSON reports)

## Notes

The decomposition of monolithic test files (`test_makefile_lifecycle.py` and
`test_makefile_targets.py`) into 7 focused suites (`test_makefile_markers.py`,
`test_makefile_stamp_test_idempotency.py`, `test_makefile_stamp_otel_idempotency.py`,
`test_makefile_install_stamp_contract.py`, `test_makefile_exit_behavior.py`,
`test_makefile_target_install_test.py`, `test_makefile_target_filtering.py`) directly improves
observability. Each decomposed test file now executes in 2-15 seconds rather than 120+ seconds,
allowing granular tracking of which specific targets or stamp behaviors fail or slow down.
Furthermore, the base venv caching via `fcntl.flock` in `tests/makefile_test_helpers.py` avoids
redundant pip install operations across parallel workers, stabilizing test execution duration
in high-concurrency CI environments.
