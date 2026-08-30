# PYPOST-1149: Technical Debt Analysis

## Shortcuts Taken

1. **Hand-rolled `CLIParser` instead of `argparse`/`click`**: A manual argument loop separates orchestrator flags from pytest passthrough. This shipped quickly and matches the Makefile contract, but it is fragile — unknown pytest options that take a value may be mishandled, and flags like `--cov-report`, `-x`, `--lf`, or `--timeout` are not explicitly classified (some fall through as pytest args, others may be dropped).

2. **`python -c "pytest.main(...); os._exit(code)"` subprocess wrapper**: Workers invoke pytest via an inline `-c` script rather than `python -m pytest`. This forces a hard process exit to avoid pytest/plugin shutdown hangs, but adds interpreter startup overhead and obscures the invocation in logs.

3. **Inline console reporting instead of a `ConsoleReporter` class**: Architecture (`20-architecture.md`) described a dedicated reporter module; implementation keeps progress, failure grouping, slowest-files table, and summary printing inside `run_parallel_tests()`. Acceptable for scope, but harder to unit-test formatting in isolation.

4. **Makefile sequential fallback retained**: `test` and `test-cov` still fall back to direct `pytest` when `scripts/run_parallel_tests.py` is absent. This preserves backwards compatibility but means two code paths must stay aligned manually.

5. **Hard-coded coverage threshold (`70`)**: `fail_under=70` appears in `CoverageManager.combine_and_report`, worker subprocess `--cov-fail-under=0` override, and post-run parsing — not read from `pyproject.toml` `[tool.pytest.ini_options] addopts`.

6. **`CoverageManager.get_env_for_worker()` is unused**: Coverage file naming is duplicated inline in `SubprocessTestExecutor.run_test_file()`; the helper method is dead API surface left from the architecture sketch.

## Code Quality Issues

1. **`CLIParser` lacks validation for invalid worker counts**: `--workers 0` or negative values from CLI bypass `get_worker_count()` guards (`cli_workers > 0` check only applies when env fallback is used). A zero worker count could reach `ThreadPoolExecutor(max_workers=0)`.

2. **Makefile contract tests not updated for parallel runner**: `tests/test_makefile.py` still asserts only `-m "not slow"` in the `test` recipe; it does not verify `scripts/run_parallel_tests.py` invocation or the `WORKERS` variable wiring introduced by this task.

3. **Default target asymmetry**: When `PYTEST_ARGS` is empty, the orchestrator path passes only `-m "not slow"` (relying on default discovery of `tests/test_*.py`), while the sequential fallback passes `tests/ -m "not slow"`. Behavior matches today but the recipes differ subtly.

4. **JSON report embeds full stdout/stderr per file**: `JsonReporter.to_dict()` stores complete subprocess output for every test file. Useful for CI debugging, but reports can grow large on verbose runs (`-v`, coverage output).

5. **Architecture `--timeout` runner flag not implemented**: `20-architecture.md` lists `--timeout` as a runner CLI option; no such flag exists. Per-file wall-clock timeouts remain delegated entirely to pytest's own `pytest.mark.timeout` markers inside each test module.

## Missing Tests

1. **Makefile integration contract**: No test asserts that `make test` / `make test-cov` invoke `scripts/run_parallel_tests.py` with `--workers $(WORKERS)` and forward `PYTEST_ARGS`.

2. **Real coverage threshold breach**: `test_parallel_runner_logs_coverage_threshold_warning` mocks `CoverageManager.combine_and_report`; there is no integration test that runs workers with `--cov` and asserts a genuine sub-70% combined report fails the orchestrator exit code.

3. **Invalid worker CLI values**: No test for `--workers 0`, negative workers, or non-numeric `--workers=abc` error handling.

4. **Sequential fallback path**: The `@if [ -f scripts/run_parallel_tests.py ]` else branch is untested.

5. **Subdirectory / glob discovery edge cases**: Requirements note flat `tests/test_*.py` only; discovery accepts explicit paths and globs but lacks regression tests for nested layouts or ambiguous targets.

6. **End-to-end repo smoke**: All integration tests use `tmp_path` fixtures; no smoke test runs the orchestrator against a small slice of the real `tests/` tree (acceptable for speed, but leaves Makefile wiring unverified under production discovery).

Timeout-marker review for **this task's** tests: **no blocker** — `tests/test_run_parallel_tests.py` declares module-level `pytestmark = pytest.mark.timeout(60)` and generated fixture files include explicit timeout markers.

## Performance Concerns

1. **Per-file subprocess startup tax**: Each of 268+ test files spawns a fresh Python interpreter and re-imports pytest/plugins. Parallelism reduces wall-clock time (observed ~1.7–3x on small batches; full suite gains depend on worker count and file duration spread), but cumulative CPU time increases versus a single pytest process.

2. **Unbounded concurrent subprocess memory**: `ThreadPoolExecutor(max_workers=N)` launches up to `N` simultaneous pytest subprocesses with no back-pressure beyond worker count. On machines where `cpu_count()` is high, operators should tune `WORKERS` to avoid memory pressure from Qt-heavy modules.

3. **Coverage combine runs sequentially after all workers finish**: The `coverage combine` / `report` / `html` steps block the final exit; large worker counts produce many `.coverage.*` files to merge.

4. **Positive mitigation**: Process-per-file isolation avoids the pre-existing single-process Qt segfault class ([PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117)) that occurs when many GUI modules run in one pytest session. This orchestrator does **not** fix modules that segfault in their own subprocess (see pre-existing failures below).

## Follow-up Tasks

### Implementation follow-ups (PYPOST-1149 scope debt)

1. Extend `tests/test_makefile.py` to lock the parallel runner recipe (`run_parallel_tests.py`, `WORKERS`, `--cov` on `test-cov`). Jira: [PYPOST-1153](https://pypost.atlassian.net/browse/PYPOST-1153)
2. Replace or wrap `CLIParser` with a maintained parser (e.g. `argparse` with known orchestrator flags + `parse_known_args` passthrough) to reduce pytest flag drift. Jira: [PYPOST-1153](https://pypost.atlassian.net/browse/PYPOST-1153)
3. Remove dead `CoverageManager.get_env_for_worker()` or consolidate coverage env setup into one code path. Jira: [PYPOST-1153](https://pypost.atlassian.net/browse/PYPOST-1153)
4. Read `--cov-fail-under` from `pyproject.toml` instead of hard-coding `70`. Jira: [PYPOST-1153](https://pypost.atlassian.net/browse/PYPOST-1153)
5. Add optional per-file orchestrator wall-clock timeout (called out as out-of-scope in `10-requirements.md` Q&A). Jira: [PYPOST-1153](https://pypost.atlassian.net/browse/PYPOST-1153)
6. Step 8: document parallel runner usage in `doc/dev/testing.md` (Makefile `WORKERS`, `--report-json`, subprocess isolation model). **Done in PYPOST-1149** — see `doc/dev/parallel_test_runner.md`
7. Consider extending parallel orchestration to `test-slow` / `test-agent-e2e` if those targets become CI bottlenecks (explicitly out of scope for PYPOST-1149). Jira: [PYPOST-1153](https://pypost.atlassian.net/browse/PYPOST-1153)

### Pre-existing test failures (NON-BLOCKER)

Observed during PYPOST-1149 verification runs (`make test` / focused pytest). These failures predate this task and are not caused by the parallel orchestrator — the orchestrator surfaces them per-file with the same underlying pytest outcomes.

| Verdict | Test node id | Suspected cause | Jira |
| --- | --- | --- | --- |
| NON-BLOCKER — pre-existing | `tests/test_metrics_protocol.py::test_metrics_manager_satisfies_tracker_protocol` | `MetricsManager` no longer satisfies `MetricsTrackerProtocol` (`isinstance` check fails) | [PYPOST-1150](https://pypost.atlassian.net/browse/PYPOST-1150) |
| NON-BLOCKER — pre-existing | `tests/test_template_expression_tokenizer.py::TestPlainVariablePattern::test_plain_pattern_rejects_whitespace_inside` | `is_plain_variable_token("{{ host }}")` returns `True`; test expects `False` for whitespace inside delimiters | [PYPOST-1151](https://pypost.atlassian.net/browse/PYPOST-1151) |
| NON-BLOCKER — pre-existing | `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates` | Dialog discovery LOC aggregate baseline drift (recorded 1,030 / 333 vs current module sizes) | [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111) |
| NON-BLOCKER — pre-existing | `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics` | SOLID baseline-metrics markdown snapshot drift vs live `audit_baseline_metrics.py` output | [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111) |
| NON-BLOCKER — pre-existing | `tests/test_suite_qapp_alignment.py::test_suite_has_no_local_qapp_fixtures_or_setupclass_qapplication` | Local `qapp()` fixture still present in `tests/test_mcp_controls_presenter.py` | [PYPOST-1110](https://pypost.atlassian.net/browse/PYPOST-1110) |
| NON-BLOCKER — pre-existing, corrected | `tests/test_ui_wait.py` (entire module — originally filed as a native segfault during collection/execution) | Originally suspected: PySide6/Shiboken segfault in isolated subprocess (`QT_QPA_PLATFORM=offscreen`). **Corrected per PYPOST-1152's investigation**: does not currently reproduce — 47/47 clean runs across 4 invocation shapes (direct `pytest`, `make test PYTEST_ARGS=...`, full-suite embedding, concurrent multi-subprocess) plus a full code-review pass of `tests/test_ui_wait.py` and `pypost/agent/ui_wait.py` found no PyPost-owned defect pattern. `tests/test_ui_wait_stress.py` now guards for a future recurrence (green, unmarked, run via `make test-slow` / `-m slow`); see `doc/dev/gui_testing.md` § Troubleshooting and `ai-tasks/PYPOST-1152/20-architecture.md` for full evidence. | [PYPOST-1152](https://pypost.atlassian.net/browse/PYPOST-1152) (this task's investigation; related: [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117); dormant follow-up if it ever recurs: [PYPOST-1254](https://pypost.atlassian.net/browse/PYPOST-1254)) |

Repro command for the filed cluster:

```bash
make test PYTEST_ARGS="tests/test_metrics_protocol.py tests/test_template_expression_tokenizer.py tests/test_pypost_1077_verification_artifacts.py tests/test_solid_audit_baseline.py tests/test_suite_qapp_alignment.py tests/test_ui_wait.py -v"
```

## Verdict

**Acceptable technical debt for merge** — The parallel orchestrator delivers the required speedup and Qt isolation model with thorough unit/integration coverage of its own behavior. Remaining debt is mostly parser maintainability, Makefile contract tests, hard-coded coverage threshold, and pre-existing suite failures tracked above. None block closing PYPOST-1149 once Steps 8 and commit complete.
