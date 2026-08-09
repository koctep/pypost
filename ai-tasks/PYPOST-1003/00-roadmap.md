# Roadmap: PYPOST-1003

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_collection_import.py::TestPlanDuplicateNamesWithinFile::test_three_duplicate_names_report_two_renames_each`
    and `tests/test_environment_import.py::TestPlanImportDuplicateNamesWithinFile::test_three_duplicate_names_report_two_renames_each`
    — were red against the old dict-shape accumulator
    (`AssertionError: {'API': 'Copy of API (2)'} != [('API', 'Copy of API'),
    ('API', 'Copy of API (2)')]` and the `'Dev'` equivalent), confirming
    last-write-wins collapse of 3 same-named duplicates to a single entry.
    Turned green in STEP 4 after `renamed` became `list[tuple[str, str]]`.
- [x] **STEP 4: Development**
  - [x] Implemented `renamed` as `list[tuple[str, str]]` (was `dict[str, str]`) on
    `CollectionImportPlanResult` (`pypost/core/collection_import.py`) and
    `ImportPlanResult` (`pypost/core/environment_import.py`), so every rename
    pair is preserved instead of later duplicates overwriting earlier ones.
  - [x] Updated all write sites (`keep_both` closure in `collection_import.py`;
    in-file duplicate branch and KEEP_BOTH branch in `environment_import.py`'s
    `plan_import`) to `.append((name, new_name))`.
  - [x] Updated `format_collection_import_result` and `format_import_result`
    to iterate `for original, new_name in result.renamed:` instead of `.items()`.
  - [x] Updated 3 existing test assertions to the list-of-tuple shape and added
    a `test_three_duplicate_names_report_two_renames_each` regression test in
    each of `tests/test_collection_import.py` and `tests/test_environment_import.py`,
    proving 3 duplicates now report 2 rename pairs.
  - [x] Confirmed via grep that downstream consumers of `.renamed`
    (`pypost/ui/presenters/collection_import_actions.py`,
    `pypost/ui/widgets/environments/environment_list_widget.py`) only use
    `len()`/truthiness and needed no change.
  - [x] flake8 clean; both test files pass (38 passed).
- [x] **STEP 5: Code Cleanup**
  - flake8 clean on the 4 touched files (one pre-existing E402 in
    `tests/test_environment_import.py` at unrelated lines 12-25, verified via
    `git stash` to predate this diff — left untouched per scope).
  - No added line in the diff exceeds 100 chars; no unused imports/vars,
    commented-out code, or debug prints introduced.
  - Both new regression tests fall under their file's module-level
    `pytestmark = pytest.mark.timeout(...)`.
  - Re-ran `tests/test_collection_import.py tests/test_environment_import.py`
    -> 38 passed.
  - Report: `ai-tasks/PYPOST-1003/40-code-cleanup.md`.
- [x] **STEP 6: Observability**
  - Verified (via `grep -rn` across `pypost/`) that the only two consumers of
    `.renamed` outside the two core modules are
    `pypost/ui/presenters/collection_import_actions.py` (line ~93) and
    `pypost/ui/widgets/environments/environment_list_widget.py` (line ~334),
    both already logging `renamed_count=%d` via `len(result.renamed)` at INFO
    level — this automatically reports the corrected count with zero code
    change, since `len()` has identical count-of-events semantics on the new
    `list[tuple[str, str]]` as it (incorrectly) did on the old `dict[str, str]`.
  - Checked the pre-existing `..._file_parsed` INFO logs in both core modules
    (parse-time candidate/error counts) and confirmed they are unrelated to
    `.renamed` and out of scope.
  - No new logging or metrics added — none warranted for a pure
    reporting-accuracy fix with no new operation/error path.
  - Re-ran `tests/test_collection_import.py tests/test_environment_import.py`
    -> 38 passed (baseline confirmation; no code changed in this step).
  - Report: `ai-tasks/PYPOST-1003/50-observability.md`.
- [x] **STEP 7: Review and Technical Debt**
  - Reviewed implementation vs architecture/DoD; no blockers.
  - Report: `ai-tasks/PYPOST-1003/60-tech-debt.md`.
  - Step 3 sub-bullet updated to historical (tests green since STEP 4).
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/collection_import.md` and `doc/dev/environments_dialog.md`
    so `renamed` is documented as `list[tuple[str, str]]` (PYPOST-1003): one
    `(original, new_name)` pair per rename event, why not a dict, and how the
    summary / `renamed_count` consumers use `len()` over the list.
  - Added troubleshooting notes for a Renamed undercount on both import paths.

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (this is a bug fix within the existing Python codebase; no new language or stack introduced).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1003/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1003/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1003/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1003/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1003/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`
