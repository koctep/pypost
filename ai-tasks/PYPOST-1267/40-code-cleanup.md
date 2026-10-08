# PYPOST-1267: Code Cleanup Report

## Linter Fixes

- No production lint fixes were necessary. `make check` passed its `lint` prerequisite:
  flake8, Markdown lint (16 files), and relative links (18 files).
- The repository exposes `lint` rather than the skill's suggested `analyze` target.

## Code Formatting

- Independent review found a 119-character parameterization decorator in
  `tests/test_collection_import_decode.py`. Wrapped its argument list without changing cases.
  No other over-100-character lines were found in the three newly added Python files.
  After this correction, `make lint` passed and
  `make test PYTEST_ARGS='tests/test_collection_import_decode.py' WORKERS=1 WORKER_TIMEOUT=180`
  passed in 4.30 seconds. `git diff --check` remained clean.
- Existing import and decoder formatting follows repository conventions; no automatic formatter
  target is available or needed for this change.
- `git diff --check` passed: no whitespace errors or conflict markers in the tracked patch.

## Code Cleanup

- Replaced a stale red-repro comment claiming that the decoding helper was absent. The observer
  still inspects frames without importing decoder helpers; no behavioral change was made.
- Reviewed changed production imports, local state, cleanup paths, and tests. No further unused
  imports, debug prints, or dead code required removal. CPython and PyYAML notices remain intact.

## Validation Results

- [x] Production static analysis and documentation checks passed.
- [x] Changed test modules declare explicit timeouts: decoder 30 seconds, real-file cancellation
  150 seconds, existing progress tests 60 seconds. Thread/event waits remain bounded.
- [x] Syntax/import validation passed through the tests and lint gate.
- [x] `make typecheck` passed with the unchanged baseline of 181 known errors.
- [x] `make verify-ai-tasks` passed: 392 completed tasks; 2 grandfathered legacy gaps.
- [ ] Full `make check` passed: its test prerequisite returned failure, so artifact verification
  was run separately. The run completed 374 modules: 363 passed, 5 failed, 6 skipped, 320.03 seconds.
  No test was skipped, deleted, or marked xfail by this task.
- All collection import modules passed, including differential decoding (16.13 seconds), all
  11 real-file cancellation cases (15.61 seconds), reader contract, progress, responsiveness,
  cancellation, asynchronous gaps, teardown, wait, apply, profile, and presenter coverage.

## Full-suite Failure Evidence

The task base is `0345e88c`. Classification below uses unchanged-tree reruns rather than a base
worktree; no claim is made that these failures were reproduced at that base. Full output is in
`/tmp/pypost-1267-step5-check.log`; the exact original command was `make check`.

### Environment export worker

NON-BLOCKER — flaky, tracked by [PYPOST-1315](https://pypost.atlassian.net/browse/PYPOST-1315).
The `tests/test_environment_export_ui.py` worker exited with signal 11 after all eight items
passed; there was no failed assertion. Its final item was
`tests/test_environment_export_ui.py::TestExportEnvironments::test_logs_completed_event`.
The worker duration was 9.25 seconds.

The unchanged rerun passed in 2.06 seconds:

```bash
make test PYTEST_ARGS='tests/test_environment_export_ui.py' WORKERS=1 WORKER_TIMEOUT=180
```

### Makefile recipes and install stamps

NON-BLOCKER — flaky, tracked by [PYPOST-1298](https://pypost.atlassian.net/browse/PYPOST-1298).
The existing issue names these same tests. Its suspected flock cause was not established by
this run, whose traces stop in subprocess polling during materialization/install.

Both modules passed an unchanged rerun: recipes 27.86 seconds; install stamps 34.62 seconds;
combined 62.48 seconds. Failure traces establish subprocess timeouts, rather than identifying
an underlying lock owner. Root cause was not investigated or changed in PYPOST-1267.

```bash
make test PYTEST_ARGS='tests/test_makefile_recipes.py tests/test_makefile_install_stamp_contract.py' WORKERS=1 WORKER_TIMEOUT=180
```

The original recipes worker had 18 setup errors and 18 passing tests in 44.84 seconds
(46.43 seconds including worker startup). The setup trace ended with:

```text
tests/makefile_test_helpers.py:425: in make_workspace
    _materialize_prewarmed_venv(ws)
tests/makefile_test_helpers.py:409: in _materialize_prewarmed_venv
    subprocess.run(
/usr/lib/python3.13/subprocess.py:2128: in _communicate
    ready = selector.select(timeout)
/usr/lib/python3.13/selectors.py:398: in select
    fd_event_list = self._selector.poll(timeout)
E   Failed: Timeout (>30.0s) from pytest-timeout.
```

Exact affected recipes nodes:

```text
tests/test_makefile_recipes.py::TestDependencyChain::test_install_depends_on_marker_only
tests/test_makefile_recipes.py::TestDependencyChain::test_test_depends_on_venv_test_venv_otel_and_marker
tests/test_makefile_recipes.py::TestDependencyChain::test_test_cov_depends_on_venv_test_venv_otel_and_marker
tests/test_makefile_recipes.py::TestDependencyChain::test_venv_test_stamp_depends_on_marker_and_pyproject
tests/test_makefile_recipes.py::TestDependencyChain::test_venv_otel_stamp_depends_on_marker_and_pyproject
tests/test_makefile_recipes.py::TestDependencyChain::test_security_audit_depends_on_install
tests/test_makefile_recipes.py::TestDependencyChain::test_lock_target_has_no_venv_prerequisites
tests/test_makefile_recipes.py::TestDependencyChain::test_lock_dev_target_has_no_venv_prerequisites
tests/test_makefile_recipes.py::TestDependencyChain::test_lock_otel_target_has_no_venv_prerequisites
tests/test_makefile_recipes.py::TestDependencyChain::test_generate_mcp_fixtures_depends_on_marker
tests/test_makefile_recipes.py::TestDependencyChain::test_check_mcp_fixtures_depends_on_marker
tests/test_makefile_recipes.py::TestDependencyChain::test_generate_license_inventory_depends_on_install
tests/test_makefile_recipes.py::TestDependencyChain::test_check_license_inventory_depends_on_install
tests/test_makefile_recipes.py::TestDependencyChain::test_run_depends_on_marker_only
tests/test_makefile_recipes.py::TestDependencyChain::test_lint_depends_on_marker_and_venv_test
tests/test_makefile_recipes.py::TestDependencyChain::test_typecheck_depends_on_marker_and_venv_test
tests/test_makefile_recipes.py::TestDependencyChain::test_test_slow_depends_on_venv_test_venv_otel_and_marker
tests/test_makefile_recipes.py::TestDependencyChain::test_test_agent_e2e_depends_on_venv_test_venv_otel_and_marker
```

The failed install item was
`tests/test_makefile_install_stamp_contract.py::TestInstallExtraStampContract::test_install_touches_both_extra_stamps`.
The worker reported one failure and one pass in 87.63 seconds (90.03 seconds including startup).
The failure occurred in `_run_make(make_workspace, "install")`, via helper line 83 and
`selector.poll`, ending `Failed: Timeout (>60.0s) from pytest-timeout.`

### Remaining Makefile timeouts

NON-BLOCKER — flaky. Both modules passed the unchanged rerun: target filtering 49.64 seconds,
exit policy 103.56 seconds; combined 153.21 seconds. No new task-caused failure remains.

The `tests/test_makefile_target_filtering.py` worker was killed after 120.00 seconds. It reported
`tests/test_makefile_target_filtering.py::TestTargetFiltering::test_make_test_excludes_slow_marker`
failed in 30.20 seconds, two later passes, then the active item
`tests/test_makefile_target_filtering.py::TestTargetFiltering::test_lint_succeeds_after_install`.
The worker ended `worker timeout after 120.0s`, without a completed assertion traceback.
These exact tests are tracked by
[PYPOST-1298](https://pypost.atlassian.net/browse/PYPOST-1298).

The `tests/test_pytest_exit_policy.py` worker was killed after 120.06 seconds. It reported
`tests/test_pytest_exit_policy.py::test_make_test_fails_closed_when_parallel_runner_is_missing`
failed in 60.06 seconds and was running
`tests/test_pytest_exit_policy.py::test_make_test_cov_fails_closed_when_parallel_runner_is_missing`
when killed. The worker ended `worker timeout after 120.0s`, without a completed traceback.
These exact tests are tracked by
[PYPOST-1299](https://pypost.atlassian.net/browse/PYPOST-1299).

Unchanged rerun command (passed, exit 0):

```bash
make test PYTEST_ARGS='tests/test_makefile_target_filtering.py tests/test_pytest_exit_policy.py' WORKERS=1 WORKER_TIMEOUT=180
```

## Notes

Step 5 remains `[/]` pending independent review. Production behavior was not changed during
cleanup. The full suite must be assessed relative to the documented, tracked flaky failures;
this report does not claim an entirely green full run.
