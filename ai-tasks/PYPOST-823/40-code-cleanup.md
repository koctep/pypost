# PYPOST-823: Code Cleanup Report

## Linter Fixes

- Fixed: flake8 `E402` (module-level imports after `pytestmark`) by moving all
  imports above the module `pytestmark` assignment — matches preferred
  `do-testing.md` / cleaner test modules.
- `make lint` (flake8 on `pypost/`): clean (no production code changes in this
  task).
- Scoped flake8 on `tests/test_env_storage_responsiveness.py`: clean (exit 0).

## Code Formatting

Applied formatting changes:

- [x] Import order normalized (stdlib → third-party → local → `pytestmark`)
- [x] Indentation and alignment verified
- [x] Line length within 100 characters (project / `.flake8` limit)

## Code Cleanup

Cleanup actions performed:

- Removed unused imports: 0 (already clean after Step 3 dropped
  `QApplication` / local `qt_app` fixture)
- Removed unused variables: 0
- Removed commented-out code: none present
- Removed debug prints: none present
- Added `Callable[[], bool]` annotation on `_process_until` predicate
- Simplified `open(..., "r")` to default text mode in persistence assertion

## Validation Results

Validation results:

- [x] Scoped tests passed:
  `make test PYTEST_ARGS="tests/test_env_storage_responsiveness.py -v"`
  → **5 passed**
- [x] All tests have explicit timeout markers (`pytestmark = pytest.mark.timeout(120)`)
- [x] No merge conflicts
- [x] Syntax is valid (flake8 clean on scoped file)
- [x] Types annotated where touched (`Callable` on helper)

## Notes

- Scope is test-only (`tests/test_env_storage_responsiveness.py`). `make lint`
  covers `pypost/` and remained clean.
- Hang-regression tests intentionally wait ~300ms; wall-clock assertions keep
  failure under 2s.
