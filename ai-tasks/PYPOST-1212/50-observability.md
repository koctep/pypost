# PYPOST-1212: Observability Implementation

## Logging Implementation

### Added Logs

The reproduction harness (`scripts/repro_gui_batch_segfault.py`) and test baseline guard (`tests/test_gui_batch_segfault_repro.py`) implement structured stdout/stderr capturing, native signal interception, and bounded traceback extraction:

- **EMERG**: `scripts/repro_gui_batch_segfault.py` (`run_pytest_subprocess`) / `tests/test_gui_batch_segfault_repro.py` (`test_large_batch_gui_execution_unmitigated_segfault_repro`) - Process killed by native segmentation fault (`SIGSEGV`, exit code 139 / returncode -11) trapped with Python faulthandler C-level stack traces.
- **ALERT**: `scripts/repro_gui_batch_segfault.py` (`run_pytest_subprocess`) - Subprocess timeout expiration (e.g. hung process exceeding 180s/45s limits).
- **CRIT**: `tests/test_gui_batch_segfault_repro.py` (`test_bounded_gui_batch_execution_passes_cleanly`) - Unexpected failure or crash in baseline bounded GUI test modules.
- **ERR**: `scripts/repro_gui_batch_segfault.py` (`execute_harness`) - Batch execution failure where child pytest process returns non-zero exit code.
- **WARNING**: `scripts/repro_gui_batch_segfault.py` (`execute_harness`) - Large-batch test execution reproduced expected native failure (`status="reproduced"`).
- **NOTICE**: `scripts/repro_gui_batch_segfault.py` (`execute_harness`) - Batch progression events (e.g., executing batch `idx + 1` of `N`, reporting chunk completion).
- **INFO**: `scripts/repro_gui_batch_segfault.py` (`execute_harness`, `main`) - Discovery summary (count of discovered GUI test modules, e.g. 110 modules), execution mode (`full`, `bounded`, `single`), environment summary, and final test status.
- **DEBUG**: `scripts/repro_gui_batch_segfault.py` (`run_pytest_subprocess`) / `tests/test_gui_batch_segfault_repro.py` - Bounded stdout/stderr tails (last 2000 characters) containing Python traceback frames and crash site detection signatures (`StyleManager.apply_theme`, `QStyleFactory.create`).

### Log Structure

Log format used:
- Structured logs: **Yes** (Human-readable CLI summaries paired with machine-readable structured JSON reports via `--output-json`).
- Includes context: **Yes** (Environment metadata: OS release/architecture, Python version, PySide6 version, Qt version, `QT_QPA_PLATFORM`; command execution lists, test module counts, signal decodings, duration timers).
- Log levels: `EMERG`, `ALERT`, `CRIT`, `ERR`, `WARNING`, `NOTICE`, `INFO`, `DEBUG`.
- Bounded payload: Captured outputs are strictly bounded using tail truncation (`[-2000:]`) to prevent unbounded log file growth during catastrophic crash cascades or verbose test failures.

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time / Execution duration**:
  - `duration_seconds`: Total wall-clock duration of batch execution in child subprocesses, recorded via `time.monotonic()` (reported in seconds to 3 decimal places).
  - Module-level timeout threshold: 240s explicit timeout guard (`@pytest.mark.timeout(240)`).
  - Subprocess child timeouts: 180s (`full` / large batch) and 45s (`bounded` / single chunk).
- **Throughput**:
  - Modules per batch: ~14 modules per chunk in bounded mode (8 batches across 110 modules).
  - Module discovery throughput: Discovered 110 GUI test modules (~1384 test cases).
- **Error rate / Pass ratio**:
  - Pass/fail ratio across execution modes: 100% pass on bounded batches vs 0% pass (100% crash/xfail) on unpartitioned single-process large batch.
  - Returncode / exit code classification: 0 (clean success), 1 (test assertion failure), 139 / -11 (SIGSEGV).

### Business Metrics

Business & Diagnostic Baseline Metrics:
- **Crash signature classification**: Categorization of exit code into `exit_code`, `returncode`, `signal` (11 for SIGSEGV), and `signal_name` (`SIGSEGV`).
- **Crash site detection**: Automated heuristic detection of `crash_site` (`pypost/ui/styles/style_manager.py` / `QStyleFactory.create`) and `crash_method` (`StyleManager.apply_theme`) from stderr/stdout diagnostics.
- **Batch topology comparison**: Contrast matrix between full batch (1 process, 110 modules), bounded batches (8 chunks of 15), per-file isolation (110 worker subprocesses), and single-module execution.

### System Health Metrics

System health & runtime diagnostics:
- **Resource usage**:
  - Process isolation boundary: Each batch executed in a fresh OS child process with independent address space.
  - Environment inventory: OS distribution/architecture, CPython 3.13.5 runtime, `PySide6 6.11.1`, `Qt 6.11.1`, and headless `QT_QPA_PLATFORM=offscreen`.
- **Component status**:
  - `faulthandler` active status via `PYTHONFAULTHANDLER=1` and `-o faulthandler_timeout=60`.
  - Subprocess timeout status (`timed_out: bool`).

## Monitoring Integration

Integration with monitoring systems:
- [x] Standard output / error stream diagnostics compatible with CI/CD logs
- [x] Machine-readable JSON output reports (`--output-json`) for automated artifact ingestion
- [x] Native signal decoding (`signal.Signals`) and exit code mapping for CI telemetry
- [x] CPython `faulthandler` integration for low-level C/C++ backtrace dump
- [ ] Prometheus metrics (N/A - developer test harness / CI diagnostic tool)
- [ ] Grafana dashboards (N/A - developer test harness / CI diagnostic tool)
- [ ] Alerting rules (N/A - captured via CI pipeline failure notifications)
- [ ] Log aggregation (ELK, Loki, etc.) (N/A - captured via CI artifact retention)

## Validation Results

Validation results:
- [x] Logs are correctly formatted (clear CLI output with execution headers and summaries)
- [x] Metrics are collected correctly (timestamps, durations, return codes, signal names, test counts)
- [x] Logging works in error scenarios (timed out subprocesses, non-zero exits, native SIGSEGV crashes)
- [x] Large data structures are not logged (bounded tail previews limited to 2000 characters)
- [x] Metrics are available for monitoring and downstream ingestion by DIAG-1 (PYPOST-1213) and MITIGATE-1 (PYPOST-1214)

## Notes

- **Structured JSON Contract**: When invoked with `--output-json <path>`, `scripts/repro_gui_batch_segfault.py` produces machine-readable records containing execution metadata, environment inventory, duration timers, signal identification, and truncated output tails.
- **Deterministic Diagnostics**: The harness decouples the test orchestrator from native child process crashes, allowing CI test runners to capture complete fatal crash dumps without aborting the main test session.
- **Handoff to DIAG-1 / MITIGATE-1**: The structured metrics and baseline output files enable downstream tasks to quantitatively verify root-cause theories and benchmark mitigation strategies.
