# Roadmap: PYPOST-1357

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1357/00-roadmap.md`
  - `ai-tasks/PYPOST-1357/10-requirements.md`
  - Language: Python
  - Business goal: restore a trustworthy Make quality signal for the
    collection export UI suite when the worker dies after all 19 nodes PASS
    under an affected test environment
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1357/20-architecture.md`
  - Research: post-PASS SIGSEGV after 19 PASSes; env-sensitive deps; PYPOST-1315
    dispose already wired for collections; missing collections contract (TD-2 /
    PYPOST-1479); Qt DeferredDelete / sendPostedEvents; diagnostic-artifact
    fallback when live crash unavailable
  - Design: reuse `dispose_collections_export_fixture`; Step 3 module
    `tests/test_collection_export_ui_teardown_repro.py` with polarity-split
    A-complete (desired end-state) + A-incomplete (residual-liveness GREEN
    negative control); named R-* red→green drivers (R-residual / R-env-crash /
    restored-host default **R-autouse** missed-finally); bounded subprocess B or
    diagnostic artifact; cause fork teardown vs environment vs both; reject
    os._exit / skips / timeout removal / permanently red suite members
  - Failing-repro plan for Step 3: included in `20-architecture.md`
    Implementation Plan (not N/A); restored-host flip is R-autouse when
    A-complete/B already green
- [x] **STEP 3: Failing Repro Test**
  - Red/evidence module: `tests/test_collection_export_ui_teardown_repro.py`
    - A-complete GREEN:
      `test_a_complete_collections_dispose_reaches_desired_end_state`
    - A-incomplete GREEN (residual-liveness negative control):
      `test_a_incomplete_collections_dispose_leaves_residual_liveness`
    - **R-autouse RED** (restored-host Step 3→4 driver):
      `test_missed_collections_dispose_reaches_desired_end_state`
      — omit `dispose_collections_export_fixture`; desired end-state fails with
      `shiboken6.isValid(panel)` still True
    - B GREEN (zero-crash diagnostic matrix, not live SIGSEGV):
      `test_b_bounded_collection_export_ui_subprocess_evidence_matrix`
  - Cause fork: **R-autouse** (missed-finally / no autouse dispose). A-complete
    already green ⇒ not R-residual. B zero-crash on restored host
    (PySide6==6.11.1, shiboken6==6.11.1, pydantic==2.14.0; 3/3 child exit 0)
    ⇒ not R-env-crash as live red member; diagnostic matrix in B pass path.
  - No production fix in this step; existing
    `tests/test_collection_export_ui.py` assertions/timeouts untouched.
- [x] **STEP 4: Development**
  - [x] Added `_created_presenters` registry + autouse
    `_cleanup_collections_export_presenters` calling
    `dispose_collections_export_fixture` in
    `tests/test_collection_export_ui.py` and
    `tests/test_collection_export_ui_teardown_repro.py` (env-export /
    PYPOST-1315 TD-5 pattern)
  - [x] R-autouse green: `test_missed_collections_dispose_reaches_desired_end_state`
    omits dispose and asserts desired end-state after autouse (fixture LIFO via
    `_collections_export_end_state_checks`)
  - [x] A-incomplete remains green (residual-liveness asserted before autouse);
    A-complete / B unchanged polarity; product assertions/timeouts preserved
  - [x] Validated: `make test WORKERS=1` on repro + collection export UI
    (`-m "not slow"`); parallel `make test` on both files — all exit 0
- [x] **STEP 5: Code Cleanup**
  - Focus: `tests/test_collection_export_ui.py`,
    `tests/test_collection_export_ui_teardown_repro.py`
  - Artifact: `ai-tasks/PYPOST-1357/40-code-cleanup.md`
  - Typing polish: `_make_presenter` return types; end-state checks
    `list[Callable[[], None]]` + fixture/test annotations
  - Validated: `make lint` OK; `make typecheck` OK; focused
    `make test WORKERS=1` on both files (`-m "not slow"`) PASSED
  - No unused imports/vars/debug prints; intentional finally+autouse dispose kept
- [x] **STEP 6: Observability**
  - Artifact: `ai-tasks/PYPOST-1357/50-observability.md`
  - Decision: **N/A for production** — harness-only R-autouse dispose/autouse;
    no `pypost/` logging or metrics added
  - Coverage retained via parallel-runner exit codes + collections dispose
    contract (`tests/test_collection_export_ui_teardown_repro.py`); no new
    test-helper log noise
- [x] **STEP 7: Technical Debt Analysis**
  - Artifact: `ai-tasks/PYPOST-1357/60-tech-debt.md`
  - No BLOCKER timeouts; suite + repro keep `pytestmark` / B `timeout(360)`
  - New follow-ups: TD-1 redundant finally+autouse; TD-2 duplicated registry;
    TD-3 narrow leftover audit
  - Addressed upstream: close PYPOST-1479; retarget/close PYPOST-1482 vs TD-1
  - Existing (do not re-file): PYPOST-1483, PYPOST-1485, PYPOST-1486, PYPOST-1303
  - Accepted: TD-7 zero-crash B diagnostic; TD-6 docs → Step 8
  - Phase D creates/closes Jira — not this step
- [x] **STEP 8: Dev Docs**
  - `doc/dev/export_ui_qt_dispose.md` — collections registry + autouse (not
    finally-only); teardown repro A-complete / A-incomplete / R-autouse / B;
    why end-state asserts run in a separate fixture teardown (LIFO after
    autouse dispose); TD-6
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1357/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1357/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_collection_export_ui_teardown_repro.py` (R-autouse red;
  A-complete / A-incomplete / B green diagnostic)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1357/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1357/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1357/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/export_ui_qt_dispose.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit
  hash are reported in chat only, never written to this file.
