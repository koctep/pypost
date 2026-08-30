# PYPOST-1198: Code Cleanup Report

## Linter Fixes

`make lint`'s `flake8` target only scopes `pypost/`, so the two touched files
(`scripts/run_parallel_tests.py`, `tests/test_run_parallel_tests.py`) were linted directly with
the project's flake8 config (`max-line-length = 100`, `extend-select = T201` for print
statements):

```
.venv/bin/python -m flake8 --jobs=1 scripts/run_parallel_tests.py tests/test_run_parallel_tests.py
```

- No warnings or errors reported. Nothing to fix.

`scripts/check_mypy_baseline.py` was also run for completeness. It covers `pypost/core`,
`pypost/models`, and `pypost/ui` only (not `scripts/` or `tests/`), so it is out of scope for
this diff; it reported 4 newly-resolved baseline errors and pre-existing unrelated failures in
`pypost/ui/presenters/*` and `pypost/ui/widgets/*` (websocket/mcp connection typing), none of
which touch the files changed in this task.

## Code Formatting

Applied formatting changes:
- [x] Automatic code formatting — diff already matches project style (checked by eye and flake8)
- [x] Indentation and alignment fixes — none needed
- [x] Line length correction — all added lines checked against 100-char limit; longest added
  line (`config.worker_timeout,`) is well under the limit; no changes needed

## Code Cleanup

Cleanup actions performed:
- Removed unused imports: 0 (none introduced)
- Removed unused variables: 0 (none introduced)
- Removed commented-out code: none present
- Removed debug prints: none present (flake8 `T201` confirms no `print()` calls added)

The diff is a 2-line change: one log format string / positional arg addition in
`scripts/run_parallel_tests.py::run_parallel_tests`, and one new assertion in
`tests/test_run_parallel_tests.py::test_parallel_runner_logs_run_config`. No dead code.

## Validation Results

Validation results:
- [x] All tests passed — `tests/test_run_parallel_tests.py` (21 tests) passed via
  `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_run_parallel_tests.py -q`
- [x] All tests have explicit timeout markers — module-level
  `pytestmark = pytest.mark.timeout(60)` (line 32) applies to the touched test
  `test_parallel_runner_logs_run_config`
- [x] No merge conflicts
- [x] Syntax is valid (tests import and run cleanly)
- [ ] Types are correct (if applicable) — N/A for `scripts/`/`tests/`, not covered by the
  project's mypy baseline gate

## Notes

Pre-existing `PytestCollectionWarning` for `TestStatus(str, Enum)` (has an `__init__`
constructor, collected because its name starts with `Test`) appears in the suite's warning
summary; it is unrelated to this change and predates this task.

Pre-existing mypy baseline failures in `pypost/ui/presenters/*` and
`pypost/ui/widgets/mcp_client|websocket/*` are unrelated to this task's diff (which only touches
`scripts/run_parallel_tests.py` and `tests/test_run_parallel_tests.py`, neither of which is in
mypy's scoped paths) and are not addressed here.
