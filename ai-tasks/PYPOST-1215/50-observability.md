# PYPOST-1215: Observability Implementation

Empirical test execution observability, duration metrics, timeout hierarchy parameters, and
structured logging emissions across isolated and parallel execution profiles for
`test_live_collection_tree_missing_option_raises` in `tests/test_ui_actions.py`.

## Logging Implementation

### Test Runner & Framework Logging

The test execution pipeline leverages syslog-compatible, structured logging across orchestrator,
worker subprocess, and UI action primitive layers:

- **EMERG**: None (no catastrophic runtime panics).
- **ALERT**: None.
- **CRIT**: None.
- **ERR / ERROR**:
  - `scripts/run_parallel_tests.py`: Emitted when a worker subprocess exceeds `WORKER_TIMEOUT`:
    `test_file_timed_out file=%s timeout_seconds=%.1f`
  - Subprocess non-zero exit logging upon unhandled test failures:
    `test_file_completed file=%s status=failed exit_code=%d duration_seconds=%.2f`
- **WARNING**: None emitted during nominal runs.
- **NOTICE** (custom level 25 in runner):
  - `scripts/run_parallel_tests.py`: Emitted for ranked slow test identification:
    `slowest_test_file rank=%d file=%s duration_seconds=%.2f`
- **INFO**:
  - `scripts/run_parallel_tests.py`: Parallel run lifecycle tracking:
    - `parallel_test_run_started workers=%d enable_coverage=%s report_json=%s ...`
    - `test_file_completed file=%s status=%s exit_code=%d duration_seconds=%.2f progress=%d/%d`
    - `parallel_test_run_completed total_files=%d passed=%d failed=%d wall_clock_seconds=%.2f ...`
- **DEBUG**:
  - `pypost.agent.ui_actions`: Emitted per interaction primitive execution:
    `ui_action_applied primitive=%s widget_id=%s outcome=ok duration_ms=%s`
  - In negative assertions (such as `test_live_collection_tree_missing_option_raises`),
    `UiTargetNotInteractableError` is raised with descriptive message (`option not found: ...`)
    without emitting noisy debug dumps.

### Log Structure

Log format and sanitization standards:
- **Structured logs**: Yes (`event_name key1=value1 key2=value2` key-value pairs).
- **Includes context**: Yes (file path, exit code, worker rank, duration, widget identifier).
- **Log levels**: INFO (orchestrator lifecycle), NOTICE (slow test ranking), ERROR (timeouts),
  DEBUG (action primitives).
- **Redaction & Safety**: Zero sensitive payloads or full Qt widget hierarchy dumps logged.

## Metrics Implementation

### Test Execution Duration & Concurrency Metrics

Empirical duration metrics captured across differential execution profiles:

- **Isolated Single Node** (`test_live_collection_tree_missing_option_raises`):
  - Execution Time: 1.28s – 1.43s (mean: 1.35s)
  - Concurrency Contention: None (single active worker process)
  - Reliability: 100% pass rate across repeated iterations
- **Isolated Single File** (`tests/test_ui_actions.py` - 14 test nodes):
  - Execution Time: 5.69s – 5.90s (mean: 5.80s)
  - Wall-clock Duration: ~5.8s
  - Reliability: 100% pass rate
- **Concurrent Integration Subset** (5 UI / Agent / MCP test suites):
  - Target File Duration: 6.09s (+5.0% timing overhead)
  - Wall-clock Duration: 14.51s across 8 workers
- **Full Parallel Suite** (300 test files repo-wide):
  - Target File Duration: 8.14s (+40.3% timing inflation due to CPU/Qt contention)
  - Total Wall-clock Duration: 171.39s
  - Aggregate Cumulative CPU Time: ~680s (effective speedup: ~4.0x)

### Timeout Hierarchy & Parameters

Observability for execution deadlines is governed by a multi-tiered timeout configuration:

1. **Test-Level Pytest Timeout**:
   - Parameter: `@pytest.mark.timeout(60)` via `pytestmark` in `tests/test_ui_actions.py`.
   - Purpose: Enforces an upper ceiling of 60 seconds per individual test node.
2. **Worker Process Subprocess Timeout**:
   - Parameter: `WORKER_TIMEOUT = 120` seconds (configured via Makefile `make test`).
   - Purpose: Prevents hanging worker processes if Qt event loop locks or deadlocks occur.
3. **UI Session Readiness Polling**:
   - Parameter: Polling interval and timeout on `session.window.is_ui_ready`.
   - Purpose: Ensures offscreen Qt window initialization completes prior to interaction.

## Monitoring Integration

- [x] **Structured CLI Logging**: Real-time progress and duration telemetry during `make test`.
- [x] **JSON Report Export**: Support for machine-readable JSON metrics via `REPORT_JSON=<path>`.
- [x] **Slow File Identification**: Automatic NOTICE logs and tabular summary for top slowest files.
- [x] **Log Aggregation Compatibility**: Key-value formatted strings compatible with ELK/Loki.
- [x] **Quality Gate Observability**: Full validation via `make check`, `make lint`, and `make test`.

## Validation Results

- [x] Logs are correctly formatted with key-value pairs and syslog-compatible log levels.
- [x] Execution duration metrics captured and benchmarked across all four profiles.
- [x] Timeout hierarchy parameters verified and documented across test and worker layers.
- [x] Large data structures and secret values are excluded from log emissions.
- [x] Quality gates pass cleanly (`make lint` and `make verify-ai-tasks`).

## Notes

- **Handoff Diagnostic Context**: The +40.3% duration inflation observed during full parallel
  runs provides quantitative baseline telemetry for downstream root-cause analysis in
  [PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216) (DIAG-1).
- **Roadmap In-Progress Marking**: Step 6 is marked `[/]` in `00-roadmap.md` per `td-roadmap`
  rules, awaiting orchestrator acceptance review.
