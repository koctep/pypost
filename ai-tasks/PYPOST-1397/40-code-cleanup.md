# PYPOST-1397: Code Cleanup Report

## Linter Fixes

- None required: no application Python modules changed.
- Touched surfaces: `Makefile` (`lock-dev` `--upgrade`), `requirements-dev.txt`
  (regenerated), `doc/dev/setup.md` (operator note).

## Code Formatting

Applied formatting changes:
- [x] Automatic code formatting — N/A (no Python source edits)
- [x] Indentation and alignment fixes — Makefile continuation line aligned
- [x] Line length correction — Makefile recipe kept within project norms

## Code Cleanup

Cleanup actions performed:
- Removed unused imports: 0
- Removed unused variables: 0
- Removed commented-out code: none
- Removed debug prints: none

## Validation Results

Validation results:
- [x] Targeted repro passed:
      `make test PYTEST_ARGS='tests/test_lockfile_verification.py::test_repro_check_lock_dev_detects_no_drift -q'`
- [x] `make check-lock-dev` exit 0
- [x] All tests have explicit timeout markers (existing module `pytestmark`)
- [x] No merge conflicts
- [x] Syntax is valid (Makefile + lockfile)
- [x] Types are correct (N/A — no typed Python changes)

## Notes

- Drift check (`check-lock-dev`) intentionally unchanged; only lock generation and
  the committed lock artifact were updated.
- Sibling `lock` / `lock-otel` targets still omit `--upgrade`; tracked in
  `60-tech-debt.md`.
