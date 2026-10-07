# PYPOST-1235: Code Cleanup Report

## Scope

Files cleaned (the only two files touched by this task):

- `tests/test_display_role_scan_ownership.py` (Step 4 change to `_module_all_exports` and its
  caller)
- `tests/test_display_role_scan_ownership_all_exports.py` (new, 16 tests)

No change to behaviour, `pypost/`, `doc/`, or the repro/independent/aggregate/discoverability
files. There are no new `def` in `tests/test_display_role_scan_ownership.py`, so the
discoverability region markers (AC-8) are unaffected.

## Linter Fixes

- `make lint` runs flake8 only on `pypost/` (gap tracked in PYPOST-1303). It does **not** lint
  `tests/`. Both files were checked by inspection against `/home/src/.flake8`
  (`max-line-length = 100`, `extend-select = T201`):
  - Line length: 0 lines over 100 in either file.
  - Trailing whitespace / tabs: none. Both files end with a newline.
  - `print(` / `breakpoint(` / `pdb` (T201): none.
  - Unused imports: none. Every import in both files is referenced.
- No linter errors needed fixing.

## Code Formatting

- [x] Automatic code formatting: not applicable. The repo has no formatter target, and the
  existing layout already matches the surrounding code.
- [x] Indentation and alignment fixes: none needed
- [x] Line length correction: none needed (all lines are 100 characters or fewer)

## Code Cleanup

- Removed unused imports: 0
- Removed unused variables: 0
- Removed commented-out code: none present
- Removed debug prints: none present
- Docstrings (`tests/test_display_role_scan_ownership_all_exports.py`):
  - The module docstring described the pre-fix reader in the present tense ("reads only the
    plain spelling and returns `set()`"). That stopped being true after Step 4, so it is now
    rephrased in the past tense ("Before the fix, ... read only ...").
  - Added a one-line docstring to the `_tree_index_with` helper.
- `tests/test_display_role_scan_ownership.py`: no change needed. The Step 4 diff already has an
  accurate docstring, explicit `targets`/`value` annotations, and no dead code.

## Validation Results

- [x] All tests passed: `make test PYTEST_ARGS="tests/test_display_role_scan_ownership_all_exports.py
  tests/test_display_role_scan_ownership.py tests/test_display_role_scan_ownership_repro.py
  tests/test_display_role_scan_ownership_independent_repro.py
  tests/test_display_role_scan_ownership_aggregate_repro.py
  tests/test_display_role_scan_ownership_discoverability.py -p no:randomly -q"` → 6/6 files
  passed, 0 failed
- [x] All tests have explicit timeout markers: module `pytestmark = pytest.mark.timeout(10)` in
  both files
- [x] No merge conflicts
- [x] Syntax is valid (collected and run)
- [x] Types are correct: `make typecheck` → "mypy baseline OK". That gate covers only
  `pypost/core`, `pypost/models`, and `pypost/ui`, so the test files were checked by inspection.
  `set[str] | None` is narrowed by `assert tree_exports is not None` before `issubset` and
  `sorted`.
- `make lint` → flake8 (`pypost/`) OK, Markdown lint OK, relative link check OK

## Notes

- `tests/` is outside the `make lint` (flake8) scope, tracked in PYPOST-1303, and outside the
  `make typecheck` scope. The checks above were done by inspection.
- `tests/test_pytest_exit_policy.py` fails before and after this task (PYPOST-1299). This is not
  a gap in this task, and that file was not run in this step.
