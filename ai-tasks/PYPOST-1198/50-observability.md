# PYPOST-1198: Observability Implementation

## Logging Implementation

### Added Logs

This task adds a single field to an existing log line; no new log statements were introduced.

- **INFO**: `scripts/run_parallel_tests.py`, `run_parallel_tests()` — the `parallel_test_run_started`
  log line now includes `worker_timeout=%s` (value: `config.worker_timeout`) alongside the
  pre-existing `workers`, `enable_coverage`, `report_json`, `test_targets`, and `pytest_arg_count`
  fields. This exposes the effective worker timeout (from CLI override or config default) at the
  start of every parallel test run, so operators can confirm which timeout was actually in effect
  without cross-referencing CLI args or config files.

No other log levels (EMERG/ALERT/CRIT/ERR/WARNING/NOTICE/DEBUG) were touched by this change.

Explicitly out of scope / unchanged:
- The existing **WARNING**-level `worker_timeout file=%s timeout_seconds=%s` log
  (`Worker._run_one` / worker-timeout handling path, around line 368-372 of
  `scripts/run_parallel_tests.py`) was **not modified**. It already logs the timeout value at the
  point a worker actually times out; adding `worker_timeout` to the run-start INFO log is
  complementary (visible up front) rather than a replacement or duplicate of that WARNING.

### Log Structure

Log format used:
- Structured logs: yes — `key=value` token style, consistent with the rest of
  `scripts/run_parallel_tests.py`'s logging (e.g. `parallel_test_run_started ...`,
  `worker_timeout file=... timeout_seconds=...`, `no_test_files_discovered test_targets=...`).
- Includes context: yes — the run-start line now carries the full effective run configuration
  (workers, coverage flag, report path, test targets, pytest arg count, worker timeout) in one
  line, using printf-style `%s`/`%d` args (lazy formatting, standard `logging` module usage).
- Log levels used (by this change): INFO only. No new levels introduced.

## Metrics Implementation (if applicable)

Not applicable to this task. This is a single-field enrichment of an existing INFO log line; no
new metrics (performance, business, or system health) were added, and none are needed for this
change's scope. Timeout-related duration/count metrics, if ever desired, would be a separate,
larger piece of work (e.g. counting/timing actual worker timeouts) and are not part of this
Debt ticket.

## Monitoring Integration

- [ ] Prometheus metrics — not applicable, no metrics added
- [ ] Grafana dashboards — not applicable
- [ ] Alerting rules — not applicable
- [ ] Log aggregation (ELK, Loki, etc.) — no change needed; the enriched log line uses the same
  logger/format already consumed by any existing log aggregation, so no new integration is
  required

## Validation Results

- [x] Logs are correctly formatted — verified by
  `tests/test_run_parallel_tests.py::test_parallel_runner_logs_run_config`, which asserts
  `worker_timeout=30.0` appears in the `parallel_test_run_started` message
- [x] Metrics are collected correctly — N/A, no metrics added
- [x] Logging works in error scenarios — N/A to this change; the run-start INFO log fires on every
  run regardless of later worker outcomes, and the pre-existing WARNING-level timeout log (unchanged)
  continues to cover the actual timeout error scenario
- [x] Large data structures are not logged — only a float (`config.worker_timeout`) was added; no
  collections or nested structures are logged
- [ ] Metrics are available for monitoring — N/A, no metrics added

## Notes

Per the task scope (Step 4 already implemented the code change), this step is documentation-only:
it records the `worker_timeout` field added to the `parallel_test_run_started` INFO log in
`scripts/run_parallel_tests.py::run_parallel_tests()`. No new metrics were added — this is
intentionally out of scope for a single-log-field enrichment. The existing WARNING-level
`worker_timeout` log (emitted when a worker actually times out) was left unchanged.
