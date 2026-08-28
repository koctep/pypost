# Roadmap: PYPOST-1217

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1217/10-requirements.md` drafted
  - Business goals, user stories, acceptance criteria, boundaries, entities, and non-goals documented
  - Step 1 acceptance gate passed (review verdict PASS)
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1217/20-architecture.md` drafted
  - Concurrency architecture, deterministic post-ready flush, tree realization settlement, strict invariant preservation, failure taxonomy differentiation, and Step 3 failing repro plan documented
  - Step 2 acceptance gate passed (review verdict PASS)
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_session_event_settle.py` (assert post-ready event loop flush and tree layout realization settlement)
  - Step 3 acceptance gate passed (review verdict PASS)
- [x] **STEP 4: Development**
  - [x] Implemented Component 1: Deterministic post-ready event loop flush (`QCoreApplication.processEvents()`) in `pypost/agent/lifecycle.py` inside `AgentAppSession.start()`
  - [x] Implemented Component 2: Layout realization settlement (`_pump()`) in `pypost/agent/ui_actions.py` inside `_select_tree()` before index lookup
  - [x] Verified Component 3: Negative exception invariant contract preserved (`UiTargetNotInteractableError` with `"option not found"`)
  - [x] Verified Step 3 failing repro tests turn green: `tests/test_agent_session_event_settle.py` (2/2 passing)
  - [x] Verified target test passes: `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`
  - [x] Verified full module and concurrent integration suite passes: `tests/test_ui_actions.py` (14/14 passing) and concurrent subset (6/6 files passing under 8 workers)
  - Step 4 acceptance gate passed (review verdict PASS)
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1217/40-code-cleanup.md`
  - Validated PEP 8, flake8, and line length (<= 100 chars) on modified and new files
  - Confirmed absence of unused imports, debug prints, and dead code
  - Verified explicit timeout markers (`pytest.mark.timeout(60)`) on test suites
  - Executed quality gates: `make lint` and `make verify-ai-tasks` passed
  - Step 5 acceptance gate passed (review verdict PASS)
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1217/50-observability.md` drafted
  - Structured logging documented across `AgentAppSession`, `ui_wait`, and UI interaction primitives
  - Diagnostic and runtime metrics analyzed across 4 execution profiles (isolated node, isolated file, concurrent subset, full parallel suite)
  - Timeout hierarchy (test-level 60s, worker-level 120s, ready polling 30s, wait polling 10s) documented
  - Event loop draining and layout settlement latency characteristics documented
  - Quality gate validation and monitoring integration documented
  - Step 6 acceptance gate passed (review verdict PASS)
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1217/60-tech-debt.md` drafted
  - Evaluated shortcuts: additive post-ready event loop flush in `AgentAppSession.start()`
    and realization pump in `_select_tree()`; preserving gateway async thread architecture
    without wholesale redesign
  - Verified code quality: strict typing, docstrings, coupling analysis, and PEP 8 compliance
  - Verified test requirements: explicit timeout markers per `do-testing` on all tests
    (NO BLOCKER)
  - Assessed performance concerns: sub-millisecond event loop pump overhead and mitigation
    of 8-worker GIL contention
  - Identified follow-up tasks: shared event-settle helpers evaluation and item view settlement
    audit (NON-BLOCKER)
- [/] **STEP 8: Dev Docs**
  - Updated `doc/dev/testing.md`: Documented implemented stabilization solution for collection
    tree actions parallel flake (post-ready event loop flush in `AgentAppSession.start()`, tree
    realization settlement in `_select_tree()`, negative contract preservation, regression suite,
    and 100% pass multi-profile results)
  - Updated `doc/dev/gui_testing.md`: Updated troubleshooting table entry with PYPOST-1217
    stabilization resolution
  - Step 8 acceptance gate passed (review verdict PASS)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1217/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1217/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_session_event_settle.py`
- `ai-tasks/PYPOST-1217/25-failing-repro.md`

### STEP 4: Development

- `pypost/agent/lifecycle.py` (deterministic post-ready event loop flush)
- `pypost/agent/ui_actions.py` (tree layout realization settlement)
- `tests/test_agent_session_event_settle.py` (Step 3 failing repro tests now passing)

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1217/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1217/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1217/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md` (implemented stabilization architecture & resolution, regression suite,
  verification profiles)
- `doc/dev/gui_testing.md` (troubleshooting table resolution)

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
