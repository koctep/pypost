# PYPOST-1348: Code Cleanup Report

## Linter Fixes

Describe fixed linter errors and warnings:
- Fixed: Checked all modified and newly created files (`Makefile`, `pyproject.toml`,
  `examples/__init__.py`, `scripts/check_package_data.py`, `tests/makefile_test_helpers.py`,
  `tests/test_makefile_install_seed_contract.py`, `tests/test_bundled_examples_packaging.py`,
  `tests/test_package_data_wheel.py`) against static analysis and linting.
- Fixed: Shortened target description line in `Makefile` for `test-slow` from 117 characters
  to 98 characters to strictly adhere to the <= 100 character line length standard.
- Verified: `make lint` passes cleanly (flake8 on `pypost/`, doc markdown lint, doc links).
- Verified: `make typecheck` passes within baseline gate (`mypy baseline OK`).

## Code Formatting

Applied formatting changes:
- [x] Automatic code formatting
- [x] Indentation and alignment fixes (fixed `monkeypatch.setattr` argument list indentation
  in `tests/test_package_data_wheel.py` to use PEP 8 4-space hanging indent on separate lines)
- [x] Line length correction (all lines across Python scripts, test modules, TOML configuration,
  and new Makefile additions strictly within 100 characters)

## Code Cleanup

Cleanup actions performed:
- Removed unused imports: 0 (verified all imports in Python scripts and tests are actively
  referenced)
- Removed unused variables: 0 (verified all local and comprehension variables are required)
- Removed commented-out code: none present
- Removed debug prints: none present (the only `print()` statement in
  `scripts/check_package_data.py` is the functional CLI output used by `make check-package-data`)

## Validation Results

Validation results:
- [x] All tests passed (`make test WORKERS=1 PYTEST_ARGS="tests/test_bundled_examples_packaging.py
  tests/test_makefile_install_seed_contract.py tests/test_package_data_wheel.py"` passed 3/3 files)
- [x] All tests have explicit timeout markers (module-level `pytestmark = pytest.mark.timeout(30)`
  in packaging, seed, and wheel test suites; function-level `@pytest.mark.timeout(180)` on slow
  real-wheel test per `do-testing`)
- [x] No merge conflicts (clean branch based on HEAD)
- [x] Syntax is valid (all Python and TOML files parse cleanly)
- [x] Types are correct (if applicable) (`make typecheck` baseline OK)
- [x] Package data validation passes (`make check-package-data` verified all 29 canonical members
  in isolated wheel build)

## Notes

- All changes respect repository Make-only tooling standards.
- Pre-existing native teardown crash (SIGSEGV/SIGBUS in Qt environment-list test) and slow
  install-smoke timeout are tracked separately in Jira issues PYPOST-1358 and PYPOST-1360.
