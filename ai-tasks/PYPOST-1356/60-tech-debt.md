# PYPOST-1356: Technical Debt Analysis

## Shortcuts Taken

No temporary production implementation or runtime fix was introduced. The test-only manager
substitutes socket/thread transport while retaining real MCP tool registration/listing,
registry resolution, settings persistence, editor actions, and canonical collection/environment
ownership. This boundary is the accepted offline architecture, not a shortcut hiding a defect.

The bundle upgrade replaces a complete temporary directory at the same injected path.
It verifies next-start loading without claiming to test an installer or a packaging upgrade.

## Code Quality Issues

No new production quality issue or acceptance gap was found. The unused transport snapshot
was removed in Step5; static/type/cap/document checks passed. The single connected scenario
uses small helpers for bundle creation, editor actions, and actual tool listing. Test-only
access to implementation fields is deliberate to verify real suppliers and canonical owners
without adding product APIs solely for testing.

The user guide preserves existing examples-path references and explicitly excludes automatic
migration of existing examples-library servers and workspace copies. Developer pointers are
scheduled for Step8, rather than omitted from the task.

## Missing Tests

The one acceptance test has an explicit 60-second timeout and 5-second bounded event waits
and teardown. It covers paired-copy sanitization and durable persistence, original startup,
shipped version replacement, next-start updated tools, canonical collection-copy persistence
and identity, unchanged source bytes, Save association, and detached startup after bundle removal.

It does not bind sockets, invoke remote tools, validate live credentials, or test real
installation services. Those are explicitly outside this offline scenario. Existing registry,
transport, and MCP implementation tests cover their own behavior; the new test does not replace
or claim equivalent transport/invocation coverage. Save/Cancel alternatives, repeated copies,
and error/privacy paths remain in the earlier 18 paired-environment and 16 collection-copy
cases. All four focused modules passed. No required new coverage gap remains.

## Performance Concerns

No runtime performance change was made. The isolated final acceptance rerun took 1.70 seconds
in Step4 and 1.61 seconds after Step5 cleanup. The finite test does not add background network
threads or remote-service latency. Existing full-suite Make fixture failures are tracked below,
not addressed by changing timeouts or adding unrelated infrastructure here.

## Follow-up Tasks

All observed baseline failures are ticketed. These are **NON-BLOCKER - pre-existing**
repository/fixture issues; none demonstrates a missing Built-in acceptance behavior.
The full `make check` completed 391 modules: 378 passed, 6 failed, 7 skipped in 310.13 seconds.
Evidence: `/tmp/pypost1356-step4-check.log`.

### Stale audit snapshots: PYPOST-1361

[PYPOST-1361](https://pypost.atlassian.net/browse/PYPOST-1361) covers all three exact nodes:

- `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
- `tests/test_pypost_1287_failing_repro.py::test_live_report_inventory_loc_matches_discovery`
- `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`

The dialog report records 1031 LOC versus 1219 discovered LOC; the SOLID prose snapshot
also differs from live metrics. These exactly match the earlier filed baseline evidence.
Module/class cap checks passed. No historical snapshot was rewritten.

### Bounded install timeout: PYPOST-1299

[PYPOST-1299](https://pypost.atlassian.net/browse/PYPOST-1299) covers:

- `tests/test_pytest_exit_policy.py::test_make_test_fails_closed_when_parallel_runner_is_missing`

The fixture's nested `make install` timed out after 60 seconds, matching the filed timeout
cluster. This test/docs task does not change its Make recipe, fixture, or install inputs.

### Flake8 reporter failure: PYPOST-1363

[PYPOST-1363](https://pypost.atlassian.net/browse/PYPOST-1363), estimated at 5 SP and verified
by the runner, covers the two exact nodes:

- `tests/test_makefile_exit_behavior.py::TestExitBehavior::test_lint_succeeds_from_bare_venv_via_venv_test`
- `tests/test_makefile_target_filtering.py::TestTargetFiltering::test_lint_succeeds_after_install`

Both nested lint commands raised `KeyError: 'default'` in flake8 reporter selection.
The unchanged narrow retry reproduced both failures in 22.11 seconds:
`/tmp/pypost1356-step4-fixture-retry.log`. The observed flake8 version was 7.4.1.
Stale/corrupt prewarmed metadata is an unconfirmed hypothesis, not a proven cause.

Baseline equivalence is concrete: the complete fixture build inputs have an empty diff
against the task base (`Makefile`, `pyproject.toml`, parallel runner, fixture helper,
and both failing modules). The fixture copies Makefile/runner, writes a minimal project,
and hardlinks a prewarmed venv. It never includes the new acceptance test or user documents.
The roadmap records the exact retry command. No broad rerun or dependency-environment mutation
was needed to establish that this task cannot affect the seeded lint inputs.

### Previously filed issues not observed here

[PYPOST-1298](https://pypost.atlassian.net/browse/PYPOST-1298) tracks shared Make-fixture
lock/time-budget failures; the reporter failure above is distinct.
[PYPOST-1362](https://pypost.atlassian.net/browse/PYPOST-1362) tracks the registry failed-bind
race. Neither produced an additional failure in this gate. They are not new task findings.

No unticketed follow-up or task-created blocker remains.
