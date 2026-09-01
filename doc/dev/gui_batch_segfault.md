# Large-Batch GUI apply_theme Segmentation Fault (PYPOST-1117 / PYPOST-1212)

## Overview

During continuous integration and local batch test execution, executing a large collection of GUI-heavy test modules (~110 modules, ~1,384+ tests) in a single long-running pytest process under headless offscreen QPA results in a native segmentation fault (`SIGSEGV`, exit code 139 / returncode -11).

The crash consistently occurs in `pypost/ui/styles/style_manager.py:102` inside `StyleManager.apply_theme()` during `QStyleFactory.create("Fusion")` / `app.setStyle(...)` calls.

This issue is tracked under parent epic [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) and structured into three sequential deliverables:
1. **REPRO-1 ([PYPOST-1212](https://pypost.atlassian.net/browse/PYPOST-1212))**: Deterministic repro and evidence baseline (*this document*).
2. **DIAG-1 ([PYPOST-1213](https://pypost.atlassian.net/browse/PYPOST-1213))**: Root-cause diagnosis (investigating Shiboken wrapper lifecycle vs `QStyle`/`QPalette` accumulation).
3. **MITIGATE-1 ([PYPOST-1214](https://pypost.atlassian.net/browse/PYPOST-1214))**: Safe mitigation, bounded batching thresholds, and CI ownership.

---

## Environment Specifications

The defect occurs consistently under the standard headless Linux test environment:

| Dimension | Specification | Notes |
| --- | --- | --- |
| **Operating System** | Linux 6.6+ (x86_64 / aarch64) | Headless CI containers and Linux developer workstations |
| **Python Interpreter** | Python 3.13.5 (verified) / Python 3.11+ | Standard CPython runtime |
| **Qt / PySide6 Bindings** | `PySide6==6.11.1` (Qt 6.11.1) | Shiboken C++ wrapper layer with Qt6 C++ runtime |
| **QPA Platform** | `QT_QPA_PLATFORM=offscreen` | Headless minimal QPA plugin |
| **Process Model** | Single OS process | Module-scoped / shared `QApplication` instance |
| **Termination Signal** | `SIGSEGV` (signal 11) / exit code 139 | Native C++ memory access violation |

---

## Reproduction Procedure and Commands

### 1. Diagnostic CLI Harness (`scripts/repro_gui_batch_segfault.py`)

A dedicated CLI harness is available in `scripts/repro_gui_batch_segfault.py` to run batches under controlled subprocesses, capture stderr backtraces, and evaluate process returncodes:

```bash
# Full unpartitioned large-batch execution in 1 OS process (triggers SIGSEGV / Exit Code 139)
python scripts/repro_gui_batch_segfault.py --mode=full --timeout=180

# Bounded chunked execution (e.g. 15 modules per subprocess batch) (PASS / Exit Code 0)
python scripts/repro_gui_batch_segfault.py --mode=bounded --batch-size=15

# Single isolated module execution (PASS / Exit Code 0)
python scripts/repro_gui_batch_segfault.py --mode=single
```

### 2. Automated Regression & Baseline Test Guard (`tests/test_gui_batch_segfault_repro.py`)

The test suite includes `tests/test_gui_batch_segfault_repro.py` to assert both the clean baseline and the unmitigated failure state:

```bash
# Run baseline tests via Make
make test-slow PYTEST_ARGS="tests/test_gui_batch_segfault_repro.py -v -m 'slow or not slow'"
```

---

## Evidence Baseline and Crash Signatures

### Traceback & Fatal Signal

When `PYTHONFAULTHANDLER=1` is active, the crash outputs the following traceback on standard error:

```text
Fatal Python error: Segmentation fault

Current thread 0x0000ffff8a9fe020 (most recent call first):
  File ".../pypost/ui/styles/style_manager.py", line 102 in apply_theme
  File ".../tests/test_settings_dialog.py", line 145 in test_theme_switch
  ...
  File ".../pytest/runner.py", line 169 in pytest_runtest_call
```

### Crash Site Characterization

- **Location**: `pypost/ui/styles/style_manager.py:102`
- **Function**: `StyleManager.apply_theme(theme_name: str, mode: str)`
- **Mechanism**: The segfault does not occur during the first invocation of `apply_theme`. It occurs only after cumulative test execution (>50-100 test modules) creates, styles, and destroys numerous Qt widgets in the same process address space.

### Distinction from SettingsDialog Teardown Crash (PYPOST-1040 / PYPOST-1115)

| Attribute | PYPOST-1040 / PYPOST-1115 | PYPOST-1117 ([PYPOST-1212](https://pypost.atlassian.net/browse/PYPOST-1212)) |
| --- | --- | --- |
| **Crash Site** | `Shiboken::callCppDestructor<QWidgetItem>` | `StyleManager.apply_theme` (`QStyleFactory.create("Fusion")`) |
| **Trigger Mechanism** | Session-end forced cyclic GC (`gc.collect()`) on `SettingsDialog` layout wrappers | Sustained large-batch execution across ~110 GUI modules in 1 process |
| **Workload Scale** | Small (2 tests in `test_agent_dialog_settle_e2e.py`) | Large (~110 modules, >1,000 test cases) |
| **Defect Class** | Teardown double-free in Shiboken wrapper table | Cumulative Qt style / palette state corruption |

---

## Pass/Fail Contrast Matrix

| Execution Topology | Command Shape | Modules / Tests | Process Model | Result | Exit Code / Signal | Duration |
| --- | --- | --- | --- | --- | --- | --- |
| **Full Large Batch** | `python scripts/repro_gui_batch_segfault.py --mode=full` | ~110 modules (~1,384 tests) | Single Process | **CRASH (SIGSEGV)** | `139` / `SIGSEGV` | ~40–60s |
| **8 Bounded Batches** | `python scripts/repro_gui_batch_segfault.py --mode=bounded --batch-size=15` | ~110 modules (8 chunks) | Subprocess per Chunk | **PASS** | `0` | ~75s total |
| **Per-File Isolation** | `scripts/run_parallel_tests.py` / `make test` | 110 modules | Subprocess per File | **PASS** | `0` | ~25–35s |
| **Individual Module** | `pytest tests/test_settings_dialog.py` | 1 module (24 tests) | Single Process | **PASS** | `0` | ~1.8s |
| **Bounded Guard Test** | `test_bounded_gui_batch_execution_passes_cleanly` | 4 modules (~45 tests) | Child Subprocess | **PASS** | `0` | ~1.1s |

---

## Downstream Handoff Contracts

### 1. DIAG-1 Contract ([PYPOST-1213](https://pypost.atlassian.net/browse/PYPOST-1213))

- **Objective**: Diagnose whether the segfault is caused by deferred Shiboken C++ wrapper collection or `QStyle` / `QPalette` accumulation under repeated theme changes.
- **Reproduction Input**: `python scripts/repro_gui_batch_segfault.py --mode=full` with debugger / `faulthandler` attached.

### 2. MITIGATE-1 Contract ([PYPOST-1214](https://pypost.atlassian.net/browse/PYPOST-1214))

- **Objective**: Implement safe batch execution boundaries and document CI ownership.
- **Verification Harness**: `scripts/repro_gui_batch_segfault.py --mode=bounded` and `tests/test_gui_batch_segfault_repro.py`.

---

## References

- Epic: [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) — Diagnose large-batch Qt/PySide6 GUI test segfault in `apply_theme`
- Task Artifact: `ai-tasks/PYPOST-1212/30-baseline-evidence.md`
- [GUI Testing Guide](gui_testing.md)
- [Parallel Test Runner Orchestrator](parallel_test_runner.md)
