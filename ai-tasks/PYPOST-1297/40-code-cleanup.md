# PYPOST-1297: Code Cleanup Report

Scope: `tests/test_websocket_outbound_metrics_repro.py` (the only changed file). No behaviour
change. `git diff -- pypost` is empty.

## Linter Fixes

- No linter findings. `make lint` exited `0` before and after cleanup. The flake8 scope of
  `make lint` is `pypost/` only, so the test file was reviewed by hand against the module
  style and the 100-character limit.

## Code Formatting

Applied formatting changes:

- [x] Automatic code formatting: not applicable. The repository has no formatter target, so
  the code was formatted by hand to match the module style.
- [x] Indentation and alignment fixes: none needed.
- [x] Line length correction: all lines are 100 characters or fewer. This was checked after
  the renames.

## Code Cleanup

Cleanup actions performed in `_run_loopback_send_table`:

- Removed the unused-in-practice `is_text` alias. `kind` and `size` now come from one
  `isinstance` branch. Before, `isinstance(payload, str)` was evaluated three times and mixed
  with `is_text`. The send branch keeps its own `isinstance`, which mypy needs for narrowing.
- Renamed terse locals for readability: `i` -> `row`, `n` -> `size`,
  `et`/`eb` -> `exp_text`/`exp_binary`, and `dt`/`db`/`dbytes` -> `d_text`/`d_binary`/`d_bytes`.
- The peer-receipt `wait_until` predicate now reads a named local, `received_count`, instead
  of computing `i + 1` inside the lambda.
- Added a one-line comment on the fixture guard assertion (UTF-8 bytes != characters).
- Updated the module docstring to name both PYPOST-1288 and the PYPOST-1297 real loopback test.
- Removed unused imports: 0. Removed unused variables: 1 (`is_text`). Removed commented-out
  code: none. Removed debug prints: none.

The assertion message formats in `30-failing-repro.md` are unchanged. The rendered text is
identical: `row <i> <kind> (<n> bytes) count delta: expected text=+<x> binary=+<y>, got
text=+<a> binary=+<b>`, `... bytes delta: expected +<n>, got +<m>`, `... not received by
peer`, `... peer kind mismatch`, and `... peer payload mismatch`.

## Validation Results

- [x] All tests passed. The gate is baseline-relative: every failure maps to a known flaky or
  pre-existing issue (see below).
- [x] All tests have explicit timeout markers. The module has `pytestmark = timeout(30)`, and
  the new test has `@pytest.mark.timeout(60)`.
- [x] No merge conflicts.
- [x] Syntax is valid.
- [x] Types are correct. `make typecheck` reports the baseline OK at 181 known errors, with
  no regression.

Command results:

| Command | Exit | Result |
| --- | --- | --- |
| `make lint` | 0 | flake8 OK; Markdown lint OK; relative links OK |
| `make typecheck` | 0 | mypy baseline OK (181) |
| `make verify-ai-tasks` | 0 | ai-tasks artifacts baseline OK |
| `make test WORKERS=1 PYTEST_ARGS='tests/test_websocket_outbound_metrics_repro.py tests/test_websocket_session_controller.py -q'` | 0 | 2/2 files passed |
| `make check` (single full run) | 2 | 368 files: 360 passed, 2 failed, 6 skipped |

`make check` failures:

| Node id | Outcome | Classification |
| --- | --- | --- |
| `tests/test_pytest_exit_policy.py` (`test_make_test_fails_closed_when_parallel_runner_is_missing`) | TIMED_OUT (120 s worker kill) | Known pre-existing: PYPOST-1299 |
| `tests/test_env_persistence_e2e.py::test_presenter_load_shows_no_env_when_key_missing_for_encrypted_data` | FAILED: `OSError: [Errno 39] Directory not empty` in `TemporaryDirectory.__exit__` | Flaky, not caused by this task: PYPOST-1311 |

Triage of `test_env_persistence_e2e.py`:

- Failure excerpt: `tests/test_env_persistence_e2e.py:168` in
  `with tempfile.TemporaryDirectory() as td:`, then `shutil.rmtree`, then
  `OSError: [Errno 39] Directory not empty: '/tmp/35759/tmp7ej_c_ue'`. The log just before it
  shows `environment_storage_async_load_dispatched`,
  `encryption_key_rotation_lookup_failed`, and `load_environments_partial_failure`.
- Re-run on the current tree:
  `make test WORKERS=1 PYTEST_ARGS='tests/test_env_persistence_e2e.py -q'` passed 3 of 3 times.
- Base evidence: at `286b3a4c` in a temporary `git worktree`,
  `make test VENV=/home/src/.venv WORKERS=1 PYTEST_ARGS='tests/test_env_persistence_e2e.py -q'`
  passed 15 of 15 times. The worktree was removed afterwards. The failure did not reproduce in
  isolation on either tree.
- Not caused by this task. The diff touches only the WebSocket metrics test module, which runs
  in a separate worker process. `pypost/` and the env test are unchanged.
- Suspected cause: the asynchronous environment load started by `EnvPresenter` writes into the
  temporary directory, or holds a file open in it, while `TemporaryDirectory` cleanup runs.
  That makes `rmtree` race under full-suite load. The root cause was not investigated further.
- Observed rate: 1 failure in 1 full-suite run; 0 failures in 18 isolated runs.

## Notes

- Filed: the `test_env_persistence_e2e.py` flake above, which is not covered by
  PYPOST-1299, -1298, -1263, -1305, or -1306, is now [PYPOST-1311][] (NON-BLOCKER, pre-existing).
- No other known flaky issues (PYPOST-1298, -1263, -1305, -1306) appeared in this run.

[PYPOST-1311]: https://pypost.atlassian.net/browse/PYPOST-1311
