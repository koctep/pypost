# Roadmap: PYPOST-1315

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1315/00-roadmap.md`
  - `ai-tasks/PYPOST-1315/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1315/20-architecture.md`
  - Research: post-PASS SIGSEGV class; env vs collection export UI teardown asymmetry; Qt DeferredDelete / pytest-qt leak guidance; PYPOST-1212 subprocess evidence pattern
  - Design: shared dispose contract (close→pump→deleteLater→pump); reuse collections `teardown` when applicable; no assertion/timeout/skip regressions
  - Failing-repro plan for Step 3: `tests/test_environment_export_ui_teardown_repro.py` — deterministic shiboken/topLevelWidgets contract (primary red) + bounded subprocess crash evidence
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_environment_export_ui_teardown_repro.py`
    - `test_incomplete_env_dispose_leaves_no_live_environment_list_widget` — mandatory RED: incomplete close/deleteLater/single processEvents leaves `shiboken6.isValid(widget)` True and/or leftover topLevelWidgets
    - `test_bounded_env_export_ui_subprocess_evidence_matrix` — ≤5 isolated children of `tests/test_environment_export_ui.py`; archives return codes; fails on native `-11`/`-7`/139/135; all-zero accepted when host cannot reproduce (contract remains red gate)
  - Collection sibling deferred until Step 4 confirms shared dispose-class defect
- [x] **STEP 4: Development**
  - [x] Added `tests/helpers/qt_widget_dispose.py` — `dispose_qt_root` drains DeferredDelete via `QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)` (processEvents alone insufficient for EnvironmentListWidget); `dispose_collections_export_fixture` fences presenter teardown + model detach + panel dispose
  - [x] Wired contract repro + `tests/test_environment_export_ui.py` fixture cleanup to `dispose_qt_root` (assertions/timeouts unchanged)
  - [x] Wired `tests/test_collection_export_ui.py` finally paths to shared collections dispose (same close-only defect)
  - [x] Validation: `make test` — teardown repro (contract + matrix), environment_export_ui, collection_export_ui — all PASSED, exit 0
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1315/40-code-cleanup.md`
  - Lint: E501/E303 in teardown repro; import order in collection export UI
  - Validation: `make lint` OK; `make typecheck` OK; focused `make test` 3/3 PASSED
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1315/50-observability.md`
  - Decision: N/A for production logging/metrics — test-harness dispose helper only; existing parallel-runner exit codes + contract assertions cover the SIGSEGV class
  - No code changes under `pypost/` or `tests/` in this step
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1315/60-tech-debt.md`
  - Follow-ups recorded (no Jira in this step); timeout markers present — no BLOCKER
- [x] **STEP 8: Dev Docs**
  - `doc/dev/export_ui_qt_dispose.md` — export UI Qt dispose / DeferredDelete teardown guidance
  - Cross-links: `doc/dev/README.md`, `doc/dev/gui_testing.md`, `doc/dev/qt_activation_helper.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1315/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1315/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_environment_export_ui_teardown_repro.py` (RED — contract assertion)
- Host bounded subprocess matrix (5 children of `tests/test_environment_export_ui.py`): all exit 0 within bound — SIGSEGV not reproduced locally; contract test remains mandatory red gate per architecture

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1315/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1315/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1315/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/export_ui_qt_dispose.md`
- Index / cross-links: `doc/dev/README.md`, `doc/dev/gui_testing.md`, `doc/dev/qt_activation_helper.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
