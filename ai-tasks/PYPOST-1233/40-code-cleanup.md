# PYPOST-1233: Code Cleanup Report

## Linter Fixes

Step 4's mechanical fix (relocating each file's `pytestmark = pytest.mark.timeout(30)` line to
directly below the last top-level import) already resolved all E402 findings:

- Fixed: `tests/test_examples_modernization.py` — 4 E402 findings, now 0
- Fixed: `tests/test_examples_modernization_repro.py` — 3 E402 findings, now 0
- Fixed: `tests/test_ui_library_manager.py` — 10 E402 findings, now 0
- Fixed: `tests/test_ui_library_manager_repro.py` — 3 E402 findings, now 0

Confirmed via `.venv/bin/python -m flake8 --select=E402` on all 4 files: 0 findings (exit code 0).

No further linter fixes were required or made by this step (see Notes for scope boundary).

## Code Formatting

Applied formatting changes:
- [x] Automatic code formatting — N/A, no reformatting needed; the diff for each file is exactly
      a 2-line move (remove `pytestmark = ...` from its old spot, re-add it after the last import)
- [x] Indentation and alignment fixes — N/A, none needed
- [x] Line length correction — N/A for the moved line itself (well under 100 chars); pre-existing
      E501 findings elsewhere in these files are out of scope (see Notes)

## Code Cleanup

Cleanup actions performed:
- Removed unused imports: 0 (none removed — see Notes on pre-existing F401 findings)
- Removed unused variables: 0
- Removed commented-out code: none found
- Removed debug prints: none found

## Validation Results

Validation results:
- [x] All tests passed — `make test PYTEST_ARGS="tests/test_lint_pytestmark_e402.py"` PASSED
      (1/1, 3.93s)
- [x] All tests have explicit timeout markers — unchanged; each file still carries
      `pytestmark = pytest.mark.timeout(30)`, just relocated below the imports
- [x] No merge conflicts — none present
- [x] Syntax is valid — flake8 parsed all 4 files without syntax errors
- [x] Types are correct (if applicable) — N/A, no type changes

## Notes

Ran full-default `flake8` (not just `--select=E402`) against the 4 files to check for anything
newly introduced by Step 4's line move:

- Before the move (checked against the pre-fix versions via `git show HEAD:<path>`), the 4 files
  had 20 E402 findings plus 30 pre-existing non-E402 findings (F401 unused imports, E501 lines
  over 100 chars, W293 whitespace-only blank lines).
- After the move, the same 4 files have 0 E402 findings and the identical set of 30 non-E402
  findings (only their reported line numbers shifted, by exactly the 2-line displacement of the
  relocated `pytestmark` statement).
- Conclusion: Step 4's change introduced zero new warnings of any kind. The 30 remaining findings
  (F401 in `test_ui_library_manager.py`/`test_ui_library_manager_repro.py`/
  `test_examples_modernization.py`/`test_examples_modernization_repro.py`, E501 long docstring/
  comment lines, W293 in `test_ui_library_manager_repro.py`) are pre-existing and unrelated to
  PYPOST-1233's E402 scope. Per the task's explicit 1-story-point, mechanical, proportionate-scope
  instruction, they are left untouched here and not tracked as new debt from this ticket.
- The moved `pytestmark` line itself is clean: no formatting, length, or lint issues.
