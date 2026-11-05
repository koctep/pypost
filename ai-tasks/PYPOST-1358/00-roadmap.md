# Roadmap: PYPOST-1358

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1358/00-roadmap.md`
  - `ai-tasks/PYPOST-1358/10-requirements.md`
  - Language: Python
  - Business goal: restore a trustworthy Make quality signal for the
    environment list widget suite when the worker dies after all 13
    assertions PASS (pre-existing, environment-sensitive native
    termination; SIGSEGV/SIGBUS observed)
  - Review-gap fix: defined “bounded repeated” as **5 consecutive**
    isolated `WORKERS=1` successes (reset on failure; stop when streak
    met); reframed Done as outcome-based elimination of post-PASS native
    termination (lifecycle/dispose notes are hypotheses only;
    non-lifecycle root cause still satisfies); clarified Done gate is
    isolated suite only—full/parallel `make check` not required
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1358/20-architecture.md`
  - Code fact: list/import suite uses `close()`-only; env export already uses
    `dispose_qt_root` on the same `EnvironmentListWidget` type
  - Design: outcome-based fix; primary hypothesis H1/R-dispose (reuse
    `dispose_qt_root` + registry/autouse); H2/R-autouse; H3/R-other allowed
  - Step 3 plan: `tests/test_environment_list_widget_teardown_repro.py`
    (A-complete / A-incomplete / R-dispose / B); Done = 5 consecutive
    isolated `WORKERS=1` Make successes
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_environment_list_widget_teardown_repro.py`
    - A-complete: `test_a_complete_environment_list_dispose_reaches_desired_end_state` (green)
    - A-incomplete: `test_a_incomplete_environment_list_close_only_leaves_residual_liveness` (green negative control)
    - R-dispose: `test_r_dispose_suite_close_only_reaches_desired_end_state` (**RED** — close-only leaves `shiboken6.isValid` True)
    - B: `test_b_bounded_environment_list_widget_subprocess_evidence_matrix` (zero-crash diagnostic on this host; accepted)
  - Cause fork: **R-dispose** (H1) — suite close-only teardown leaves live `EnvironmentListWidget` C++ roots; shared family with PYPOST-1315 / PYPOST-1357 (same widget type; list/import still close-only vs export dispose)
  - Verified: `make test WORKERS=1 PYTEST_ARGS='tests/test_environment_list_widget_teardown_repro.py -v'` → 1 failed (R-dispose), 3 passed
- [x] **STEP 4: Development**
  - [x] Wired `dispose_qt_root` + `_created_widgets` registry/autouse into
    `tests/test_environment_list_widget.py` (mirror env export PYPOST-1315)
  - [x] Updated R-dispose driver to apply suite dispose path (close-only →
    `dispose_qt_root`) so Step 3 red→green contract holds
  - [x] Teardown repro green:
    `make test WORKERS=1 PYTEST_ARGS='tests/test_environment_list_widget_teardown_repro.py -v'`
    → exit 0 (R-dispose + A-complete / A-incomplete / B)
  - [x] Acceptance streak: **5 consecutive** successes of
    `make test WORKERS=1 PYTEST_ARGS='tests/test_environment_list_widget.py'`
    (run_ids ab3890ca6d3f, 4750d7f1313d, 09114a6047c8, 917fb411f1d8,
    c5ecd253960d; each exit 0 / file PASSED; no reset)
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1358/40-code-cleanup.md`
  - Import-order cleanup in `tests/test_environment_list_widget.py`
    (stdlib → third-party → local; match export sibling)
  - Kept close()+dispose pattern and A-complete/R-dispose separation
  - Validated: `make lint` OK; focused `WORKERS=1` Make test of list
    widget + teardown repro → 2/2 PASSED
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1358/50-observability.md`
  - Production logging/metrics: **N/A** — test-harness-only fix
    (`dispose_qt_root` + `_created_widgets` registry/autouse in list suite;
    no `pypost/` changes). Architecture already flagged Step 6 as thin/N/A
    for harness-only work.
  - Failure class remains observable via parallel-runner non-zero worker
    exit codes and teardown-repro contract asserts (unchanged)
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1358/60-tech-debt.md`
  - No BLOCKER (timeouts present on list suite + teardown repro)
  - Follow-ups: TD-1 retarget PYPOST-1481 (redundant finally close);
    TD-2 dedupe/rename A-complete vs R-dispose; TD-5 shared env-widget
    registry helper; TD-9 inventory other close-only GUI suites;
    Phase D close/verify PYPOST-1480 (A-incomplete covers 1315 TD-3)
  - Step 8 owns TD-3/TD-4 doc+comment sync; TD-6 accepted (B zero-crash);
    TD-7/TD-8 existing PYPOST-1485 / PYPOST-1303
- [x] **STEP 8: Dev Docs**
  - Extended `doc/dev/export_ui_qt_dispose.md` for list/import registry/autouse
    (PYPOST-1358) alongside export suites; title/overview/architecture/API/
    validate commands + list teardown repro section; TD-4
  - Updated `tests/helpers/qt_widget_dispose.py` module docstring (no longer
    export-only)
  - Aligned `tests/test_environment_list_widget_teardown_repro.py` comments so
    A-incomplete / `_suite_close_only` describe close-only residual path, not
    the product suite's full registry/autouse teardown; TD-3
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1358/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1358/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1358/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1358/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1358/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/export_ui_qt_dispose.md` (extended for list/import)
- `tests/helpers/qt_widget_dispose.py` (module docstring)
- `tests/test_environment_list_widget_teardown_repro.py` (comment sync)

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
