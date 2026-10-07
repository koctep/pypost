# PYPOST-1287: Code Cleanup Report

## Linter Fixes

- `make lint` (flake8 on `pypost/`, Markdown lint, relative link check): clean. No findings to
  fix. The task changes only tests and Markdown, so flake8's `pypost/` scope does not cover them.
  Line length was checked by hand: every changed line is 100 characters or fewer.

## Code Formatting

Formatting changes:

- [x] Automatic code formatting: not needed. The changed code already matches the module style.
- [x] Indentation and alignment fixes: none needed.
- [x] Line length correction: none needed. No line is over 100 characters in
      `tests/test_pypost_1077_verification_artifacts.py`,
      `tests/test_pypost_1287_failing_repro.py` or
      `doc/dev/verification_artifact_contracts.md`.

## Code Cleanup

Cleanup actions performed:

- Naming: in `tests/test_pypost_1077_verification_artifacts.py`, renamed the
  `_module_count_errors` parameter `n` to `module_count`. The parameter is only passed by
  position, and the messages are unchanged.
- Stale docstring: the `tests/test_pypost_1287_failing_repro.py` module docstring described the
  pinned-snapshot contract in the present tense. It now says that was the state before the fix.
  The repro's assertions, regexes and helpers are untouched.
- Removed unused imports: 0. All imports are used, including `Sequence`, `DialogModule`, `Path`
  and `re`.
- Removed unused variables or helpers: 0. All repro helpers and constants are used.
- Removed commented-out code: none found.
- Removed debug prints: none found (no `print(` or `breakpoint`).

## Validation Results

- [x] Targeted tests pass after cleanup:
      `make test WORKERS=1 PYTEST_ARGS='tests/test_pypost_1287_failing_repro.py
      tests/test_pypost_1077_verification_artifacts.py tests/test_pypost_1259_failing_repro.py
      tests/test_dialogs_audit.py -q'` (4/4 files passed). After the docstring edit, the
      first two files were re-run and passed (2/2).
- [x] `make typecheck`: mypy baseline OK (181 known errors, no regression).
- [x] `make verify-ai-tasks`: OK (387 completed tasks; 2 grandfathered legacy gaps).
- [x] `make check` (run once, full suite): 368 files, 361 passed, 1 failed, 6 skipped
      (wall time 288 s). `lint` passed. The `test` target failed, so `make` stopped before
      `verify-ai-tasks`, which passed when run on its own (see above). The only failure:
  - `tests/test_pytest_exit_policy.py` (worker timeout at 120 s):
    `::test_make_test_fails_closed_when_parallel_runner_is_missing` failed after 60 s, and
    `::test_make_test_cov_fails_closed_when_parallel_runner_is_missing` hung. This is the filed
    pre-existing issue **PYPOST-1299**. It is not related to this task (Makefile/runner policy).
  - No failures outside the filed pre-existing set, so no new triage was needed.
- [x] All tests have explicit timeout markers (`pytestmark = pytest.mark.timeout(10)` in both
      changed test modules).
- [x] No merge conflicts.
- [x] Syntax is valid (modules collect and run).
- [x] Types: no new mypy findings (the test modules are outside the mypy scope; annotations are
      complete).

## Notes

- No behaviour change: the validator rules R1-R7, the message shapes and the repro are as
  accepted in Step 4.
- DoD 8 is met: the targeted `make test` passes, and `make check` has no failure outside the
  filed pre-existing set (PYPOST-1299).
