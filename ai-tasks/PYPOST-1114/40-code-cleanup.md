# PYPOST-1114: Code Cleanup Report

Scope: files touched by this task only.

- `pypost/core/key_sources/file_cache.py` (modified in Step 4)
- `tests/test_pypost_1114_failing_repro.py` (new in Step 3)

## Linter Fixes

- `make lint` (flake8 on `pypost/` + Markdown/link checks): clean, no fixes needed in
  `file_cache.py`.
- `tests/test_pypost_1114_failing_repro.py` is **outside `make lint` scope**: the `lint` target
  runs `flake8 --jobs=1 pypost/` with no path variable, so no make target lints `tests/`. Per
  AGENTS.md (make-only), flake8 was not invoked directly. The file was checked by inspection against
  `.flake8` (`max-line-length = 100`, `extend-select = T201`): no line over 100
  characters, no trailing whitespace, no `print`/debug calls, all imports used. No violations
  found.

## Code Formatting

- [x] Automatic code formatting — not applicable (project has no formatter target); manual
  PEP 8 check
- [x] Indentation and alignment fixes — none needed
- [x] Line length correction — none needed (all lines at most 100 characters)

## Code Cleanup

- Removed unused imports: 0 (none found)
- Removed unused variables: 0 (none found)
- Removed commented-out code: none present
- Removed debug prints: none present
- Docstrings (test file):
  - Module docstring said "Failing repro tests"; the tests are green after Step 4, so it now says
    "Regression tests" and notes they began as the Step 3 repro.
  - Added one-line docstrings to the private helpers `_counting_text_loader` and
    `_registry_json`.
- Organization (test file): moved helper `_registry_json` up next to the other module helpers
  so it is no longer defined between two tests. Test bodies are unchanged.
- `file_cache.py`: no changes. Docstrings already cover the module, class and `get()`; the
  digest helper is private and never logged. The private alias `_clear()` that delegates to
  `clear()` predates this task and is left as-is (out of scope).

## Validation Results

- [x] All tests passed — `make test PYTEST_ARGS="tests/test_pypost_1114_failing_repro.py
  tests/test_key_sources_chain_coverage.py tests/test_key_sources_secret_store.py
  -p no:randomly -q"`: 3 files passed, 0 failed
- [x] All tests have explicit timeout markers — module-level `pytestmark =
  pytest.mark.timeout(30)` in the new test file
- [x] No merge conflicts — `git diff --check` clean
- [x] Syntax is valid — `make lint` OK
- [x] Types are correct — `make typecheck`: mypy baseline OK (181 known errors, no new ones)

## Notes

- The full suite was not run. `tests/test_pytest_exit_policy.py` already fails before this task
  (Jira PYPOST-1299) and is unrelated to this change.
- Tech-debt candidate for Step 7: `make lint` covers only `pypost/`, so new test files
  (including `tests/test_pypost_1114_failing_repro.py`) are never flake8-checked by any make
  target.
- Behavior is unchanged: production code was not edited, and the test edits only touch
  docstrings and the order of helper definitions.
