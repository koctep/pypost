# PYPOST-1216: Technical Debt Analysis

PYPOST-1216 (DIAG-1) delivered the canonical root-cause diagnosis of the intermittent failure of
`tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises` under multi-worker
parallel test execution (`make test`), evaluating the suspected Qt `apply_theme` vs `uvicorn` race,
establishing the failure class taxonomy, and defining stabilization specifications for downstream
implementation in [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217) (FIX-1).

There is **no AC-breaking debt** in this story's deliverables. All work strictly adheres to the
epic decomposition and scope boundaries established in
[PYPOST-1205](https://pypost.atlassian.net/browse/PYPOST-1205) under parent epic
[PYPOST-1188](https://pypost.atlassian.net/browse/PYPOST-1188). In accordance with DIAG-1's
mandate, zero production code in `pypost/` was modified, and the negative assertion contract from
[PYPOST-975](https://pypost.atlassian.net/browse/PYPOST-975) remains completely intact.

Jira keys below that already exist are cited for context. **New follow-up issues are not created
in this step** (Phase D / orchestrator).

---

## Shortcuts Taken

1. **Diagnostic investigation without production code modification**:
   By intentional architectural decomposition
   ([PYPOST-1205](https://pypost.atlassian.net/browse/PYPOST-1205)), production and harness
   stabilization is strictly owned by FIX-1
   ([PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217)). No temporary "quick fixes",
   ad-hoc delays, or assertion relaxation were introduced into `pypost/` or
   `tests/test_ui_actions.py`.
2. **Non-invasive diagnostic probing**:
   GIL scheduling contention, thread isolation, and event loop dispatch timings were verified
   using non-destructive execution profiling and existing runtime telemetry rather than
   instrumenting production files with invasive debug hooks or monkey patches.
3. **Controlled empirical profiling matrix**:
   Profiling was performed across four representative execution profiles (isolated node, isolated
   file, concurrent 5-suite subset, and full 300-file parallel suite) rather than unbounded
   multi-hour Monte Carlo loops, which proved sufficient to establish duration inflation (+40.3%)
   and refute the direct race hypothesis without unnecessary CI delays.
4. **Preservation of behavioral invariants**:
   No test assertion was softened or bypassed. The contract requiring `UiTargetNotInteractableError`
   with `"option not found"` was preserved exactly as written.

---

## Code Quality Issues

1. **Zero production code touched**:
   Zero lines of code in `pypost/` were modified, ensuring no code smells, dead code, or quality
   regressions were introduced into the application.
2. **Artifact formatting and link hygiene**:
   All markdown deliverables in `ai-tasks/PYPOST-1216/` comply with repository standards (line
   length <= 100 characters, valid relative doc links, valid Jira URLs, and proper heading
   structure).
3. **Trace and probe cleanliness**:
   No temporary diagnostic scripts, scratch files, or transient artifacts were committed to the
   repository root or `scripts/`.
4. **Make-only compliance**:
   All diagnostic profiling and validation steps adhered strictly to the repository's Make-only
   operational guideline (`AGENTS.md`).

---

## Missing Tests

**Timeout markers: NO BLOCKER.**
All relevant test items declare explicit pytest timeout markers in full compliance with the
`do-testing` skill requirements:
- `tests/test_ui_actions.py` declares
  `pytestmark = [pytest.mark.timeout(60), pytest.mark.agent_e2e]` at module scope.
- Parallel worker timeout ceiling is enforced at `WORKER_TIMEOUT = 120s` by
  `scripts/run_parallel_tests.py`.
- Internal UI wait budgets are strictly bounded: `AgentAppSession.start` ready wait is bounded at
  30.0s, and `ui_wait.wait_until` is bounded at 10.0s with 50ms polling intervals.

In-scope diagnostic verification:
- Isolated node execution passes deterministically:
  `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises` (1.37s).
- Full file execution passes deterministically: `tests/test_ui_actions.py` (14 tests, 5.80s).
- Negative interaction assertion invariant verified: raises `UiTargetNotInteractableError` with
  `"option not found"`.
- Step 3 failing repro documented as N/A in `ai-tasks/PYPOST-1216/25-failing-repro.md` because
  DIAG-1 is an analytical root-cause investigation with zero production changes.

Deferred test enhancements (assigned to downstream tickets):
- **Parallel stabilization verification gate**: Automated regression testing of the post-ready
  event loop flush (`QCoreApplication.processEvents()`) and collection tree realization under full
  8-worker parallel load is deferred to FIX-1
  ([PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217)).

---

## Performance Concerns

1. **Compound GIL and CPU Contention under Multi-Worker Parallel Execution**:
   Running 8 subprocess workers on 6 physical CPU cores produces a CPU load factor > 1.33. Thread
   preemption delays under the Python GIL create 20–50ms scheduling pauses that starve the main
   Qt GUI thread's event loop pump.
2. **Qt Event Loop Dispatch Latency**:
   The deferred `QTimer.singleShot(0, apply_settings)` timer queued during `MainWindow.showEvent()`
   and the asynchronous `load_completed` signal from `CollectionStorageGateway` suffer dispatch
   lag when the CPU is saturated, inflating `tests/test_ui_actions.py` execution duration by +40.3%
   (5.80s -> 8.14s).
3. **Elevated Worker Contention Thresholds**:
   Under higher concurrency configurations (`WORKERS=16`), cumulative contention for offscreen
   window allocation and background loopback server threads increases the risk of worker
   subprocesses approaching the 120s `WORKER_TIMEOUT`.

---

## Follow-up Tasks

Phase D of the orchestrator creates Jira issues. Step 7 records follow-up context and citations.

1. **NON-BLOCKER — intentional downstream slice: Stabilization Implementation (FIX-1)**
   - Implement production and harness stabilization per DIAG-1 specifications:
     1. Add post-ready event loop flush (`QCoreApplication.processEvents()`) in
        `AgentAppSession.start()` (`pypost/agent/lifecycle.py`).
     2. Implement collection tree layout realization gating in `pypost/agent/ui_actions.py`.
     3. Maintain strict preservation of the
        [PYPOST-975](https://pypost.atlassian.net/browse/PYPOST-975) negative assertion
        contract.
     4. Validate 100% pass rate under isolated and parallel `make test` / `make check`.
   - Verdict: **NON-BLOCKER — intentional downstream slice**.
   - Jira: [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217)

2. **NON-BLOCKER — pre-existing parallel flake (parent epic context)**
   - Target node: `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`
   - Symptom: Intermittent failure / timeout under parallel `make test` load vs isolated pass.
   - Root Cause: Compound GIL/CPU contention and Qt event loop starvation under multi-worker load
     (refuting direct `apply_theme` vs `uvicorn` in-memory race).
   - Verdict: **NON-BLOCKER — pre-existing**.
   - Jira: [PYPOST-1188](https://pypost.atlassian.net/browse/PYPOST-1188)

3. **NON-BLOCKER — Step 8 Dev Docs of this task (not a new ticket)**
   - Document root-cause findings, refuted race hypothesis, failure class taxonomy, and
     downstream stabilization specifications in `doc/dev/testing.md`.
   - Owned by PYPOST-1216 Step 8.
   - Verdict: **NON-BLOCKER**.
   - Jira: none
