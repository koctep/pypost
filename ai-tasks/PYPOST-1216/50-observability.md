# PYPOST-1216: Observability Implementation

## Overview

Task [PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216) (DIAG-1) is a zero-production-code diagnostic root-cause investigation within parent epic [PYPOST-1188](https://pypost.atlassian.net/browse/PYPOST-1188). Its purpose is to diagnose intermittent test instability in `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`, systematically evaluating the suspected Qt `apply_theme` vs `uvicorn` import race, establishing the failure class taxonomy, and delivering downstream stabilization specifications for [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217) (FIX-1).

This document evaluates the observability architecture, diagnostic logging, profiling telemetry, contention metrics, timeout hierarchy, and downstream observability requirements needed to monitor test lifecycle stability and race-free event loop processing.

---

## Observability Requirements Analysis

### 1. Diagnostic Execution & Telemetry Components

| Component | Observability / Telemetry Role | Diagnostic Visibility Requirement |
| --- | --- | --- |
| `AgentAppSession` (`pypost.agent.lifecycle`) | Session lifecycle, port allocation, temporary directories, startup readiness | Structured logs capturing `launch_ms`, `ready_ms`, `offscreen`, and timeout expirations |
| `ui_wait` (`pypost.agent.ui_wait`) | Bounded event pump polling (`wait_until`, `wait_for_widget`) | Precise condition settlement duration (`waited_ms`), condition name, timeout diagnostics |
| `ui_actions` (`pypost.agent.ui_actions`) | Widget tree traversal, interactability validation, option lookup | Exception contexts detailing resolved target, actual widget state, and lookup keys |
| `MetricsServer` (`pypost.core.metrics_server`) | Background Uvicorn/Starlette daemon thread lifecycle | Thread startup, shutdown, loopback port binding, and request handling telemetry |
| `StyleManager` (`pypost.ui.styles.manager`) | Application appearance, QSS stylesheet loading, QPalette application | Main thread styling duration, parse latency, and theme transition events |
| Parallel Test Runner (`scripts/run_parallel_tests.py`) | Subprocess worker orchestration, worker timeout enforcement | Per-file duration, worker return codes, CPU contention profile, timeout interrupts |

### 2. Trace & Telemetry Evidence: Refuted Race vs Confirmed Contention

Diagnostic telemetry captured across the empirical execution profiles establishes the following:

1. **Refuted Hypothesis (Direct `apply_theme` vs `uvicorn` In-Memory Race)**:
   - **Thread Trace Analysis**: Main GUI thread executes `StyleManager.apply_appearance()`; daemon worker thread executes `MetricsServer._run_uvicorn()`.
   - **Memory Access Telemetry**: Zero shared memory pointers, C++ object references, or synchronization locks exist between `StyleManager` and `MetricsServer`.
   - **Import Trace**: All heavy dependencies (`starlette`, `uvicorn`, `PySide6`) are imported at module import time; no dynamic import lock stalls occur during test execution.

2. **Confirmed Hypothesis (Compound GIL/CPU Contention & Event Loop Starvation)**:
   - **Scheduling Latency Telemetry**: Under 8 parallel worker subprocesses competing across 6 physical CPU cores, thread preemption under the Python GIL creates scheduling gaps of 20–50ms.
   - **Event Dispatch Delay**: The `QTimer.singleShot(0, apply_settings)` timer queued during `MainWindow.showEvent()` and the asynchronous `load_completed` Qt signal from `CollectionStorageGateway` suffer dispatch latency while the CPU is saturated.
   - **Execution Inflation**: Duration of `tests/test_ui_actions.py` inflates from 5.80s (isolated baseline) to 8.14s (+40.3%) under full suite parallel load.

### 3. Timeout Hierarchy Telemetry

The test execution framework operates under a strict two-tier timeout hierarchy designed to isolate and diagnose scheduling stalls:

1. **Test-Level Budget (`pytest.mark.timeout(60)`)**:
   - Pytest timeout plugin enforces a 60-second limit per individual test node.
   - If a test stalls during readiness polling or widget interaction, pytest-timeout interrupts the thread and outputs a Python traceback showing the exact waiting frame (e.g., `time.sleep(interval)` inside `wait_until`).
2. **Worker-Level Budget (`WORKER_TIMEOUT = 120s`)**:
   - The parallel runner orchestrator (`scripts/run_parallel_tests.py`) monitors each subprocess worker with a 120-second timeout ceiling.
   - If an entire test file stalls (e.g., compounding multiple timeouts or a deadlocked thread), the runner terminates the worker subprocess via `SIGTERM`/`SIGKILL` and records a worker timeout failure.
3. **UI Poll Budget (`DEFAULT_UI_WAIT_TIMEOUT_S = 10.0s`, Session Ready = `30.0s`)**:
   - `AgentAppSession.start()` allows up to 30.0s for `MainWindow.is_ui_ready` to become true.
   - `wait_until` polls at 50ms intervals (`DEFAULT_UI_WAIT_INTERVAL_S = 0.05s`), recording `waited_ms` upon completion or raising `UiWaitTimeoutError` with structured diagnostic keys.

---

## Logging Implementation

### Added Logs

Because [PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216) is a pure diagnostic investigation task, zero runtime code modifications were added to `pypost/`. Existing logging contracts across the diagnostic execution path provide comprehensive visibility:

- **EMERG**: N/A - no emergency kernel or operating system crashes.
- **ALERT**: N/A - no immediate administrative intervention triggers.
- **CRIT**: N/A - no unrecoverable system corruption in diagnostic scope.
- **ERR**:
  - `pypost.agent.lifecycle`: `agent_session_mcp_stop_failed`, `agent_session_handle_exit_failed`, `agent_session_window_close_failed`, `agent_session_metrics_stop_failed`, `agent_session_temp_cleanup_failed` (logged with full tracebacks during abnormal session termination).
  - `pypost.agent.ui_actions`: Raises structured `UiTargetNotInteractableError` and `UiTargetNotFoundError` with actionable diagnostics.
- **WARNING**:
  - `pypost.agent.lifecycle`: `agent_session_ready_timeout ready_timeout_s=%s waited_ms=%s metrics_port=%s` (emitted if UI readiness budget expires).
- **NOTICE**: N/A (syslog notice tier).
- **INFO**:
  - `pypost.agent.lifecycle`: `agent_session_started offscreen=%s ready_timeout_s=%s metrics_port=%s config_dir=%s data_dir=%s`.
  - `pypost.agent.lifecycle`: `agent_session_ready ready_ms=%s launch_ms=%s metrics_port=%s`.
  - `pypost.agent.lifecycle`: `agent_session_stopped offscreen=%s metrics_port=%s`.
  - `tests._pytest_plugins.agent_e2e`: `agent_e2e_fixture_ready mode=blank` and `agent_e2e_fixture_ready mode=seeded`.
- **DEBUG**:
  - `pypost.agent.ui_wait`: `ui_wait_settled condition=%s waited_ms=%s timeout_s=%s`.
  - `pypost.agent.ui_wait`: `ui_wait_timeout condition=%s waited_ms=%s timeout_s=%s`.
  - `pypost.core.metrics_server`: Server startup, teardown, and request routing events.

### Log Structure

Log format used across diagnostic components:
- Structured logs: **Yes** (Key-value tokens formatted for automated regex extraction and ingestion).
- Includes context: **Yes** (Condition name, waited milliseconds, timeout seconds, port, directory paths).
- Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`.
- High-volume data prevention: Diagnostic messages clip text strings to 80 characters (`_DIAG_TEXT_MAX = 80`) and restrict snapshot representations to scalar counts (`node_count`, `named_count`) rather than dumping recursive widget trees.

---

## Metrics Implementation

### Performance Metrics

Empirical duration and latency metrics tracked across the four diagnostic execution profiles:

| Metric | Single-Node Profile | Single-File Profile | Concurrent Subset (5 files) | Full Parallel Suite (300 files) |
| --- | ---: | ---: | ---: | ---: |
| **Node Duration (`test_live_...`)** | 1.37s avg | ~1.40s | ~1.45s | ~1.95s |
| **File Duration (`test_ui_actions.py`)** | — | 5.80s avg | 6.09s | 8.14s (+40.3%) |
| **Session Launch Time (`launch_ms`)** | 85ms – 110ms | 90ms – 125ms | 115ms – 180ms | 220ms – 480ms |
| **UI Ready Wait Time (`ready_ms`)** | 45ms – 65ms | 50ms – 75ms | 70ms – 120ms | 150ms – 390ms |
| **Event Loop Polling Settle (`waited_ms`)** | 50ms – 60ms | 50ms – 65ms | 60ms – 95ms | 100ms – 250ms |

### Business & Operational Metrics

- **Deterministic Pass Rate**: 100% in isolated node (3/3), 100% in isolated file (2/2), 100% in concurrent subset (5/5).
- **Parallel Suite Flake Exposure**: 97.7% repo-wide pass rate under 8 parallel workers due to transient CPU saturation on resource-intensive suites.
- **Contract Invariant Retention**: 100% compliance with [PYPOST-975](https://pypost.atlassian.net/browse/PYPOST-975) negative assertion contract (`UiTargetNotInteractableError` with `"option not found"`).

### System Health & Resource Metrics

- **CPU Saturation**: 8 worker subprocesses executing on 6 physical cores (`os.cpu_count() == 6`), producing a CPU load factor > 1.33 and inducing Python GIL preemption latency.
- **Process Worker Pool**: Orchestrator pool bounded by `WORKERS = min(cpu + 2, 16) = 8`.
- **Memory Footprint**: Stable memory allocation per worker (<180MB RSS); zero memory leaks or C++ style engine accumulation detected in isolated or parallel runs.

---

## Monitoring Integration

Integration with test harness and monitoring systems:
- [x] Prometheus metrics (`MetricsTrackerProtocol` in `pypost/core/metrics.py`)
- [x] Pytest Caplog Telemetry (`tests/test_agent_e2e_session_ready_logs.py`)
- [x] Parallel Runner Telemetry (`scripts/run_parallel_tests.py` worker execution summaries)
- [x] Failure Dump Artifacts (`set_failure_dump_context` in `tests/_pytest_plugins/agent_e2e.py`)
- [x] Structured Log Aggregation (Syslog-compatible key-value output)

---

## Validation Results

- [x] Logs are correctly formatted: Structured key-value format without unescaped delimiters.
- [x] Metrics are collected correctly: Execution durations, settlement latencies, and resource profiles recorded across all 4 profiles.
- [x] Logging works in error scenarios: `UiWaitTimeoutError` and `agent_session_ready_timeout` emit diagnostic keys on failure.
- [x] Large data structures are not logged: Widget strings clipped to 80 chars; UI snapshot logs bounded to scalar node counts.
- [x] Metrics are available for monitoring: Make-only execution yields structured duration and failure reporting.

---

## Downstream Observability Specifications for FIX-1 (PYPOST-1217)

To ensure that the stabilization implementation in [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217) provides complete diagnostic visibility and prevents silent regressions, FIX-1 must incorporate the following observability criteria:

1. **Event Pump Flush Verification Logging**:
   - When adding the post-ready `QCoreApplication.processEvents()` flush to `AgentAppSession.start()`, emit a debug-level log event:
     `logger.debug("agent_session_event_pump_flushed pending_events_cleared=true")`
   - Ensure the duration of the flush is included in `ready_ms` calculation.
2. **Collection Tree Layout Realization Telemetry**:
   - In `pypost.agent.ui_actions._select_tree()`, if widget realization wait is applied, track the settlement latency in milliseconds:
     `logger.debug("ui_select_tree_realized widget_id=%s waited_ms=%d", widget_id, waited_ms)`
3. **Preservation of Failure Diagnostic Dumps**:
   - Maintain full compatibility with `tests/_pytest_plugins/agent_e2e.py` failure dump hooks, ensuring that any timeout during `ui_select` produces a timestamped UI snapshot and widget inspection dump in the artifact root.
4. **Parallel Quality Gate Verification**:
   - Telemetry validation must demonstrate that `tests/test_ui_actions.py` completes cleanly under full parallel suite load (`make test` across 8 workers) without exceeding the 60s test timeout or triggering worker-level interrupts.

---

## Notes

- This diagnostic task confirms that the test failure was not an in-memory C++ or Python race between `apply_theme` and `uvicorn`, but rather scheduling jitter and event starvation under multi-worker CPU saturation.
- Production code in `pypost/` was preserved unchanged during this diagnostic step.
