# PYPOST-1192: Observability Implementation

## Logging Implementation

### Added Logs

Timeout observability was added in Step 4 on the parallel orchestrator
(`scripts/run_parallel_tests.py`). No further log-site changes were required in
Step 6; this document records the production signals and validation.

- **EMERG**: N/A — not used by this CLI orchestrator.
- **ALERT**: N/A — not used by this CLI orchestrator.
- **CRIT**: N/A — not used by this CLI orchestrator.
- **ERR**: `run_parallel_tests()` — `logger.error("test_file_timed_out file=%s exit_code=%d duration_seconds=%.2f", ...)` for each `TestStatus.TIMED_OUT` result in the FAILURES section (distinct from `test_file_failed` for ordinary pytest failures). Full stdout/stderr remain on CLI stdout only.
- **WARNING**: `SubprocessTestExecutor.run_test_file()` — on `subprocess.TimeoutExpired`, immediate structured signal:
  `logger.warning("worker_timeout file=%s timeout_seconds=%s", rel_file, worker_timeout)`.
  This is the primary operator-visible timeout event required by the story.
- **NOTICE**: Unchanged from PYPOST-1149 (`slowest_test_file`); timed-out files may appear in the slowest ranking by duration.
- **INFO**: Unchanged completion path still fires for timed-out workers:
  `logger.info("test_file_completed file=%s status=%s ...", ..., "timed_out", ...)`.
  Run start/end and JSON-report logs unchanged (no `worker_timeout` field on
  `parallel_test_run_started`; configured bound is visible on timeout WARNING).
- **DEBUG**: N/A — not used by this CLI orchestrator.

### CLI Output (not logging)

Progress line prints `TIMED_OUT` (uppercased `TestStatus` value) instead of
`PASSED`/`FAILED`/`SKIPPED`. FAILURES section includes timed-out files and
appends a short stderr note `worker timed out after Ns` (not duplicated into
structured logger payloads beyond the dedicated timeout events).

### Log Structure

Log format used:
- Structured logs: Yes (`key=value` fields; event name as first token)
- Includes context: Yes (`file`, `timeout_seconds` on WARNING; `file`,
  `exit_code`, `duration_seconds` on ERROR; `status=timed_out` on INFO completion)
- Log levels: WARNING (primary timeout), ERROR (summary FAILURES path), INFO
  (per-file completion with `timed_out`)

Example WARNING line (stderr via `%(levelname)s %(message)s`):

```text
WARNING worker_timeout file=tests/test_hang.py timeout_seconds=1.0
```

## Metrics Implementation (if applicable)

### Performance Metrics

No new Prometheus-style metrics. Existing RunSummary timings still apply:

- **Per-file duration**: `TestResult.duration_seconds` measured until
  `TimeoutExpired` (wall time ≥ configured bound)
- **Wall-clock / cumulative / speedup**: unchanged aggregate fields; timed-out
  files contribute their measured duration to cumulative totals

### Business Metrics

- **Timed-out outcome**: `TestStatus.TIMED_OUT` / JSON `status: "timed_out"`;
  increments `failed_files` and forces `is_success` false
- **Timeout bound**: `RunnerConfig.worker_timeout` (CLI `--worker-timeout` /
  env `WORKER_TIMEOUT` / default 30); emitted on the WARNING log as
  `timeout_seconds`

### System Health Metrics

- **Worker kill sentinel**: `exit_code=-9` on timed-out `TestResult` (kill-on-
  timeout path)
- No new resource gauges (CPU/memory) for this story

## Monitoring Integration

Integration with monitoring systems:
- [x] Structured stderr logs (`worker_timeout`, `test_file_timed_out`,
  `test_file_completed` with `status=timed_out`) for CI log scrapers
- [x] Machine-readable JSON summary (`--report-json`) includes
  `status: "timed_out"` per file
- [x] CLI FAILURES / progress distinguish timeout from ordinary failure
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

## Validation Results

Validation results:
- [x] Logs are correctly formatted (`worker_timeout file=… timeout_seconds=…`)
- [x] Metrics / status collected correctly (`TIMED_OUT` counts as failure;
  JSON/status field is `timed_out`)
- [x] Logging works in error scenarios — covered by
  `tests/test_run_parallel_tests.py::test_hung_worker_under_timeout_yields_timed_out`
  (`caplog` asserts `worker_timeout` and `timeout_seconds=` at WARNING)
- [x] Large data structures are not logged — WARNING/ERROR carry path and
  scalars only; stdout/stderr stay on CLI / JSON artifact
- [x] Signals available for operators (stderr WARNING + ERROR, progress
  `TIMED_OUT`, JSON status)

## Notes

- Architecture allowed either a dedicated timeout log **or** completion with
  `status=timed_out`. Implementation emits **both**: immediate WARNING
  `worker_timeout` at kill time, then INFO `test_file_completed` with
  `status=timed_out`, plus ERROR `test_file_timed_out` in the FAILURES pass.
- `parallel_test_run_started` does not yet include `worker_timeout=…`;
  operators infer the bound from config docs or from timeout WARNING fields.
  Optional enrichment only — not required for DoD.
- Logging setup remains `_configure_logging()` in `main()` (`INFO`, stderr);
  unit tests capture records via `caplog` without that call.
