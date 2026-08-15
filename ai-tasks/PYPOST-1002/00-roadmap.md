# Roadmap: PYPOST-1002

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1002/10-requirements.md` written, grounded in the
    real code: `_resolve_import_conflicts`
    (`pypost/ui/widgets/environments/environment_list_widget.py:342-359`),
    `generate_import_copy_name` (`pypost/core/import_conflicts.py:21-29`),
    and the existing two-conflict test
    (`tests/test_environment_list_widget.py:123-144`,
    `test_apply_to_all_conflicts_prompts_only_once`). Approval treated as
    granted under sprint-task-runner autonomy (same as sibling PYPOST-1001).
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1002/20-architecture.md` written: plan is one new
    test method per gap (not parametrization/edits of the existing
    2-conflict/`(2)` tests), placed alongside the existing siblings in
    `TestImportEnvironments` (`tests/test_environment_list_widget.py`) and
    `TestGenerateImportCopyName` (`tests/test_environment_import.py`). No
    production code changes anticipated — same pattern as sibling
    PYPOST-1001. Approval treated as granted under sprint-task-runner
    autonomy.
- [x] **STEP 3: Failing Repro Test**
  - [x] Execution: added
    `tests/test_environment_list_widget.py::TestImportEnvironments::test_apply_to_all_conflicts_applies_to_third_and_later_conflicts`
    (3 conflicting names, asserts `prompt_import_conflict` called once and all
    three environments unchanged under SKIP) and
    `tests/test_environment_import.py::TestGenerateImportCopyName::test_returns_next_numbered_copy_when_first_two_taken`
    (seeds "Copy of Dev" and "Copy of Dev (2)" as taken, asserts result is
    "Copy of Dev (3)"). Both PASSED immediately against current code (see run
    output) — expected verification-lock outcome per architecture doc, not a
    classic red-then-fix cycle. No production code touched.
  - [x] Review: confirmed both are genuine, non-tautological locks by
    temporarily breaking the underlying production logic (apply-to-all
    carry, SKIP-mutates-state, `while`→`if` in the copy-name generator) and
    observing each targeted test fail, then reverting (verified `pypost/`
    diff clean afterward). Two informational, non-blocking gaps noted for
    the record: test 1 shares a SKIP-default blind spot with its 2-conflict
    sibling (pre-existing pattern, out of scope); test 2 proves "at least
    one increment" rather than strictly "loop re-checks," which only
    diverges at `(4)+`, explicitly out of this ticket's scope per the
    requirements Q&A. Neither blocks Step 4.
- [x] **STEP 4: Development**
  - [x] Re-ran `tests/test_environment_list_widget.py` and
    `tests/test_environment_import.py` in full (26 tests, `.venv/bin/python
    -m pytest`): all pass, including both Step 3 locks
    (`test_apply_to_all_conflicts_applies_to_third_and_later_conflicts`,
    `test_returns_next_numbered_copy_when_first_two_taken`). Broader sanity
    pass `-k "environment" -m "not slow"`: 230 passed, 1986 deselected, 0
    failed.
  - [x] Re-verified `_resolve_import_conflicts`
    (`pypost/ui/widgets/environments/environment_list_widget.py:342-359`)
    and `generate_import_copy_name`
    (`pypost/core/import_conflicts.py:21-29`) against the Step 1 DoD: the
    `for i, name in enumerate(conflicts)` loop has no early exit/break and
    applies `apply_to_all` to every subsequent conflict once set; the
    `while f"{candidate} ({suffix})" in existing_names: suffix += 1` loop
    has no bound other than the membership check and correctly advances
    past `(2)` to `(3)`. Both already satisfy DoD items 1-2.
  - [x] **No production code changed** — confirmed expected outcome, same
    pattern as sibling PYPOST-1001. `git status` shows no modifications
    under `pypost/`; only the two new test methods added in Step 3 remain
    as the diff. No defect found, so DoD item 5's fix/record branch does
    not apply.
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1002/40-code-cleanup.md` written: ran
    `.venv/bin/python -m flake8` against both changed test files; the two new
    test methods introduce zero new lint findings (pre-existing `E402`
    warnings on both files' `pytestmark`-before-imports lines confirmed
    identical before/after this ticket's diff, out of scope). No line-length,
    unused-import/variable, debug-print, dead-code, or duplication issues.
    Naming and placement mirror each new test's nearest sibling per the Step
    2 architecture. Both files' module-level `pytestmark =
    pytest.mark.timeout(60)` covers the new methods. Full re-run: 26 passed,
    0 failed. No production code touched.
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1002/50-observability.md` written: assessed against
    `.cursor/rules/50-observability.mdc` and determined N/A — confirmed via
    `git diff --stat -- pypost/` (empty) that zero production code changed
    (only the two new test methods from Step 3, unmodified through Steps
    4-5). The rule's Completion Criteria gate logging/metrics on "key
    operations"/"critical indicators... if applicable to the project"; no
    new or changed production execution path exists to instrument. Same
    precedent and reasoning as sibling PYPOST-1001
    (`ai-tasks/PYPOST-1001/50-observability.md`) and PYPOST-1006/1008/1009
    on the same parent (PYPOST-986). Existing logging in
    `environment_list_widget.py` (`environment_import_completed`,
    `environment_import_file_invalid`) already covers the import path the
    new tests exercise and is unmodified; `import_conflicts.py` is a pure
    function with no I/O and no logging to add.
- [x] **STEP 7: Review and Technical Debt**
  - [x] `ai-tasks/PYPOST-1002/60-tech-debt.md` written: holistic self-review
    confirmed the diff (2 test methods, 0 production changes) satisfies all
    6 Step 1 DoD items; reconfirmed 26/26 targeted tests pass; no shortcuts,
    code-quality issues, missing tests, performance concerns, or DoD
    deviations found within scope. Parent-ticket check (informational):
    PYPOST-986's `60-tech-debt.md` Follow-up Tasks list has exactly 4
    entries (PYPOST-999, -1000, -1001, -1002); the other three are all
    closed (roadmaps show all 8 steps `[x]`), so once this ticket reaches
    Step 8 all four are closed — no PYPOST-986-sourced follow-up is left
    unticketed. Two non-blocking informational gaps from Step 3 (SKIP-only
    coverage of the apply-to-all decision at 3+ conflicts;
    "(3)"-not-"(4)" strict-loop-recheck coverage) were recorded as two Low
    priority Follow-up Tasks, consistent with sibling PYPOST-1001's
    precedent of recording out-of-scope discoveries rather than silently
    dropping them.
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/environments_dialog.md` § Import environments
    (PYPOST-986) "Tests:" paragraph: appended a sentence describing
    PYPOST-1002's two new tests (3+-conflict apply-to-all lock in
    `test_environment_list_widget.py::TestImportEnvironments`,
    `generate_import_copy_name` reaching `"(3)"` in
    `test_environment_import.py::TestGenerateImportCopyName`), following the
    same ticket-by-ticket pattern already used for PYPOST-999/1000/1001 in
    that paragraph. This completes the record for all four of PYPOST-986's
    follow-ups. No new doc structure invented; no production code changed.

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (verification/testing debt within the existing Python codebase; no new
language or stack introduced).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1002/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1002/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1002/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1002/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1002/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`
