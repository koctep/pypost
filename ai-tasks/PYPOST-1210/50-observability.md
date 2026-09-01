# PYPOST-1210: Observability Implementation

## Scope and Context

PYPOST-1210 is a dependency pin evaluation and technical decision task investigating Candidate 1 (`PySide6`/`shiboken6` pin mitigation) for the intermittent Qt teardown GC crash identified in PYPOST-1040. Because this evaluation established that no upstream release patch exists for the `QWidgetItem` GC teardown defect in PySide6 6.11.x and that the `PySide6==6.11.1` lock should be maintained while transferring settlement ownership to Candidate 2 (PYPOST-1211), no new production runtime logging or telemetry code was added to `pypost/`.

Observability for this task centers on:
1. Structured diagnostic logging within test harnesses (`tests/test_agent_dialog_settle_teardown_stress.py` and `tests/test_agent_dialog_settle_e2e.py`).
2. Statistical detector metrics, baseline crash rate monitoring (~32.5%), and CI test execution telemetry.

---

## Logging Implementation

### Added / Analyzed Logs

Overview of logging contracts across diagnostic harnesses and evaluated paths:
- **EMERG**: None — Evaluation task; no emergency production alerts added.
- **ALERT**: None — No immediate action alerts added.
- **CRIT**: None — No critical error logs added.
- **ERR**: None — Production error logging paths unchanged.
- **WARNING**: `tests/test_agent_dialog_settle_teardown_stress.py` (`_LOGGER.warning(summary)`) — Diagnostic logging of child process crashes/failures (exit code, termination signal decoding e.g. SIGSEGV/SIGBUS, stdout/stderr tails). Because the test is marked `@pytest.mark.xfail(strict=False)`, pytest suppresses dynamic assertion tracebacks in standard terminal output; WARNING-level logging surfaces the failure details through `log_cli` without requiring special flags.
- **NOTICE**: None — No notice-level logs in evaluation scope.
- **INFO**: None — Production runtime informational logs unchanged.
- **DEBUG**: `pypost.agent.ui_wait` — Structured debug contract logging (`ui_wait_timeout ... condition=... step=... active_modal_type=... dialog_title=... dialog_object_name=...`) verified in `tests/test_agent_dialog_settle_e2e.py` via `caplog`.

### Log Structure

Log format used:
- Structured logs: yes (key-value format in `pypost.agent.ui_wait` and formatted diagnostic summaries in `test_agent_dialog_settle_teardown_stress.py`)
- Includes context: yes (step name, condition name, modal widget type/name, child exit code, signal name, stdout/stderr tails)
- Log levels: `WARNING`, `DEBUG`

---

## Metrics Implementation (if applicable)

### Performance Metrics

Added / monitored performance metrics:
- **Response time / Execution duration**:
  - Functional suite (`tests/test_agent_dialog_settle_e2e.py`): ~0.76s–0.88s execution duration (2 passed).
  - Stress detector suite (`tests/test_agent_dialog_settle_teardown_stress.py`): ~49s–53s total execution duration across 25 child processes (~2.0s per child iteration).
  - Timeout enforcement: `pytest.mark.timeout(60)` for e2e functional suite; `pytest.mark.timeout(150)` for stress detector; `CHILD_TIMEOUT_S = 30.0` for per-child subprocess isolation.
- **Throughput / Detector Power**:
  - Sample size: $N = 25$ independent child subprocesses per stress evaluation run.
  - Detection power: $P(\ge 1\text{ crash}) = 1 - (1 - 0.325)^{25} \approx 99.993\%$ statistical confidence against baseline crash rate.
- **Error rate / Crash rate**:
  - Baseline crash rate: ~32.5% (13/40 single-run crash rate on Linux / Python 3.13.5 / PySide6 6.11.1).
  - Candidate 1 evaluation target: 0/25 crashes ($0.0\%$ failure rate under stress).
  - Candidate 1 evaluation observed: Crash rate persisted at baseline (~32.5%), confirming lack of upstream patch resolution and directing settlement ownership transition to Candidate 2.

### Business Metrics

Task-level progress and outcome metrics:
- **Evaluation Decision**: Maintain `PySide6==6.11.1` lock (no viable upstream patch; sandbox offline constraint).
- **Settlement Ownership**: Transferred to Candidate 2 (MITIGATE-3 / PYPOST-1211: explicit widget cycle breaking / disconnect in `SettingsDialog`).
- **Regression Preservation**: 100% functional test pass rate preserved (2/2 green on `test_agent_dialog_settle_e2e.py`).

### System Health Metrics

System health and test runner metrics:
- **Resource usage**: Subprocess memory and process cleanup isolated per iteration; child processes execute `pytest` in isolated subprocesses with `QT_QPA_PLATFORM=offscreen` to prevent display server resource leaks.
- **Component status**:
  - `AgentAppSession` and `SettingsDialog` lifecycle: Clean functional teardown.
  - CPython cyclic GC (`gc.collect()` in pytest `unraisableexception` plugin): Monitored via stress detector harness.

---

## Monitoring Integration

Integration with monitoring and CI systems:
- [x] Pytest terminal reporter and `log_cli` capturing structured diagnostic logs
- [x] JUnit XML / CI test telemetry tracking execution times and xfail/pass statuses
- [ ] Prometheus metrics (not applicable for client-side Qt desktop application test suite)
- [ ] Grafana dashboards (not applicable)
- [ ] Alerting rules (CI build failure on unexpected regressions)
- [ ] Log aggregation (standard CI build artifacts and pytest log files)

---

## Validation Results

Validation results:
- [x] Logs are correctly formatted (verified structured DEBUG logs in `pypost.agent.ui_wait` and WARNING summary in stress detector)
- [x] Metrics are collected correctly (statistical detection power and crash rate calculations verified)
- [x] Logging works in error scenarios (verified `_LOGGER.warning(summary)` on non-zero child process exits)
- [x] Large data structures are not logged (stdout/stderr tails truncated to relevant diagnostic slices: 2000 chars stdout, 1000 chars stderr)
- [x] Metrics are available for monitoring (CI execution logs, timeout enforcement, test duration telemetry)

---

## Notes

- **Task Type**: PYPOST-1210 is a dependency pin evaluation task, hence no production logging changes were made in `pypost/`.
- **Diagnostic Logging Value**: The `_LOGGER.warning` mechanism in `tests/test_agent_dialog_settle_teardown_stress.py` ensures that crash signals (such as SIGSEGV / SIGBUS) occurring during Qt GC teardown are captured and rendered in CI test logs even when pytest marks the test as `XFAIL`.
- **Settlement Transfer**: Observability verification for the subsequent application-level fix will be tracked under PYPOST-1211 (Candidate 2).
