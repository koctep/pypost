# PYPOST-1149: Observability Implementation

## Logging Implementation

### Added Logs

The parallel test orchestrator (`scripts/run_parallel_tests.py`) uses structured `logging` calls (stderr via `basicConfig`) alongside CLI `print()` output on stdout for pytest-style progress and failure tracebacks.

- **EMERG**: N/A — not used by this CLI orchestrator.
- **ALERT**: N/A — not used by this CLI orchestrator.
- **CRIT**: N/A — not used by this CLI orchestrator.
- **ERR**: `run_parallel_tests()` — `logger.error("test_file_failed file=%s exit_code=%d duration_seconds=%.2f", ...)` for each failed test file (context only; full stdout/stderr remain on CLI stdout).
- **WARNING**: `run_parallel_tests()` — `logger.warning("no_test_files_discovered test_targets=%s", ...)` when discovery finds zero files; `logger.warning("coverage_threshold_failed fail_under=%d", ...)` when combined coverage is below `--cov-fail-under`.
- **NOTICE**: `run_parallel_tests()` — `logger.log(NOTICE, "slowest_test_file rank=%d file=%s duration_seconds=%.2f", ...)` for each entry in the top-5 slowest ranking (custom syslog-compatible level 25).
- **INFO**: `run_parallel_tests()` — `logger.info("parallel_test_run_started workers=%d enable_coverage=%s report_json=%s test_targets=%s pytest_arg_count=%d", ...)` at run start; `logger.info("test_file_completed file=%s status=%s exit_code=%d duration_seconds=%.2f progress=%d/%d", ...)` per completed worker; `logger.info("coverage_report_completed fail_under=%d", ...)` after successful coverage combine; `logger.info("parallel_test_run_completed total_files=%d passed=%d failed=%d skipped=%d wall_clock_seconds=%.2f cumulative_duration_seconds=%.2f speedup=%.1f", ...)` at end; `logger.info("json_report_written path=%s", ...)` when `--report-json` is used.
- **DEBUG**: N/A — not used by this CLI orchestrator.

### CLI Output (not logging)

User-facing stdout `print()` calls are retained for pytest-style live progress (`[n/total] file ... PASSED`), grouped failure headers with full stdout/stderr, coverage terminal output, slowest-files table, and the final summary block.

### Log Structure

Log format used:
- Structured logs: Yes (`key=value` fields in message strings)
- Includes context: Yes (workers, targets, coverage flag, JSON path, per-file status/exit code/duration, aggregate counts and timings)
- Log levels: INFO, NOTICE (custom level 25), WARNING, ERROR

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time / Wall-clock duration**: `RunSummary.total_wall_clock_seconds` measured via `time.perf_counter()` — `scripts/run_parallel_tests.py`
- **Cumulative CPU execution time**: `RunSummary.cumulative_duration_seconds` (sum of individual subprocess durations)
- **Parallel speedup factor**: Ratio of cumulative CPU time to wall-clock time (`cumulative_duration / wall_clock`)
- **Per-file test duration**: `TestResult.duration_seconds` captured for each executed test suite file

### Business Metrics

Business metrics:
- **Test execution counts**: Total, passed, failed, and skipped file counts (`RunSummary`)
- **Parallel worker concurrency**: `RunSummary.worker_count` / `RunnerConfig.workers`

### System Health Metrics

System health metrics:
- **Worker status**: Exit codes per worker subprocess (`TestResult.exit_code`)
- **Coverage health**: Aggregate line coverage via `CoverageManager.combine_and_report()`

## Monitoring Integration

Integration with monitoring systems:
- [x] Machine-readable JSON summary artifact (`--report-json`) for CI/CD observability and dashboard ingestion
- [x] Grouped failure output for automated build log aggregators (CLI stdout)
- [x] Coverage aggregation output (`.coverage` and `htmlcov/`) compatible with code quality platforms
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

## Validation Results

Validation results:
- [x] Logs are correctly formatted (structured `logger.*` calls with `key=value` context)
- [x] Metrics are collected correctly (wall-clock, cumulative durations, speedup factor, pass/fail counts)
- [x] Logging works in error scenarios (`logger.error` for failures; `logger.warning` for coverage threshold breach)
- [ ] Large data structures are not logged — **partial**: structured logs omit per-file stdout/stderr, but the JSON report (`JsonReporter.to_dict`) still embeds full `stdout`/`stderr` per result in the artifact file (by design for CI debugging); coverage combine output is printed to CLI stdout only, not duplicated into logs
- [x] Metrics are available for monitoring (via CLI output, stderr logs, and structured JSON schema)

## Notes

The JSON report (`JsonReporter.write_report`) produces a schema containing:
1. `summary`: aggregate metrics (counts, durations, worker count, overall status)
2. `slowest_files`: ranked array of top slowest files and durations
3. `results`: detailed per-file results including exit code, duration, stdout, and stderr (artifact only — not emitted via `logger.*`)

Logging is configured in `main()` via `_configure_logging()` (`level=INFO`, `stream=sys.stderr`). Direct calls to `run_parallel_tests()` from tests still emit log records captured by pytest `caplog`.
