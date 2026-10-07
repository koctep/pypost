# PYPOST-1286: Code Cleanup Report

## Linter Fixes

- `make lint` passes (flake8 on `pypost/`, Markdown lint, relative link check).
- The repository provides `lint` rather than the generic skill's `analyze` target.
- Removed the unused `process_until` import from
  `tests/test_websocket_stream_view_repro.py`. The test now synchronizes with
  `wait_for_export()`, and `make lint` does not run flake8 on `tests/`, so lint did not
  report this import.

## Code Formatting

- [x] Inspected the production and test diff for indentation and alignment.
- [x] All changed lines are 100 characters or shorter.
- [ ] Automatic code formatting: the Makefile has no formatter target.

## Code Cleanup

- Removed unused imports: 1 (`process_until` in `tests/test_websocket_stream_view_repro.py`).
- Removed unused variables: 0.
- Removed commented-out code: none present.
- Removed debug prints: none present.
- Removed 4 redundant per-test `@pytest.mark.timeout(30)` decorators from
  `tests/test_pypost_1286_failing_repro.py`. The module-level
  `pytestmark = pytest.mark.timeout(30)` already sets the same timeout.
- Corrected the `WebSocketStreamView.closeEvent` docstring. It now says that `closeEvent`
  refuses to close while the view still owns an export worker after the wait budget. The old
  docstring said it "ensures cleanup". This is a docstring change only.

## Validation Results

- [x] Target tests passed in 3 consecutive full-suite parallel runs (see table).
- [x] All tests have explicit timeout markers. Changed test modules declare a
  module-level 30 s timeout.
- [x] No merge conflicts.
- [x] Syntax is valid.
- [x] Types are correct. `make typecheck` reports "mypy baseline OK (181 known errors)",
  which is no regression against the baseline.

### Full-suite parallel runs (default `WORKERS`)

| Run | Command | Files passed/failed/skipped | `test_stream_view_transcript_export_actions` | `test_strict_conversion_keeps_literal_fallback_for_unrelated_failed_token` |
| --- | --- | --- | --- | --- |
| 1 | `make check` | 353 / 7 / 6 | PASS | PASS |
| 2 | `make test` | 359 / 1 / 6 | PASS | PASS |
| 3 | `make test` | 359 / 1 / 6 | PASS | PASS |

The task repro (`tests/test_pypost_1286_failing_repro.py`) passed in all three runs. The target
tests had zero failures across the three runs, which meets the DoD for the targets. Every
failure is in a subprocess-based Makefile or exit-policy test that this task does not touch.

- All 3 runs: `tests/test_pytest_exit_policy.py` timed out after 120 s. Inside it,
  `test_make_test_fails_closed_when_parallel_runner_is_missing` hit its 60 s pytest-timeout.
  It also fails at base `10ba60b7` in the same way, so it is a **pre-existing** failure.
  Filed as [PYPOST-1299](https://pypost.atlassian.net/browse/PYPOST-1299), which also covers
  the `test_make_test_cov_...` variant.
- Run 1 only: `tests/test_makefile_recipes.py` and `tests/test_makefile_markers.py` had setup
  timeouts in `makefile_test_helpers._get_shared_base_venv` (`fcntl.flock`).
  `test_makefile_install_stamp_contract.py`, `test_makefile_stamp_otel_idempotency.py`,
  `test_makefile_stamp_test_idempotency.py` and `test_makefile_target_filtering.py` also
  timed out in run 1. All of them passed in runs 2 and 3 on the unchanged tree. At base,
  `test_makefile_target_filtering.py` also timed out. These are **flaky** under parallel
  venv-lock contention and are not caused by this task. All six files are filed as
  [PYPOST-1298](https://pypost.atlassian.net/browse/PYPOST-1298).
- The base-commit run used a temporary worktree, now removed. It ran `make test` and failed
  5 files: `test_pytest_exit_policy.py` and `test_makefile_target_filtering.py`, plus
  `test_collection_import_profile.py`, `test_env_presenter.py` and `test_run_parallel_tests.py`. These three were not seen on the task tree.

`make check` exited non-zero only because of the failures listed above. `lint` passed, and
`verify-ai-tasks` did not run because the `test` prerequisite failed.

## Notes

- Step 4 iterations 5 to 7 addressed the earlier interrupted attempt's concerns. These were
  queued-completion ownership, the close-timeout refusal, and a repro that held the worker with
  a sleep. The repro now holds the worker with a `threading.Event` and contains no sleeps.
- The failures above are **NON-BLOCKER** pre-existing failures. They are filed under the
  triage rules and do not block this task:
  - [PYPOST-1299](https://pypost.atlassian.net/browse/PYPOST-1299):
    `tests/test_pytest_exit_policy.py::test_make_test_fails_closed_when_parallel_runner_is_missing`
    and the `test_make_test_cov_...` variant. Fails in 3 of 3 runs and at base `10ba60b7`.
  - [PYPOST-1298](https://pypost.atlassian.net/browse/PYPOST-1298): `test_makefile_recipes`,
    `test_makefile_markers`, `test_makefile_install_stamp_contract`,
    `test_makefile_stamp_otel_idempotency`, `test_makefile_stamp_test_idempotency` and
    `test_makefile_target_filtering` time out on the shared venv `flock`. Flaky in 1 of 3
    runs; `test_makefile_target_filtering` also timed out at base.
