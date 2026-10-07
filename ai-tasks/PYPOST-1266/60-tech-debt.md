# PYPOST-1266: Technical Debt Analysis

## Assessment and Evidence

Reviewed the accepted [requirements](10-requirements.md), [architecture](20-architecture.md),
[cleanup evidence](40-code-cleanup.md), and [observability report](50-observability.md), together
with the scoped worker/presenter diff, migrated reader fakes, and
`tests/test_collection_import_reader_contract.py`.

**Verdict: no new implementation debt or blocking issue identified in this scope.** The
reader-dependent cancellation gap from PYPOST-1229 debt item 1 is addressed. Remaining loading,
coverage, and lifecycle limitations have existing owners below. Independent acceptance of this
analysis remains with the autonomous orchestrator; this execution leaves Step 7 `[/]`.

Step 4's focused contract, parser, progress, cancellation, responsiveness, and UI checks passed.
Production lint passed, and typecheck passed against the unchanged 181-error baseline. Step 6
also passed four retained-log checks. These are recorded results, not tests rerun in Step 7.

The full Step 5 `make check WORKER_TIMEOUT=120` exited 2: 359 files passed, seven failed, and
six skipped. Its task-caused SOLID snapshot drift was corrected with `make baseline-metrics`,
and the focused SOLID module passed. All six remaining failed modules are classified below;
the full quality gate is not represented as passing. Exact commands, run IDs, excerpts, baseline
comparison, and two unchanged-tree reruns are retained in the cleanup report.

## Shortcuts Taken

- No temporary adapter, signature inspection, retry without a callback, or compatibility escape
  was retained. `ReadImportFile` is a structural `Protocol` with required keyword `on_progress`,
  and the worker calls every reader once with that keyword.
- Cancellation continues to use the existing progress callback and local
  `CollectionImportCancelled` exception. This is the accepted design: the parser stays Qt-free,
  and callback exceptions unwind into the worker's cancellation outcome.
- The pure production parser retains an optional callback for synchronous callers. The worker
  always supplies it; an optional default does not weaken the background call contract.
- Opaque-reader tests intentionally use invalid signature metadata and an optional callback to
  expose the old fallback. Other supported-shape tests require the callback. These are deliberate
  regression fixtures, not production compatibility code.

## Code Quality Issues

- The former `Callable[..., ...]` alias and `_callable_accepts_progress()` inference are removed.
  Presenter injection and affected UI helpers now use `ReadImportFile`. Functions, bound methods,
  callable objects, and keyword forwarding need no runtime registry or inheritance.
- Typing describes call compatibility; invoking checkpoints and propagating their exceptions
  remain semantic obligations of each reader. The production parser and record-processing fakes
  obey them, with behavioral coverage. Runtime protocol checks would not prove that behavior.
- File-error fakes accept the keyword but fail before any record exists, so no synthetic progress
  checkpoint is required. The responsiveness and delayed fakes invoke checkpoints after their
  finite simulated work, retaining the original purposes of those tests.
- No new hardcoded production values, dependencies, duplicated lifecycle branches, or unexplained
  architecture deviations were introduced. Existing teardown budgets and repeated interruption
  paths remain owned by PYPOST-1264. Fixed test data and finite wait budgets are intentional.
- The existing lint target excludes tests, tracked by PYPOST-1303. Production lint and the mypy
  baseline gate are useful evidence but do not imply test lint coverage or zero typing errors.

## Missing Tests

No missing coverage was identified for the accepted reader-contract change. The focused module
checks:

- The original opaque-reader regression: interruption at record one yields one progress event,
  one cancellation, no completion or failure, and no processing of records two or three.
- Success/progress and first-checkpoint cancellation for six supported shapes: keyword-only and
  positional-or-keyword functions, bound methods, callable objects, keyword forwarding, and
  opaque callable metadata. Assertions preserve returned candidates and record errors.
- The actual JSON parser through the worker: normal completion with valid/invalid records, plus
  cancellation at the valid first record and invalid second record, without result publication.
- The progress module rejects a legacy single-argument reader before its body executes, checks
  `TypeError`, captures the existing ERROR log, and excludes completion and cancellation.

Existing presenter tests protect application suppression and cancellation/error presentation;
the final-publication regression protects interruption after the last checkpoint. Broader real
JSON/YAML, pre-start interruption, and user-close/lifecycle matrices remain PYPOST-1265 scope.
The focused JSON cases here partially address that broader coverage need without claiming its
entire matrix complete. Legacy-reader support is no longer part of the accepted contract.

### Explicit Timeouts and Bounded Waits

All added or modified test modules declare module-level `pytest.mark.timeout`:

| Module | Seconds |
| --- | --- |
| `test_collection_import_reader_contract.py` | 30 |
| `test_collection_import_progress.py` | 60 |
| `test_collection_import_responsiveness.py` | 120 |
| `test_collection_import_async_gaps.py` | 60 |
| `test_collections_import_ui.py` | 60 |
| `test_collections_import_ui_repro.py` | 30 |

New worker contract/rejection tests retain worker references, use `wait(5000)`, and request
interruption in `finally` before another bounded join. GUI polling has finite deadlines, and
simulated work uses finite delays. Direct-connected checkpoint handlers make cancellation
ordering deterministic rather than depending on elapsed-time assertions. No missing explicit
timeout marker or newly unbounded wait was found; the mandatory timeout blocker does not apply.

## Performance Concerns

- `_read_records()` still reads and decodes the whole file before per-record checkpoints. Neither
  this protocol nor cooperative cancellation bounds loading/decoding latency; PYPOST-1267 owns
  streaming or interruptible decoding and measured large-file cancellation latency.
- A costly single record can delay the next safe checkpoint. Existing teardown limits can still
  return unclean if work exceeds their budgets; PYPOST-1264 owns lifecycle policy consolidation.
- Direct invocation removes signature introspection. The existing progress signal and
  interruption check remain per-record operations; no new loop, telemetry emission, or payload
  copy was added. No new performance regression was identified by inspection, and no benchmark
  or latency bound is claimed by this task.

## Architecture and Documentation

The implementation follows the accepted protocol, direct worker invocation, presenter typing,
fake migration, and production-contract validation plan. Signals, terminal outcomes, parser
return values, and the conflict/apply workflow retain their established behavior. No new
observability component is needed, as assessed in Step 6.

User documentation updates are not applicable to this dependency contract. Step 8 will update
`doc/dev/collection_import.md` with the required keyword and checkpoint exception obligation;
that planned deliverable is not deferred debt.

## Step 7 Validation

`make lint-docs verify-ai-tasks` passed: 16 user documentation files linted, 18 files checked
for relative links, and 391 completed task artifacts accepted with two grandfathered legacy
gaps. These Make targets do not validate Markdown style in this open task's reports; the report
was reviewed directly for structure, references, and consistency with the accepted evidence.
No production or test changes were made, and existing passing tests were not rerun.

## Follow-up Tasks

### Existing Scoped Follow-ups

No new issue is required by this analysis. Reuse these existing owners:

- [PYPOST-1267](https://pypost.atlassian.net/browse/PYPOST-1267): whole-file loading/decoding
  cancellation latency and its measured large-file bound. Remains outside this task's guarantee.
- [PYPOST-1265](https://pypost.atlassian.net/browse/PYPOST-1265): broader real-file and lifecycle
  cancellation coverage. Account for the new focused JSON cases and legacy-reader rejection
  when extending the matrix; do not restore the removed legacy compatibility contract.
- [PYPOST-1264](https://pypost.atlassian.net/browse/PYPOST-1264): consolidate teardown interruption
  and join policy, including the inherited 5000 ms and 100 ms budgets.
- [PYPOST-1303](https://pypost.atlassian.net/browse/PYPOST-1303): existing lint coverage gap for
  tests. This is tooling debt, not a newly failing test or a reason to change task scope.

The following Step 5 failure triage is preserved, including exact test identifiers and existing
Jira owners. No new failure, exclusion, skip, or xfail was introduced during Step 7.

### PYPOST-1298: Existing Makefile Timeout Clusters

[PYPOST-1298](https://pypost.atlassian.net/browse/PYPOST-1298) already tracks the four
Makefile modules that failed in the full check. Verdict:
`NON-BLOCKER — pre-existing (flaky)`. At task base `28084091`, all four passed. Two unchanged
current-tree reruns also passed all four modules. Per module, current observations are one
failed and two passing runs; baseline passes are counted separately. See
[the cleanup report](40-code-cleanup.md) for commands, logs, and original failure excerpts.
Shared environment contention or setup cost is suspected; this run does not establish the
same lock root cause for every timeout.

For the identifiers below, concatenate the displayed module/class prefix and test name
without whitespace. This preserves complete identifiers while keeping source lines readable.

Prefix: `tests/test_makefile_recipes.py::TestDependencyChain::`

- `test_install_depends_on_marker_only`
- `test_test_depends_on_venv_test_venv_otel_and_marker`
- `test_test_cov_depends_on_venv_test_venv_otel_and_marker`
- `test_venv_test_stamp_depends_on_marker_and_pyproject`
- `test_venv_otel_stamp_depends_on_marker_and_pyproject`
- `test_security_audit_depends_on_install`
- `test_lock_target_has_no_venv_prerequisites`
- `test_lock_dev_target_has_no_venv_prerequisites`
- `test_lock_otel_target_has_no_venv_prerequisites`
- `test_generate_mcp_fixtures_depends_on_marker`
- `test_check_mcp_fixtures_depends_on_marker`
- `test_generate_license_inventory_depends_on_install`
- `test_check_license_inventory_depends_on_install`
- `test_run_depends_on_marker_only`
- `test_lint_depends_on_marker_and_venv_test`
- `test_typecheck_depends_on_marker_and_venv_test`
- `test_test_slow_depends_on_venv_test_venv_otel_and_marker`
- `test_test_agent_e2e_depends_on_venv_test_venv_otel_and_marker`

Prefix: `tests/test_makefile_install_stamp_contract.py::TestInstallExtraStampContract::`

- `test_install_touches_both_extra_stamps`

Prefix: `tests/test_makefile_stamp_test_idempotency.py::TestVenvTestStampIdempotency::`

- `test_venv_test_skips_pip_when_current`

Prefix: `tests/test_makefile_target_filtering.py::TestTargetFiltering::`

- `test_make_test_excludes_slow_marker` failed before module termination.
- `test_lint_succeeds_after_install` was running when the 120-second worker timeout fired.

### PYPOST-1299: Existing Exit-Policy Timeout

[PYPOST-1299](https://pypost.atlassian.net/browse/PYPOST-1299):
`NON-BLOCKER — pre-existing`. The same 60-second test failure followed by a 120-second
worker timeout reproduced at task base `28084091`, run `a1e3573d2213`.

Prefix: `tests/test_pytest_exit_policy.py::`

- `test_make_test_fails_closed_when_parallel_runner_is_missing`
- `test_make_test_cov_fails_closed_when_parallel_runner_is_missing`

### PYPOST-1315: Export UI Worker Crash

[PYPOST-1315](https://pypost.atlassian.net/browse/PYPOST-1315):
`NON-BLOCKER — pre-existing (flaky)`. The full check reported eight passed test bodies,
then worker exit -11 without a traceback. Two unchanged-tree reruns passed; the fresh baseline
also passed. Current-tree observations are one failed and two passing module runs.
Root cause is not investigated; a specific failing assertion or test body is not established.

Prefix: `tests/test_environment_export_ui.py::TestExportEnvironments::`

- `test_single_environment_export_writes_object_root`
- `test_happy_path_exports_all_and_shows_success`
- `test_cancelled_scope_leaves_files_unchanged`
- `test_selected_scope_without_selection_shows_error`
- `test_hidden_values_require_confirmation`
- `test_cancelled_secrets_confirmation_skips_write`
- `test_no_serialize_callable_is_noop`
- `test_logs_completed_event`

## Independent Closure Review

The separate blocker review returned `SAFE TO CLOSE`: all recorded items are non-blockers,
and the scoped typed reader and cancellation acceptance criteria are met. Step 8 developer
documentation remains the next required deliverable before commit and Jira closure.
