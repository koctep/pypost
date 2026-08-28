# Failing Repro Evaluation: PYPOST-1216

**Step 3 Status**:
`N/A — diagnostic investigation only (no runtime behavioral change in this task;`
`stabilization owned by FIX-1 / PYPOST-1217)`

## 1. Task Scope & Context

- **Jira Task Key**: [PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216) (DIAG-1)
- **Parent Epic**: [PYPOST-1188](https://pypost.atlassian.net/browse/PYPOST-1188)
  (Stabilize `test_live_collection_tree_missing_option_raises`)
- **Upstream Task**: [PYPOST-1215](https://pypost.atlassian.net/browse/PYPOST-1215)
  (REPRO-1 — Baseline Flake Evidence in `ai-tasks/PYPOST-1215/25-failing-repro.md`)
- **Downstream Task**: [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217)
  (FIX-1 — Stabilization and Parallel Gate Verification)

## 2. Rationale for N/A Determination

Per `ai-tasks/PYPOST-1216/20-architecture.md` (Section "Step 3 Failing Repro Requirement")
and `td-25-failing-repro` skill guidelines:

1. **Diagnostic / Architectural Deliverable Only**:
   - PYPOST-1216 is strictly an analytical and architectural investigation task.
   - It delivers a formal failure classification, evaluates the direct `apply_theme` vs
     `uvicorn` race hypothesis, contrasts the flake with related prior art
     ([PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) and
     [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) /
     [PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040)), and provides
     remediation constraints for downstream implementation.

2. **No Production Code Modifications**:
   - In accordance with the non-goals and architectural boundaries of this story, zero
     modifications to production code under `pypost/` are introduced.
   - The behavioral contract established in
     [PYPOST-975](https://pypost.atlassian.net/browse/PYPOST-975) for `COLLECTION_TREE`
     negative selection assertions remains strictly locked and unchanged.

3. **Separation of Concerns Across Epic Lifecycle**:
   - **REPRO-1 (PYPOST-1215)**: Captured differential execution benchmarks and concurrency
     timing inflation (+40.3% duration under 8-worker suite load).
   - **DIAG-1 (PYPOST-1216 - This Task)**: Established root-cause taxonomy (refuting direct
     memory race; confirming compound GIL/CPU contention & event pump starvation).
   - **FIX-1 (PYPOST-1217)**: Owns test harness stabilization, event loop synchronization
     gating, and full parallel test suite verification (`make test` / `make check`).

## 3. Target Node & Behavioral Contract Lock

- **Target Test Node**: `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`
- **Assertion Invariants**:
  - Target widget: `COLLECTION_TREE` (`QTreeView`, `objectName == "pypost_collection_tree"`)
  - Target operation: `session.ui_select(COLLECTION_TREE, "__no_such_collection_tree_option__")`
  - Expected exception: `UiTargetNotInteractableError`
  - Expected message substring: `"option not found"`
- **Current Baseline Status**: Passes 100% deterministically in isolated runs
  (`make test PYTEST_ARGS="tests/test_ui_actions.py"`).

## 4. Downstream Handoff to FIX-1 ([PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217))

FIX-1 will consume the architecture and failure taxonomy delivered in
`ai-tasks/PYPOST-1216/20-architecture.md` to:
1. Implement deterministic event pump flushing during `AgentAppSession.start()` and UI
   readiness polling.
2. Stabilize widget tree realization handling under multi-worker parallel CPU saturation.
3. Validate zero regressions across both single-file runs and full parallel suite runs
   (`make check`).
