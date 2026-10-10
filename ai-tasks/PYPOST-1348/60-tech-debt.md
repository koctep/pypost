# PYPOST-1348: Technical Debt Analysis

## Shortcuts Taken

No production or packaging shortcuts were taken. The implementation strictly adheres
to the architectural decisions approved in `20-architecture.md`:
- Explicit package discovery is used instead of wildcard heuristics, ensuring exact
  mapping of all 18 application packages and `pypost.bundled_examples`.
- `examples/` remains the single canonical source of truth for official example
  collections, environments, and metadata; no duplicate copies or parallel trees
  were introduced.
- Package data declarations in `pyproject.toml` explicitly enumerate required file
  patterns (`pypost-library.yaml`, `builtin-collections.yaml`, `README.md`,
  `collections/*.json`, `environments/*.json`), ensuring forward compatibility with
  PYPOST-1350 without relying on loose globs or build hacks.
- A standalone, typed verification script (`scripts/check_package_data.py`) was introduced
  and integrated into Make (`make check-package-data` and `make test-slow`), ensuring
  real built wheels are validated byte-for-byte against the canonical source tree.
- The installation seed helpers in `tests/makefile_test_helpers.py` were upgraded to
  strictly validate that all declared packages, mapped source directories, initializers,
  and package-data files exist, failing closed on missing directories rather than silently
  skipping them.

## Code Quality Issues

No critical code quality issues or architectural compromises were identified in the
implemented solution:
- All new and modified Python files (`scripts/check_package_data.py`,
  `tests/test_bundled_examples_packaging.py`, `tests/test_package_data_wheel.py`,
  `tests/makefile_test_helpers.py`, `tests/test_makefile_install_seed_contract.py`)
  pass `make lint` (flake8) and `make typecheck` (mypy baseline gate).
- Line length across all modified and newly created files is strictly kept within
  100 characters.
- In `scripts/check_package_data.py`, zip archive traversal and path escape prevention
  are explicitly implemented and tested (`test_inspector_rejects_manifest_escape`).
- Potential minor refinement: If additional subpackages are added to `pypost/` in the
  future, the explicit package list in `pyproject.toml` must be manually updated.
  However, this is intentional design: `tests/test_bundled_examples_packaging.py`
  specifically enforces that any new package with `__init__.py` under `pypost/` must be
  declared in `pyproject.toml`, preventing accidental package omissions upon release.

## Missing Tests

No missing test scenarios remain for the scope of PYPOST-1348:
- Fast packaging declaration contracts (`tests/test_bundled_examples_packaging.py`)
  verify package lists, source mappings, required resource coverage, and future
  Built-in declaration patterns.
- Installation seed contracts (`tests/test_makefile_install_seed_contract.py`) test
  mapped package data resolution, initializers inclusion, fail-closed handling on
  missing source directories, and complete committed seed coverage.
- Wheel inspection contracts (`tests/test_package_data_wheel.py`) test offline missing-member
  detection, byte mismatch detection, path traversal rejection, CLI exit codes, and slow
  real-wheel verification via Make.
- All test files and test cases have explicit timeout markers per `do-testing`
  (`pytestmark = pytest.mark.timeout(30)` in packaging, seed, and wheel modules;
  `@pytest.mark.timeout(180)` on slow real-wheel integration test).

## Performance Concerns

- Build and packaging verification: Running `make check-package-data` requires building
  an isolated wheel in a temporary directory via `pip wheel --no-deps`. This takes
  approximately 10–15 seconds due to setuptools build execution. To preserve fast test suite
  responsiveness, this target is excluded from `make test` / `make check` and placed
  in the slow verification tier (`make test-slow`).
- Fast test suite overhead: Fast unit tests (`test_bundled_examples_packaging.py` and
  `test_package_data_wheel.py` offline tests) execute in ~1–3 seconds using `tomllib` and
  in-memory zip inspection without invoking pip or setuptools builds.

## Follow-up Tasks

All task-specific goals have been achieved. The following pre-existing baseline issues
and follow-up items are tracked:

### PYPOST-1358 — Native UI environment-list teardown crash
- **Classification**: NON-BLOCKER — pre-existing
- **Status**: Filed as [PYPOST-1358](https://pypost.atlassian.net/browse/PYPOST-1358), outside sprint/epic.
- **Description**: Environment list widget native teardown crash (SIGSEGV / SIGBUS) observed
  after all 13 test assertions pass in `tests/test_environment_list_ui.py`. Verified on clean
  baseline `1e64239f` (1/3 pass, 2/3 crash with SIGBUS/SIGSEGV).

### PYPOST-1359 — Dev-lock check stale with CI-pinned uv
- **Classification**: NON-BLOCKER — pre-existing
- **Status**: Filed as [PYPOST-1359](https://pypost.atlassian.net/browse/PYPOST-1359), outside sprint/epic.
- **Description**: Dependency lock check (`make check-lock` / `make check-lock-all`) reports
  stale lock against CI-pinned `uv` 0.11.31 on clean baseline `1e64239f`. Development inputs
  and lockfiles remain untouched in PYPOST-1348.

### PYPOST-1360 — Install-smoke timeout on clean base
- **Classification**: NON-BLOCKER — pre-existing
- **Status**: Filed as [PYPOST-1360](https://pypost.atlassian.net/browse/PYPOST-1360), outside sprint/epic.
- **Description**: Slow installation smoke test `tests/test_makefile_install_smoke.py` times
  out at 180 seconds on clean baseline `1e64239f` (179.91s baseline vs 179.77s current).
  Tracked separately outside sprint and epic.

### Future Epic Stories (PYPOST-1335)
- **PYPOST-1349**: Implement runtime package resource loader resolving `pypost.bundled_examples`.
- **PYPOST-1350**: Add Built-in collections declaration (`builtin-collections.yaml`) to `examples/`.
