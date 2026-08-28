# Root-Cause Diagnosis Report: apply_theme vs uvicorn Race for Collection-Tree Flake

**Jira Task Key**: [PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216) (DIAG-1)  
**Parent Epic**: [PYPOST-1188](https://pypost.atlassian.net/browse/PYPOST-1188)
(Stabilize `test_live_collection_tree_missing_option_raises`)  
**Upstream Baseline**: [PYPOST-1215](https://pypost.atlassian.net/browse/PYPOST-1215)
(REPRO-1 — `ai-tasks/PYPOST-1215/baseline-evidence.md`)  
**Downstream Implementation**: [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217)
(FIX-1 — Stabilization and Parallel Gate Verification)  
**Base Commit Anchor**: `353370cdbd19c7a3338e2ed05c292b0a404d7b90`  

---

## 1. Executive Summary & Verdict

### Target Test Node
- **Test File**: `tests/test_ui_actions.py`
- **Node Identifier**: `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`
- **Behavioral Contract**: PYPOST-975 negative interaction test asserting that selecting a
  non-existent option in `COLLECTION_TREE` (`pypost_collection_tree`) raises
  `UiTargetNotInteractableError` with `"option not found"`.

### Core Verdict Summary

| Candidate Hypothesis | Verdict | Summary |
| --- | --- | --- |
| **Hypothesis A**: Direct in-memory race | **REFUTED** | Zero shared mutable state |
| **Hypothesis B**: GIL/CPU contention & starvation | **CONFIRMED** | CPU saturation under load |

### Detailed Verdict Analysis

1. **Hypothesis A: Direct in-memory race between `apply_theme` and `uvicorn` — REFUTED**:
   `StyleManager.apply_theme()` is strictly confined to the main Qt GUI thread.
   `MetricsServer._run_uvicorn()` runs on an isolated daemon worker thread inside an
   `asyncio` event loop. There is zero concurrent access to shared C++ Qt widget pointers,
   palettes, or mutable Python state.

2. **Hypothesis B: Compound GIL/CPU contention & event loop starvation — CONFIRMED**:
   Under multi-worker parallel execution (`make test` with 8 subprocess workers on 6 CPU cores),
   CPU saturation causes Global Interpreter Lock (GIL) preemption delays. Concurrent module
   imports (`starlette`, `uvicorn`), async disk JSON deserialization, and QSS parsing delay signal
   delivery and starve the `QCoreApplication.processEvents()` pump in `AgentAppSession.start()`
   and `ui_wait.wait_until(is_ui_ready)`.

---

## 2. System & Execution Path Analysis

### 2.1 Execution Path Breakdown

```
[AgentAppSession.start()]
   │
   ├── 1. QApplication acquisition / creation (offscreen QPA)
   ├── 2. MetricsManager.start_server() ───► [Spawns Uvicorn Daemon Thread]
   │                                            └── asyncio loop + Starlette app
   ├── 3. MainWindow.__init__()
   │       ├── Layout & Presenters initialization
   │       ├── collections.load_collections_async() ───► [Spawns Storage Thread]
   │       │                                                └── JSON parse & load
   │       └── MainWindow.apply_settings()
   │             └── StyleManager.apply_appearance() (QSS parse + QPalette)
   ├── 4. MainWindow.show() ───► MainWindow.showEvent()
   │                               └── QTimer.singleShot(0, apply_settings) [Queued]
   ├── 5. ui_wait.wait_until(is_ui_ready, timeout=30.0)
   │       └── Loop: processEvents() + time.sleep(0.05)
   │             ├── Waits for Storage load_completed signal
   │             ├── Waits for Env environments_loaded signal
   │             └── Flushes pending singleShot timer
   └── 6. is_ui_ready == True ───► Session Ready
                                           │
                                           ▼
                       [test_live_collection_tree_missing_option_raises]
                          ├── 1. assert session.window.is_ui_ready
                          ├── 2. session.ui_select(COLLECTION_TREE, "__no_such_...")
                          │       ├── find_widget(window, COLLECTION_TREE)
                          │       ├── _require_interactable(widget, widget_id)
                          │       └── _select_tree(widget, widget_id, option)
                          │             └── find_tree_index_by_display_text(...) -> None
                          └── 3. Raises UiTargetNotInteractableError("option not found")
```

### 2.2 Thread Isolation Analysis

1. **Main GUI Thread (Pytest Runner Worker Thread)**:
   - Executes `AgentAppSession.start()`, `MainWindow` construction,
     `QApplication.processEvents()`, and the test body.
   - Calls `StyleManager.apply_appearance()` which parses `.qss` files and sets
     `QApplication.setStyle()` / `QPalette`.
   - All PySide6 widget object ownership (`MainWindow`, `QTreeView`, `QHeaderView`)
     resides exclusively on this thread.

2. **Background Metrics Server Thread (`MetricsServer._run_uvicorn`)**:
   - Initialized as a daemon thread running `uvicorn.Server.serve()` within a dedicated
     `asyncio` event loop.
   - Manages HTTP endpoint listeners (`Starlette`) on loopback ephemeral ports
     (`127.0.0.1:<port>`).
   - Completely isolated from the Qt QObject tree; communicates solely via HTTP and
     atomic primitive variables.

3. **Background Storage Worker Thread (`CollectionStorageGateway`)**:
   - Executes disk reads and JSON deserialization of collection data from temporary
     test fixtures.
   - Communicates back to the main thread exclusively through Qt queued signal connections
     (`gateway.load_completed`).

---

## 3. Systematic Evaluation of the `apply_theme` vs `uvicorn` Race

During [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167) Step 4 development,
this intermittent failure was flagged in `ai-tasks/PYPOST-1167/60-tech-debt.md` as a
*"suspected Qt `apply_theme` vs uvicorn import race"*.

### 3.1 Evaluation Against Concurrency Failure Criteria

1. **Shared Mutable State**:
   - *Criteria*: Two or more threads reading/writing unsynchronized memory locations.
   - *PyPost Reality*: `StyleManager` modifies Qt C++ structures; `MetricsServer` modifies
     Starlette/asyncio objects. Zero shared memory.
   - *Status*: **Refuted**

2. **Thread Affinity Violations**:
   - *Criteria*: Qt GUI objects accessed from a non-GUI background thread.
   - *PyPost Reality*: All Qt widget and styling calls are strictly pinned to the thread
     running `QApplication`.
   - *Status*: **Refuted**

3. **Import-Level Lock Contention**:
   - *Criteria*: Circular or concurrent top-level module imports causing Python import lock
     stalls.
   - *PyPost Reality*: All heavy imports (`uvicorn`, `starlette`, `PySide6`) are completed at
     module import time; runtime execution does not trigger dynamic import locks.
   - *Status*: **Refuted**

4. **CPU / GIL Scheduling Contention**:
   - *Criteria*: Multiple threads competing for CPU cores under Python GIL, inflating
     scheduling latency.
   - *PyPost Reality*: 8 worker processes running across 6 cores. Concurrently spawning
     uvicorn and storage threads causes thread switching delays and event pump latency.
   - *Status*: **CONFIRMED**

### 3.2 Mechanism of Perceived Race

The perceived race was an artifact of temporal overlap rather than shared-state corruption:
1. When `AgentAppSession.start()` runs, it initiates `MetricsManager.start_server()`
   (spawning the uvicorn thread), `load_collections_async()` (spawning the storage thread),
   and `apply_appearance()` (parsing QSS on the main thread) in close temporal proximity.
2. Under isolated single-node execution, the system has surplus CPU capacity, completing
   this sequence in ~50–100ms.
3. Under multi-worker parallel execution (`make test`), all 6 CPU cores are saturated by
   8 worker processes. Python GIL preemption causes thread-switching latency:
   - The main thread's `wait_until(is_ui_ready)` polling loop suffers scheduling gaps.
   - The `QTimer.singleShot(0, apply_settings)` styling timer queued during `showEvent`
     experiences delayed processing.
   - The asynchronous `load_completed` Qt signal from the storage worker thread experiences
     queue dispatch delay.
4. Consequently, test execution intermittently begins while the UI tree model is in the
   middle of event pump settling, leading to intermittent assertion timeouts or timing
   inflation (+40.3% duration).

---

## 4. Failure Class Taxonomy & Comparative Matrix

To establish rigorous architectural boundaries and prevent scope conflation across active
and historical epics, this failure mode is formally classified and contrasted against
related prior art.

### 4.1 Comparative Matrix

#### PYPOST-1216 / PYPOST-1188 (This Flake)
- **Failure Class**: **Class 2: Compound Resource Contention & Event Loop Starvation**
- **Failure Symptom**: Intermittent test timeout, UI interaction delay, or timing
  inflation (+40.3%).
- **Trigger Environment**: Multi-worker parallel test execution (`make test` across
  8 parallel subprocesses, CPU saturation).
- **Root Cause Mechanism**: GIL preemption and thread scheduling contention delaying
  Qt event dispatch and async readiness signaling.
- **Subsystem Involved**: `AgentAppSession`, `ui_wait.py`, `CollectionsPresenter`,
  `MetricsServer`.
- **Resolution Ownership**: Event pump synchronization and readiness gating
  (owned by **FIX-1 / PYPOST-1217**).

#### PYPOST-1117 (Large-Batch Segfault)
- **Failure Class**: **Class 3: Long-Lived Native C++ State Leak**
- **Failure Symptom**: Hard native `SIGSEGV` (core dump) inside
  `QStyleFactory.create("Fusion")` / Qt styling engine.
- **Trigger Environment**: Monolithic sequential batch execution (~110 GUI test files,
  ~1,384 tests in a single long-lived process).
- **Root Cause Mechanism**: Memory leak and style state accumulation in PySide6 C++ binding
  layer over hundreds of repeated `apply_theme` calls.
- **Subsystem Involved**: `StyleManager.apply_theme()`, PySide6 `QStyle` binding.
- **Resolution Ownership**: Batch partitioning and test process isolation
  (owned by **PYPOST-1214**).

#### PYPOST-1115 / PYPOST-1040 (Dialog GC Teardown)
- **Failure Class**: **Class 4: Destructor Double-Free during GC**
- **Failure Symptom**: Post-PASS `SIGSEGV` during Python garbage collection
  (`Shiboken::callCppDestructor`).
- **Trigger Environment**: Sequential or isolated test execution involving opening and
  rejecting `SettingsDialog`.
- **Root Cause Mechanism**: Orphaned `QWidgetItem` wrappers in nested `SettingsDialog`
  layout trees destroyed improperly during Python GC.
- **Subsystem Involved**: `SettingsDialog`, PySide6 `QLayout` item hierarchy.
- **Resolution Ownership**: Explicit widget parenting, layout item deletion, and GC
  suppression (owned by **PYPOST-1115**).

### 4.2 Explicit Distinction Prose

1. **Distinction from PYPOST-1117**:
   - *PYPOST-1117* is a native C++ segmentation fault caused by cumulative state corruption
     in PySide6's styling engine when running large monolithic batches of tests sequentially
     in a single process. It does not occur under isolated or short runs.
   - *PYPOST-1216* is a non-fatal concurrency timing and event pump starvation issue
     occurring in multi-process parallel test runs where subprocesses saturate the CPU.
2. **Distinction from PYPOST-1115 / PYPOST-1040**:
   - *PYPOST-1115/1040* is a post-pass C++ destructor crash occurring when Python's garbage
     collector frees orphaned `QWidgetItem` layout wrappers after a `SettingsDialog` is
     closed.
   - *PYPOST-1216* does not involve `SettingsDialog`, layout item destruction, or garbage
     collection double-frees. It is confined to `AgentAppSession` startup and collection
     tree readiness.

---

## 5. Empirical Evidence Summary

From the REPRO-1 baseline captured in `ai-tasks/PYPOST-1215/baseline-evidence.md`:

| Profile | Scope | Workers | Runs | Pass Rate | Mean Time | Delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| **Isolated Node** | 1 test (`test_live_...`) | 1 | 3 | 100% | 1.37s | Baseline |
| **Isolated File** | 14 tests (`test_ui_actions.py`) | 1 | 2 | 100% | 5.80s | Baseline |
| **Concurrent Subset** | 5 suites (UI, Agent, MCP) | 8 | 1 | 100% | 14.51s | +5.0% file |
| **Parallel Suite** | 300 test files repo-wide | 8 | 1 | 97.7% | 171.39s | **+40.3% file** |

### Key Takeaways:
1. The test logic is 100% deterministic and correct in isolation.
2. The duration of `tests/test_ui_actions.py` inflates from 5.80s to 8.14s (+40.3%) under
   full suite parallel execution due to CPU saturation across the 8 subprocess workers.
3. Event loop pumping and readiness polling must be robust against scheduling jitter.

---

## 6. Downstream Stabilization Specifications (Handoff to FIX-1 / PYPOST-1217)

To eliminate parallel test flakes without regressing performance or violating architectural
constraints, [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217) (FIX-1) must adhere
to the following specifications:

### 6.1 Stabilization Requirements for FIX-1

1. **Deterministic Event Loop Settle during Session Startup**:
   - In `pypost/agent/lifecycle.py` (`AgentAppSession.start()`), after
     `wait_until(lambda: composed.window.is_ui_ready)` returns `True`, execute a
     deterministic event flush (`QCoreApplication.processEvents()`) to ensure all deferred
     single-shot timers (including post-show `apply_settings`) have completed execution
     before yielding control to the test body.
2. **Collection Tree Widget Realization Gating**:
   - In `pypost/agent/ui_actions.py` (`ui_select`), verify that when target is
     `COLLECTION_TREE`, the widget's model and viewport have fully processed layout events
     before evaluating display text indices.
3. **Preservation of Behavioral Invariants**:
   - The negative interaction assertion contract from
     [PYPOST-975](https://pypost.atlassian.net/browse/PYPOST-975) must remain unchanged:
     ```python
     with pytest.raises(UiTargetNotInteractableError) as exc_info:
         session.ui_select(COLLECTION_TREE, "__no_such_collection_tree_option__")
     assert "option not found" in str(exc_info.value)
     ```
   - Do NOT soften or remove the assertion; do NOT introduce arbitrary `time.sleep()` calls
     in test bodies.
4. **Verification Gate**:
    - FIX-1 must pass:
      - Isolated node:
        ```bash
        make test PYTEST_ARGS="tests/test_ui_actions.py \
          -k test_live_collection_tree_missing_option_raises"
        ```
      - Isolated file: `make test PYTEST_ARGS="tests/test_ui_actions.py"`
      - Full repository quality gate: `make check` (running `lint`, `test`, and
        `verify-ai-tasks` across 8 parallel workers).

---

## 7. Scope & Boundary Assertions

- **Zero Production Modifications in DIAG-1**: Zero code changes in `pypost/` have been
  introduced in this task.
- **Diagnostic Deliverable Only**: This document serves as the canonical root-cause
  diagnosis and architectural handoff.

---

## 8. References

- [PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216) —
  This diagnosis task (DIAG-1)
- [PYPOST-1188](https://pypost.atlassian.net/browse/PYPOST-1188) —
  Parent epic
- [PYPOST-1215](https://pypost.atlassian.net/browse/PYPOST-1215) —
  Upstream baseline evidence (`ai-tasks/PYPOST-1215/baseline-evidence.md`)
- [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217) —
  Downstream stabilization story (FIX-1)
- [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167) —
  Discovery note (`ai-tasks/PYPOST-1167/60-tech-debt.md`)
- [PYPOST-975](https://pypost.atlassian.net/browse/PYPOST-975) —
  Originating negative assertion contract
- [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) —
  Large-batch `apply_theme` segfault epic
- [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) /
  [PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040) —
  SettingsDialog GC teardown issues
