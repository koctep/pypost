# Roadmap: PYPOST-1001

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_environment_list_widget.py::TestImportButtonWiring::test_mouse_click_on_import_button_starts_import`
    — written and run; PASSED against current code (production wiring at
    `environment_list_widget.py:124` already connects the click to
    `import_environments`; no defect found). Review subagent confirmed the
    lock is genuine by temporarily breaking the connect() call and observing
    the test fail, then reverting. Verification-lock outcome accepted per
    Step 1 requirements; Step 4 requires no production change.
- [x] **STEP 4: Development**
  - [x] No production code change required. Re-verified
    `pypost/ui/widgets/environments/environment_list_widget.py:122-124`
    (`import_btn` created, `set_widget_id(import_btn, ENV_IMPORT_BUTTON)`,
    `import_btn.clicked.connect(self.import_environments)`) and
    `pypost/ui/widget_ids.py:34` (`ENV_IMPORT_BUTTON =
    "pypost_env_import_button"`) against the Step 1 DoD — the click wiring
    is correct as-is, matching Step 3's finding. No production file was
    touched in this step (only the Step 3 test addition to
    `tests/test_environment_list_widget.py` already exists in the working
    tree).
  - [x] Test run confirms green:
    - `tests/test_environment_list_widget.py`: 10/10 passed, including
      `TestImportButtonWiring::test_mouse_click_on_import_button_starts_import`.
    - `tests/` filtered to `-k "environment" -m "not slow"`: 228 passed.
    - Full fast suite (`pytest tests/ -m "not slow"`, excluding one
      pre-existing flaky module unrelated to this ticket, see below):
      2175 passed, 22 deselected, 9 failed — all 9 failures are codebase-wide
      audit/baseline/catalog snapshot tests (`test_dialogs_audit.py`,
      `test_function_registry.py`, `test_jira_mcp_live_smoke.py`,
      `test_main_window_encrypted_startup.py`, `test_solid_audit_baseline.py`
      x4, `test_verify_ai_task_artifacts.py`) with zero references to
      `environment_list_widget`, `ENV_IMPORT_BUTTON`, or
      `import_environments` (confirmed via grep); pre-existing repo drift
      from other in-flight work, out of this ticket's scope.
    - `tests/test_settings_encryption_migration_ui.py` hangs/times out when
      run as part of the full suite (passes in isolation, 8/8). Confirmed
      via `git stash` that this hang reproduces identically on `dev` HEAD
      without this ticket's test diff — pre-existing flakiness, unrelated
      to Import button wiring, out of scope per Step 1 scope-out.
  - [x] No user-visible Import behavior changed, per DoD: "No change to
    user-visible Import behavior is required when the button is already
    wired correctly."
- [x] **STEP 5: Code Cleanup**
  - [x] Reviewed the only code artifact this ticket produced — the new
    `TestImportButtonWiring` class in `tests/test_environment_list_widget.py`
    — for naming, duplication, dead code, and style; no issues found (matches
    the established `test_collection_export_ui.py` button-wiring-lock
    pattern; reuses the file's `_make_widget` helper; no unused
    imports/vars, no debug prints, no commented-out code).
  - [x] Ran `flake8 --jobs=1` against the file: 10 pre-existing `E402`
    warnings (repo-wide convention from `pytestmark` timeout placement,
    present in 200+ test files; `make lint` doesn't even cover `tests/`),
    zero other findings. Left as-is per "small, safe fixes only" — not a
    defect of this diff.
  - [x] `tests/test_environment_list_widget.py`: 10/10 passed. Module-level
    `pytestmark = pytest.mark.timeout(60)` covers the new class.
  - [x] See `ai-tasks/PYPOST-1001/40-code-cleanup.md` for full report.
- [x] **STEP 6: Observability**
  - [x] Assessed against `.cursor/rules/50-observability.mdc`: the
    Completion Criteria gate logging/metrics on key operations and
    critical indicators "if applicable to the project" — this ticket
    changed zero production code (only added
    `TestImportButtonWiring::test_mouse_click_on_import_button_starts_import`
    to `tests/test_environment_list_widget.py`), so there is no new
    execution path, error path, or metric to instrument. Determined N/A,
    consistent with the same determination on sibling verification-lock
    tickets on this parent (PYPOST-1006, PYPOST-1008, PYPOST-1009).
  - [x] Confirmed the new test never exercises production logging: it
    patches `EnvironmentListWidget.import_environments` itself before
    constructing the widget, so the click reaches the mock, not the real
    method body (and its existing `environment_import_file_invalid` /
    `environment_import_completed` log lines).
  - [x] See `ai-tasks/PYPOST-1001/50-observability.md` for full report.
- [x] **STEP 7: Review and Technical Debt**
  - [x] Holistic self-review of the whole ticket's deliverable (the single
    `TestImportButtonWiring` test class, +19 lines, zero production
    changes) against the Step 1 Definition of Done: every DoD bullet
    confirmed met, no gap found between delivered diff and ticket scope.
  - [x] No shortcuts, code-quality issues, missing tests (in-scope), or
    performance concerns identified — genuine "no technical debt from this
    ticket" outcome, consistent with pure verification-lock work that found
    no defect.
  - [x] Recorded 3 out-of-scope follow-up items surfaced during Step 4
    verification (not this ticket's to fix): the repo-wide flake8 E402
    `pytestmark`-placement convention (Low), the 9 pre-existing full-suite
    audit/baseline test failures (Medium), and the
    `test_settings_encryption_migration_ui.py` full-suite hang
    (Medium-High) — each with enough detail for a future ticket, per the
    rule file's guidance on out-of-scope discoveries.
  - [x] See `ai-tasks/PYPOST-1001/60-tech-debt.md` for full report.
- [x] **STEP 8: Dev Docs**
  - [x] Located the existing coverage doc for this area:
    `doc/dev/environments_dialog.md` § "Import environments (PYPOST-986)"
    already carries a running "Tests:" paragraph that lists each Import
    test-coverage addition by ticket (PYPOST-986 base coverage, PYPOST-999
    Overwrite × Hidden, PYPOST-1000 presenter wiring lock). This is the
    project's established pattern for documenting Import test coverage —
    no separate index/table of "button click tests exist for X/Y widgets"
    exists elsewhere in `doc/dev/` (checked `gui_testing.md`, `testing.md`,
    `collection_export.md` for a generic wiring-lock index; each feature
    doc keeps its own coverage paragraph/table instead of a central list).
  - [x] Appended a sentence to that paragraph describing the new
    `TestImportButtonWiring::test_mouse_click_on_import_button_starts_import`
    click-wiring lock (`QTest.mouseClick` on `ENV_IMPORT_BUTTON` →
    `import_environments` invoked), distinguishing it from the existing
    direct-call tests, and noting it was verified against current code
    with zero production changes.
  - [x] No new `doc/dev/<feature-name>.md` file created: the rule file's
    "create a new file only if no relevant file exists" branch does not
    apply here — a relevant, actively-maintained file (`environments_dialog.md`)
    already exists and already documents Import test coverage ticket-by-ticket.

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (verification/testing debt within the existing Python codebase; no new
language or stack introduced).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1001/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1001/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1001/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1001/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1001/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`
