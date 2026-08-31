# PYPOST-1197: Observability Implementation

## Logging Implementation

### Added Logs

The parallel test runner orchestrator (`scripts/run_parallel_tests.py`) implements multi-tiered structured logging and diagnostic output covering worker execution, timeout events, process group termination, and run summaries:

- **EMERG**: None (not applicable for test runner CLI orchestrator).
- **ALERT**: None (not applicable for test runner CLI orchestrator).
- **CRIT**: None (not applicable for test runner CLI orchestrator).
- **ERR**:
  - `scripts/run_parallel_tests.py:run_parallel_tests`: `logger.error("test_file_timed_out file=%s exit_code=%d duration_seconds=%.2f", r.test_file, r.exit_code, r.duration_seconds)` — logged during failure reporting for test files that exceeded the worker timeout.
  - `scripts/run_parallel_tests.py:run_parallel_tests`: `logger.error("test_file_failed file=%s exit_code=%d duration_seconds=%.2f", r.test_file, r.exit_code, r.duration_seconds)` — logged during failure reporting for test files that failed with non-zero exit codes.
- **WARNING**:
  - `scripts/run_parallel_tests.py:SubprocessTestExecutor.run_test_file`: `logger.warning("worker_timeout file=%s timeout_seconds=%s", rel_file, self.config.worker_timeout)` — emitted immediately when a worker process exceeds `worker_timeout`, prior to process group cleanup.
  - `scripts/run_parallel_tests.py:run_parallel_tests`: `logger.warning("coverage_threshold_failed coverage=%.2f fail_under=%d", total_cov, fail_under)` — emitted when coverage falls below the required threshold.
  - `scripts/run_parallel_tests.py:run_parallel_tests`: `logger.warning("no_test_files_discovered test_targets=%s", test_targets)` — emitted when target patterns match no files.
- **NOTICE**:
  - `scripts/run_parallel_tests.py:run_parallel_tests`: `logger.log(NOTICE, "slowest_test_file rank=%d file=%s duration_seconds=%.2f", rank, file_path, duration)` — logged for the top slowest test files.
- **INFO**:
  - `scripts/run_parallel_tests.py:run_parallel_tests`: `logger.info("parallel_test_run_started workers=%d enable_coverage=%s report_json=%s test_targets=%s pytest_arg_count=%d worker_timeout=%s", ...)` — emitted at run launch.
  - `scripts/run_parallel_tests.py:run_parallel_tests`: `logger.info("test_file_completed file=%s status=%s exit_code=%d duration_seconds=%.2f progress=%d/%d", ...)` — emitted as each worker completes.
  - `scripts/run_parallel_tests.py:run_parallel_tests`: `logger.info("parallel_test_run_completed total_files=%d passed=%d failed=%d skipped=%d wall_clock_seconds=%.2f cumulative_duration_seconds=%.2f", ...)` — emitted at completion.
- **DEBUG**:
  - `scripts/run_parallel_tests.py:kill_process_group`: `logger.debug("kill_process_group sending SIGKILL to pgid=%s for pid=%s", pgid, pid)` — emitted when initiating process group teardown on POSIX.
  - `scripts/run_parallel_tests.py:kill_process_group`: `logger.debug("kill_process_group getpgid failed for pid=%s: %s; falling back to pgid=pid", pid, exc)` — emitted if `os.getpgid` raises `ProcessLookupError` or `OSError`.
  - `scripts/run_parallel_tests.py:kill_process_group`: `logger.debug("kill_process_group killpg failed for pgid=%s: %s", pgid, exc)` — emitted if `os.killpg` encounters transient errors (suppressed to prevent orchestrator crash).
  - `scripts/run_parallel_tests.py:kill_process_group`: `logger.debug("kill_process_group win32 failed for pid=%s: %s", pid, exc)` — emitted on Windows if `os.kill` encounters transient errors.

### Log Structure

Log format used:
- Structured logs: yes (key=value formatting consistently applied across all events: `file=%s`, `timeout_seconds=%s`, `status=%s`, `exit_code=%d`, `duration_seconds=%.2f`, `pgid=%s`, `pid=%s`).
- Includes context: yes (relative test file paths, configured timeout duration, process group IDs, exit codes, execution wall clock and cumulative durations).
- Log levels: `DEBUG`, `INFO`, `NOTICE` (level 25), `WARNING`, `ERROR`.

## Diagnostic Output & Stderr Enrichment

When a worker times out:
1. **Stderr enrichment**:
   - `stderr_str = f"{stderr_str}\n{timeout_note}".strip()` where `timeout_note = f"worker timed out after {self.config.worker_timeout}s"`.
   - Ensures that console test failure reporting displays the explicit timeout reason alongside any partial worker stderr.
2. **Status & Exit code**:
   - `TestStatus.TIMED_OUT` (value `"timed_out"`).
   - Exit code `-9` (corresponding to `SIGKILL`).
   - Propagated to `TestResult` and captured in `--report-json` artifact under the file's result object.
3. **Transient error suppression**:
   - In `kill_process_group(pid)`, `ProcessLookupError`, `PermissionError`, and `OSError` are safely caught and logged at `DEBUG` level so an already-reaped process or race condition never crashes the orchestrator or emits an unhandled traceback.

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time**: Wall clock execution time (`total_wall_clock_seconds`) and cumulative worker execution time (`cumulative_duration_seconds`) tracked in `RunSummary` and written to JSON report.
- **Throughput**: Worker completion progress (`progress=%d/%d`) logged per file in `SubprocessTestExecutor` / orchestrator.
- **Error rate**: Counts of `passed_files`, `failed_files`, and `skipped_files` recorded in `RunSummary` and aggregated at run conclusion.

### Business Metrics

Business metrics:
- **Test suite pass rate**: Binary suite success status (`summary.is_success`, evaluated as `failed_files == 0`), where timed-out workers are counted toward `failed_files`.

### System Health Metrics

System health metrics:
- **Resource usage**: Configured worker parallelism count (`workers`), process session isolation (`start_new_session=True`), and full process group teardown prevent leaked zombie/orphan processes from degrading host memory and CPU.
- **Component status**: Worker exit code (`-9` on timeout) and per-worker status (`TestStatus.TIMED_OUT`, `TestStatus.FAILED`, `TestStatus.PASSED`, `TestStatus.SKIPPED`).

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics (not applicable for CLI runner tool)
- [ ] Grafana dashboards (not applicable for CLI runner tool)
- [x] Alerting rules / CI gating (exit code 1 on failed or timed-out tests, non-zero returncode in CI pipeline)
- [x] Log aggregation (JSON report output via `--report-json` compatible with CI test result collectors)

## Validation Results

Validation results:
- [x] Logs are correctly formatted: Structured `key=value` syntax adhering to existing runner conventions.
- [x] Metrics are collected correctly: `total_files`, `passed_files`, `failed_files`, `duration_seconds` in `RunSummary` and JSON report.
- [x] Logging works in error scenarios: Verified via unit and integration tests (`test_hung_worker_under_timeout_yields_timed_out`, `test_kill_process_group_posix_suppresses_exceptions`).
- [x] Large data structures are not logged: Only scalar IDs, timings, counts, and file paths are logged.
- [x] Metrics are available for monitoring: Serialized via `--report-json` and console stdout/stderr.

## Notes

- The orchestrator configures `stream=sys.stderr` in `logging.basicConfig` to ensure logging does not pollute stdout when stdout is redirected.
- POSIX process group signaling uses `os.killpg(pgid, signal.SIGKILL)` following `start_new_session=True` on `subprocess.Popen`, preventing orphaned grandchildren. All error scenarios (such as reaped PIDs) log at DEBUG level and do not throw.
