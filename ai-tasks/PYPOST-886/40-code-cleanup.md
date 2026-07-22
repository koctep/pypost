# PYPOST-886: Code Cleanup Report

## Linter Fixes

- No production (`pypost/`) changes; lint surface is test-only.
- Removed unused `QApplication` / `sys` imports from migrated modules after
  dropping local lifecycle ownership.
- Removed leftover `_app = None` globals after deleting `_get_app()` helpers.
- Restored blank-line spacing compacted during batch migration.

## Code Formatting

Applied formatting changes:
- [x] Automatic code formatting (blank-line normalization between top-level
  classes / fixtures)
- [x] Indentation and alignment fixes (manual restore of `usefixtures` on
  scanner / bind-host classes after over-aggressive strip)
- [x] Line length correction (kept within 100 where touched)

## Code Cleanup

Cleanup actions performed:
- Removed unused imports: many (`QApplication` from modules that no longer
  construct it; `sys` where only used for `QApplication(sys.argv)`)
- Removed unused variables: leftover `_app` globals; unused inline `app = ...`
  in `test_worker_race.py`
- Removed commented-out code: none
- Removed debug prints: none
- Removed duplicate local `def qapp()` fixtures (~22 modules)
- Removed `setUpClass` `QApplication` ownership (~29 modules + special cases)

## Validation Results

Validation results:
- [x] Focused priority + related batches passed (`make test` with
  `PYTEST_ARGS`; **331 passed** including alignment guard + workers /
  presenters / editors + collection worker)
- [x] Suite inventory guard green:
  `tests/test_suite_qapp_alignment.py` (**19 passed**)
- [x] Inventory: **0** remaining `setUpClass`+`QApplication`; **0** remaining
  local `def qapp()`
- [x] All touched tests retain explicit timeout markers (`pytestmark` /
  per-test)
- [x] No merge conflicts
- [x] Syntax is valid
- [x] Types are correct (if applicable) — N/A for harness-only

## Notes

- `test_env_presenter.py` still embeds a subprocess child string that creates
  `QApplication` for hang canary isolation — intentional; not suite fixture
  ownership.
- Combining some large Qt modules in one pytest process occasionally segfaulted
  during agent runs; per-module runs stayed green (known Qt teardown sensitivity,
  not introduced as a product defect).
