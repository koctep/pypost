# PYPOST-1212: Baseline Evidence and Reproduction Record

## 1. Overview and Purpose

This artifact records the empirical baseline evidence and deterministic reproduction procedure for the large-batch Qt/PySide6 GUI test native segmentation fault investigated under epic [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) and decomposed in [PYPOST-1204](https://pypost.atlassian.net/browse/PYPOST-1204).

- **Ticket**: [PYPOST-1212](https://pypost.atlassian.net/browse/PYPOST-1212) (REPRO-1)
- **Downstream Tasks**: [PYPOST-1213](https://pypost.atlassian.net/browse/PYPOST-1213) (DIAG-1: Root-Cause Diagnosis) and [PYPOST-1214](https://pypost.atlassian.net/browse/PYPOST-1214) (MITIGATE-1: Safe Mitigation and CI Ownership)
- **Primary Deliverables**: Subprocess-based reproduction harness (`scripts/repro_gui_batch_segfault.py`), regression & baseline test guard (`tests/test_gui_batch_segfault_repro.py`), and developer guide (`doc/dev/gui_batch_segfault.md`).

---

## 2. Environment Inventory

The defect manifests consistently in headless Linux execution environments under the following hardware, OS, and runtime configurations:

| Dimension | Specification | Notes / Configuration |
| --- | --- | --- |
| **Operating System** | Linux 6.6+ (x86_64 / aarch64) | Headless Debian/Ubuntu CI containers and developer hosts |
| **Python Interpreter** | Python 3.13.5 (verified) / Python 3.11+ | Standard CPython interpreter with `PYTHONFAULTHANDLER=1` |
| **PySide6 Version** | `PySide6==6.11.1` | Qt6 C++ bindings layer (Shiboken6) |
| **Qt Runtime Version** | `Qt 6.11.1` | Underlying C++ GUI framework |
| **QPA Platform** | `QT_QPA_PLATFORM=offscreen` | Minimal headless QPA plugin for running GUI tests without an X11/Wayland display |
| **Process Model** | Single OS process | Module-scoped / shared `QApplication` instance across cumulative test modules |
| **Termination Signal** | `SIGSEGV` (signal 11 / exit code 139 / returncode -11) | Native memory access violation during C++ Qt style factory allocation |

---

## 3. Deterministic Reproduction Procedure & Command Shapes

### 3.1 CLI Diagnostic Harness (`scripts/repro_gui_batch_segfault.py`)

The repository provides a dedicated diagnostic harness for executing and contrasting test execution modes in isolated child subprocesses while trapping native signals:

```bash
# 1. Full unmitigated large batch (~110 GUI modules in 1 OS process) -> Triggers SIGSEGV / Exit Code 139
python scripts/repro_gui_batch_segfault.py --mode=full --timeout=180 --output-json=ai-tasks/PYPOST-1212/repro_full.json

# 2. Bounded chunked batches (e.g. 15 modules per chunk) -> PASS (Exit Code 0)
python scripts/repro_gui_batch_segfault.py --mode=bounded --batch-size=15 --output-json=ai-tasks/PYPOST-1212/repro_bounded.json

# 3. Single module execution -> PASS (Exit Code 0)
python scripts/repro_gui_batch_segfault.py --mode=single
```

### 3.2 Automated Regression & Baseline Test Guard (`tests/test_gui_batch_segfault_repro.py`)

An automated test module is registered under the test suite:
- `test_bounded_gui_batch_execution_passes_cleanly`: Asserts that bounded module subsets complete with exit code 0.
- `test_large_batch_gui_execution_unmitigated_segfault_repro`: Executes the large-batch workload in a single child process, capturing and asserting the native crash signature under unmitigated single-process conditions (`@pytest.mark.xfail(strict=False)`).

Execute via Make:
```bash
# Run repro suite via Make
make test-slow PYTEST_ARGS="tests/test_gui_batch_segfault_repro.py -v -m 'slow or not slow'"

# Or run fast check
make test PYTEST_ARGS="tests/test_gui_batch_segfault_repro.py -v -m slow"
```

---

## 4. Crash Site Analysis & Failure Signatures

### 4.1 Traceback & Fatal Error Forensic Signature

When executed in a single unmitigated OS process, `PYTHONFAULTHANDLER=1` captures the native crash during `apply_theme`:

```text
Fatal Python error: Segmentation fault

Current thread 0x0000ffff8a9fe020 (most recent call first):
  File ".../pypost/ui/styles/style_manager.py", line 102 in apply_theme
  File ".../tests/test_settings_dialog.py", line 145 in test_theme_switch
  ...
  File ".../pytest/runner.py", line 169 in pytest_runtest_call
```

### 4.2 Failure Site Characterization

- **File**: `pypost/ui/styles/style_manager.py` (line 102)
- **Method**: `StyleManager.apply_theme(theme_name: str, mode: str)`
- **Native Operations**:
  - `QStyleFactory.create("Fusion")`
  - `app.setStyle(...)`
  - `app.setPalette(...)`
- **Dynamic**: The crash does not occur on the first call to `apply_theme`. It occurs only after many (>50-100) GUI tests have created and destroyed widget hierarchies and called `apply_theme` repeatedly within the same OS process address space.

### 4.3 Distinction from Prior Art (PYPOST-1040 / PYPOST-1115)

| Dimension | PYPOST-1040 / PYPOST-1115 | PYPOST-1117 / PYPOST-1212 |
| --- | --- | --- |
| **Crash Site** | `Shiboken::callCppDestructor<QWidgetItem>` | `StyleManager.apply_theme` (`app.setStyle` / `QStyleFactory.create`) |
| **Trigger Mechanism** | pytest session-end forced cyclic GC (`gc.collect()`) on `SettingsDialog` layout wrappers | Sustained large-batch execution across ~110 GUI modules in a single process |
| **Workload Scale** | Small (2 tests in `test_agent_dialog_settle_e2e.py`) | Large (~110 modules, >1,000 test cases) |
| **Root Category** | Teardown double-free in Shiboken C++ wrapper table | Process-accumulated Qt C++ style / palette state instability |

---

## 5. Quantitative Pass/Fail Contrast Matrix

Empirical testing across execution topologies yields the following comparative results:

| Execution Topology | Invocation Command / Harness | Total Modules / Tests | Process Model | Result | Exit Code / Signal | Duration |
| --- | --- | --- | --- | --- | --- | --- |
| **Full Unpartitioned Batch** | `python scripts/repro_gui_batch_segfault.py --mode=full` | ~110 modules (~1,384 tests) | Single OS Process | **CRASH (SIGSEGV)** | `139` / `SIGSEGV` (returncode -11) | ~40–60s (until crash) |
| **8-Way Bounded Batches** | `python scripts/repro_gui_batch_segfault.py --mode=bounded --batch-size=15` | ~110 modules (8 chunks of ~14) | Fresh OS Process per Chunk | **PASS** | `0` (clean exit) | ~75s total |
| **Per-File Worker Isolation** | `scripts/run_parallel_tests.py` / `make test` | 110 modules (1 per worker) | Fresh Subprocess per File | **PASS** | `0` (clean exit) | ~25–35s (parallel) |
| **Individual Module Run** | `pytest tests/test_settings_dialog.py` | 1 module (24 tests) | Single OS Process | **PASS** | `0` (clean exit) | ~1.8s |
| **Bounded Baseline Guard** | `tests/test_gui_batch_segfault_repro.py::test_bounded_gui_batch_execution_passes_cleanly` | 4 modules (~45 tests) | Single Child Subprocess | **PASS** | `0` (clean exit) | ~1.1s |

---

## 6. Downstream Handoff Contracts

### 6.1 DIAG-1 Contract ([PYPOST-1213](https://pypost.atlassian.net/browse/PYPOST-1213))

- **Entry Point**: `python scripts/repro_gui_batch_segfault.py --mode=full`
- **Diagnostic Focus**:
  1. Determine whether the native crash is caused by deferred cyclic GC of Shiboken C++ wrapper objects or cumulative `QStyle` / `QPalette` allocation leaks under repeated `apply_theme` invocations.
  2. Utilize `faulthandler`, `gdb`, or `lldb` attached to the child process to inspect pointer validity and C++ heap structures at `QStyleFactory.create("Fusion")`.
  3. Validate independence from widget teardown lifecycles (differentiating from PYPOST-1040).

### 6.2 MITIGATE-1 Contract ([PYPOST-1214](https://pypost.atlassian.net/browse/PYPOST-1214))

- **Verification Harness**: `scripts/repro_gui_batch_segfault.py --mode=bounded` and `tests/test_gui_batch_segfault_repro.py`
- **Mitigation Scope**:
  1. Formalize process isolation or bounded batch execution in repository Make targets and CI workflows.
  2. Establish documented thresholds for maximum GUI test batch size per process.
  3. Update developer documentation and CI configuration with clear ownership and failure triage protocols.
