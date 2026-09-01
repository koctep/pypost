# PYPOST-1209: Observability Implementation

## Logging Implementation

### Added Logs

PYPOST-1209 is a contract and documentation task (MITIGATE-1 under epic [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115)), so no new production logging code was introduced in `pypost/`. However, observability across the dual proof surfaces defined in the evaluation contract is structured and verified as follows:

- **EMERG**: None (N/A — desktop application / evaluation contract).
- **ALERT**: None (N/A).
- **CRIT**: None (N/A).
- **ERR**: None added in production code.
- **WARNING**: 
  - `tests/test_agent_dialog_settle_teardown_stress.py:191`: `_LOGGER.warning(summary)` emits structured summaries of detected child process crashes (iteration count, exit signals, stdout/stderr tails) during teardown stress evaluation. This ensures failure telemetry is visible in CI logs and standard test output even when marked with `xfail(strict=False)`.
- **NOTICE**: None.
- **INFO**: Standard agent session lifecycle events (e.g. `AgentAppSession.shutdown()` logs `agent_session_shutdown_completed`).
- **DEBUG**:
  - `pypost.agent.ui_wait` (verified in `tests/test_agent_dialog_settle_e2e.py:92-97`): Emits structured diagnostic records (e.g. `ui_wait_timeout condition=forced_dialog_settle_timeout step=wait_dialog_after_settings_open dialog_title=... dialog_object_name=... active_modal_type=...`) whenever modal or dialog settlement conditions time out.

### Log Structure

Log format used:
- **Structured logs**: Yes (key-value scalar attributes, signal descriptions, bounded stdout/stderr output tails).
- **Includes context**: Yes (includes iteration index, return code / signal name, dialog step identifier, modal widget object names).
- **Log levels**: `WARNING`, `INFO`, `DEBUG`.

---

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance and execution time boundaries:
- **Child Execution Timeout**: `CHILD_TIMEOUT_S = 30.0s` per single-shot pytest subprocess in `tests/test_agent_dialog_settle_teardown_stress.py`.
- **Stress Suite Timeout**: `pytest.mark.timeout(150)` covering $N=25$ child runs plus generous buffer for OS cleanup.
- **E2E Suite Timeout**: `pytest.mark.timeout(60)` for functional dialog settlement proof.

### Business Metrics / Evaluation Quality Metrics

The evaluation contract defines quantitative statistical and stability metrics for mitigation candidates:

- **Baseline Crash Rate ($p_{\text{baseline}}$)**: **32.5%** ($13 / 40$ runs; 11× SIGSEGV/139, 2× SIGBUS/135 on Linux/Python 3.13.5/PySide6 6.11.1 offscreen).
- **Evaluation Sample Size ($N$)**: **25 independent child processes** per candidate trial on `tests/test_agent_dialog_settle_teardown_stress.py`.
- **Statistical Detection Power**: **>99.991%** ($1 - (1 - 0.325)^{25} \approx 0.999914$).
- **Success Target Threshold**: Exactly **0 crashes out of 25 runs** ($0/25$, 0.0% crash rate) on the stress detector.
- **Functional Regression Metric**: **0 broken assertions** on `tests/test_agent_dialog_settle_e2e.py`.

### System Health Metrics

System health and process boundary metrics:
- **Process Exit Signals**: Tracked via `_describe_returncode()` in `tests/test_agent_dialog_settle_teardown_stress.py` (distinguishes clean exit `0`, SIGSEGV `139`/`-11`, SIGBUS `135`/`-7`, and subprocess timeouts).
- **Subprocess Isolation**: Prevents parent test runner memory corruption or crash cascading by isolating each dialog settle execution in a separate OS process.

---

## Monitoring Integration

Integration with monitoring and CI systems:
- [x] Pytest / CI test reporting (JUnit XML test results and runner exit codes)
- [x] Structured logger integration (`_LOGGER.warning` in stress harness; `pypost.agent.ui_wait` DEBUG logging)
- [x] CI quality gates (`make check`, `make test`, `make test-slow`, `make verify-ai-tasks`)
- [ ] Prometheus metrics (N/A — desktop Qt application / test harness)
- [ ] Grafana dashboards (N/A — test suite / local developer tool)
- [ ] Alerting rules (N/A — CI notifications on build failure or regression)

---

## Validation Results

Validation results:
- [x] Logs are correctly formatted (verified in `tests/test_agent_dialog_settle_e2e.py` caplog assertions and `tests/test_agent_dialog_settle_teardown_stress.py` warning formatter).
- [x] Metrics are collected correctly (statistical formulation and binomial power calculation verified).
- [x] Logging works in error scenarios (diagnostic error rewrapping with modal scalar fields verified).
- [x] Large data structures are not logged (output tails bounded to `stdout[-2000:]` and `stderr[-1000:]`).
- [x] Metrics are available for monitoring (accessible via test summary, exit codes, and CI artifacts).

---

## Notes

- **Task Scope**: As established in [PYPOST-1209](https://pypost.atlassian.net/browse/PYPOST-1209) requirements and architecture, this story specifies the evaluation contract and documents baseline facts.
- **Downstream Consumption**:
  - **MITIGATE-2 ([PYPOST-1210](https://pypost.atlassian.net/browse/PYPOST-1210))** will execute the stress metrics across dependency pin updates.
  - **MITIGATE-3 ([PYPOST-1211](https://pypost.atlassian.net/browse/PYPOST-1211))** will execute the stress metrics across application-side lifecycle modifications.
- **Settlement Observability**: The deterministic settlement ownership matrix ensures that when a candidate succeeds, the removal of `xfail` and dev doc settlement will produce unambiguous CI test status changes (transitioning from `XFAIL` to `PASSED`).
