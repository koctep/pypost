# Roadmap: PYPOST-1184

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1184/00-roadmap.md`
  - `ai-tasks/PYPOST-1184/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1184/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_tabs_presenter_insert.py` — red: `pypost.ui.presenters.tabs_presenter_insert`
    does not exist yet, and `add_new_tab`/`_insert_mcp_client_tab`/`_insert_websocket_tab` still
    contain the duplicated insert-before-plus logic instead of delegating to the shared helper.
    Existing behavioral coverage (focus, save_tabs_state gating, insertion position) already
    exists in `tests/test_tabs_presenter.py`; no new behavioral test needed per architecture.
- [x] **STEP 4: Development**
  - [x] Added `pypost/ui/presenters/tabs_presenter_insert.py` with free function
    `insert_tab_before_plus(presenter, tab, name, *, save_state=True)`, following the
    `TYPE_CHECKING`-import-of-presenter pattern from `tabs_presenter_close.py`.
  - [x] Refactored `add_new_tab`, `_insert_mcp_client_tab`, and `_insert_websocket_tab` in
    `pypost/ui/presenters/tabs_presenter.py` to delegate to the new helper, removing the
    triplicated insert-before-plus/append/focus/save block; each call site kept its own
    `name` computation and existing return behavior (`add_new_tab` returns `None`,
    the other two `return tab`). File shrank from 1064 to 1039 lines.
  - [x] `tests/test_tabs_presenter_insert.py` and `tests/test_tabs_presenter.py` pass
    (targeted `PYTEST_ARGS` run via `make test`).
  - [x] Orchestrator ran full-suite `make test` (base commit b93cdb83): 323 passed, 7 failed,
    6 skipped. Triaged all 7 against baseline per failing-tests-triage: 5 dedupe into existing
    open PYPOST-1261 (function_expression_resolver invalid_arity x2, solid_audit_baseline
    snapshot drift, template_service invalid_arity x2 — reproduce identically at base commit
    b93cdb83); 1 filed as new PYPOST-1262 (test_makefile_lifecycle.py / test_makefile_targets.py
    120s worker timeout, unrelated files); 1 filed as new PYPOST-1263
    (test_collection_import_profile flaky timing test — passed on rerun and at baseline). None
    caused by this task's diff (only pypost/ui/presenters/tabs_presenter.py and the new
    tabs_presenter_insert.py module were touched).
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1184/50-observability.md`
  - No logging/metrics added: sibling helper `tabs_presenter_close.py` (closest
    structural precedent) is also unlogged, and all three call sites of
    `insert_tab_before_plus` are already covered by caller-level logging
    (`handle_new_tab`, `restore_tabs`, `load_request_from_history`) and
    metrics (`track_gui_new_tab_action`). Pure refactor, no behavior change.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1184/60-tech-debt.md` — no shortcuts, no code quality issues, no missing
    tests, no performance concerns, no architecture deviations, no hardcoded values found.
    Confirmed `tests/test_tabs_presenter_insert.py` has `pytestmark = pytest.mark.timeout(30)`
    (not a BLOCKER). Recorded 7 pre-existing, already-triaged test failures from Step 4's
    full-suite run under Follow-up Tasks (PYPOST-1261, PYPOST-1262, PYPOST-1263).
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/websocket_draft_tab.md` and `doc/dev/mcp_client_draft_tab.md`: added
    `tabs_presenter_insert.py::insert_tab_before_plus` to each Architecture section, refreshed
    stale `tabs_presenter.py` LOC snapshots (1059→1039/1165) and forward-references that named
    this task as pending future work, now resolved. Updated
    `doc/dev/websocket_collections_menu.md` Related-work row from "(still open)" to done. No new
    doc file created (pure internal refactor, no new public API — existing docs already had the
    right hooks to extend per td-70-dev-docs guidance).
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1184/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1184/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1184/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1184/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1184/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
