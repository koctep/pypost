# PYPOST-872: Code Cleanup Report

## Linter Fixes

- No flake8 findings in production packages (`make lint` on `pypost/`
  exits 0). Makefile / test-only change; no Python package edits.

## Code Formatting

- [x] Line length ≤ 100 on edited Makefile help comments and test
  docstrings
- [x] Indentation and alignment unchanged for existing pytest style
- [x] No autoformatter required beyond project norms

## Code Cleanup

Cleanup actions performed:
- Removed unused imports: 0
- Removed unused variables: 0
- Removed commented-out code: none
- Removed debug prints: none
- Narrowed `test_runtime_targets_depend_on_marker_only` from
  `run`/`test`/`lint` to `run`/`lint` so it matches ENABLE
- Replaced obsolete
  `test_test_fails_without_pytest_in_bare_venv` with
  `test_test_succeeds_from_bare_venv_via_venv_test`

## Validation Results

Validation results:
- [x] `tests/test_makefile.py` — 39 passed, 1 deselected (slow)
- [x] Explicit timeout: module `pytestmark = pytest.mark.timeout(120)`
- [x] No merge conflicts in touched files
- [x] Syntax valid (Makefile + pytest collect)
- [ ] Types N/A (no typed production API change)

## Notes

- Dual `venv-test` then `venv-otel` pip on each `make test` is accepted
  per architecture (same non-stamp pattern as pre-existing `venv-otel`);
  stamp caching deferred to tech-debt follow-up.
- Docs updates land in Step 8.
