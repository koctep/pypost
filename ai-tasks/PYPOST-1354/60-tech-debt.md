# PYPOST-1354: Technical Debt Analysis

## Shortcuts Taken

No temporary production stubs, template writes, dialog-owned storage, origin-name heuristics, or
bypassed persistence acknowledgments remain. Copy creation follows the accepted canonical-owner
and asynchronous acknowledgment design.

Busy storage rejects a new copy and permits retry after draining. This is the accepted admission
contract, not deferred queue support: it prevents the gateway's queued-save coalescing from
being mistaken for the copy's durable acknowledgment. Negative correlation sequences keep copy
completion separate from existing request-update sequences. These are deliberate scoped design
choices, rather than a general transaction system.

## Code Quality Issues

No task-introduced correctness or maintainability blocker was identified in the reviewed scope.
The cohesive creation helper keeps the presenter within existing size caps; those caps and test
assertions were retained. The narrow gateway cleanup removes only a failed staged environment
from a queued snapshot and preserves the associated request-update sequences.

The repository still has 181 known mypy baseline errors. The task adds no baseline differences.
This records the inherited type-checking policy, not a new request to fix unrelated code.

## Missing Tests

The 18-case repro covers immutable sanitized derivation, exact provenance after persistence,
collision repair, optional manual selection, missing ownership, delayed acknowledgment,
rejection/exception/failure/incomplete UI outcomes, source changes, closed editors, canonical
ownership and wiring, teardown admission, synchronous failure/retry, and controlled real
encrypted gateway success/failure with unrelated queued updates.

All new tests use the explicit module-level 30-second timeout and bounded worker/event-loop gates.
Diagnostic assertions check lifecycle outcomes and absence of private values, names, and raw
exception content in new logs. No missing timeout marker or proven unmet acceptance criterion
was identified.

Coverage is focused rather than exhaustive: incomplete UI completion is simulated, while real
gateway persistence failure and acknowledgment are exercised. The suite does not simulate every
possible operating-system crash or worker exceeding its teardown deadline. This limitation is
not evidence that accepted behavior failed; a concrete reproduction would require assessment
before being classified as an acceptance blocker or follow-up.

## Performance Concerns

Derivation copies only the selected template. Collision checks, highlighting, queued failure
cleanup, and publication use linear scans over workspace environments. Existing gateway
persistence already copies the workspace snapshot. No measured performance regression or
optimization requirement was observed, so no speculative optimization follow-up is proposed.

## Follow-up Tasks

No new implementation follow-up is proposed. The following existing Jira issues own the
classified pre-existing validation failures. They remain **NON-BLOCKER — pre-existing** for
PYPOST-1354; acceptance gaps must not be hidden under that classification.

### PYPOST-1361: Stale validation snapshots

**NON-BLOCKER — pre-existing** — [PYPOST-1361][snapshots]. These exact tests failed at the task's
base commit `0890b8dc`: the dialog report recorded 1,031 lines versus the base's 1,112, and the
SOLID snapshot stored stale presenter/controller counts. Task growth exposes the same drift.

```text
tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates
tests/test_pypost_1287_failing_repro.py::test_live_report_inventory_loc_matches_discovery
tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics
```

### PYPOST-1362: Registry bind-failure teardown race

**NON-BLOCKER — pre-existing** — [PYPOST-1362][registry-race]. The same assertion failed at
`0890b8dc`: the failed-bind signal arrived while `beta-server` still reported running. The
current isolated module retry passed, consistent with the filed race.

```text
tests/test_mcp_server_registry.py::test_failed_bind_is_reported_for_only_the_requested_instance
```

### PYPOST-1298: Makefile infrastructure timeouts

**NON-BLOCKER — pre-existing** — [PYPOST-1298][make-timeouts]. Full-suite fixture setup timed
out in shared-prewarm installation/locking; later workers exceeded their bounded 120-second
budget. One unchanged narrow retry passed recipes and markers but retained other infrastructure
timeouts. Makefile and fixture helpers were not changed by this task. The contaminated baseline
fixture run with a propagated absolute VENV override was discarded and is not evidence here.

Exact failed/error nodes and nodes executing when the bounded worker was stopped:

```text
tests/test_makefile_exit_behavior.py::TestExitBehavior::test_clean_exits_zero_on_empty_tree
tests/test_makefile_exit_behavior.py::TestExitBehavior::test_unknown_target_exits_nonzero
tests/test_makefile_exit_behavior.py::TestExitBehavior::test_lint_succeeds_from_bare_venv_via_venv_test
tests/test_makefile_install_stamp_contract.py::TestInstallExtraStampContract::test_install_touches_both_extra_stamps
tests/test_makefile_install_stamp_contract.py::TestInstallExtraStampContract::test_install_stamps_allow_skip_pip_on_venv_test_otel
tests/test_makefile_markers.py::TestMarkerLifecycle::test_venv_creates_version_marker
tests/test_makefile_markers.py::TestMarkerLifecycle::test_clean_removes_venv_and_marker
tests/test_makefile_markers.py::TestMarkerLifecycle::test_venv_is_idempotent
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
tests/test_makefile_recipes.py::TestHelpTarget::test_help_prints_non_empty_output
tests/test_makefile_recipes.py::TestHelpTarget::test_help_lists_test_agent_e2e
tests/test_makefile_recipes.py::TestHelpTarget::test_help_frames_test_agent_e2e_broader_beyond_golden
tests/test_makefile_stamp_otel_idempotency.py::TestVenvOtelStampIdempotency::test_venv_otel_skips_pip_when_current
tests/test_makefile_stamp_otel_idempotency.py::TestVenvOtelStampIdempotency::test_venv_otel_installs_when_stamp_missing
tests/test_makefile_stamp_otel_idempotency.py::TestVenvOtelStampIdempotency::test_venv_otel_installs_when_stamp_stale
tests/test_makefile_stamp_otel_idempotency.py::TestVenvOtelStampIdempotency::test_venv_otel_depends_on_stamp
tests/test_makefile_stamp_test_idempotency.py::TestVenvTestStampIdempotency::test_venv_test_skips_pip_when_current
tests/test_makefile_stamp_test_idempotency.py::TestVenvTestStampIdempotency::test_venv_test_installs_when_stamp_missing
tests/test_makefile_stamp_test_idempotency.py::TestVenvTestStampIdempotency::test_venv_test_installs_when_stamp_stale
tests/test_makefile_stamp_test_idempotency.py::TestVenvTestStampIdempotency::test_venv_test_depends_on_stamp
tests/test_makefile_target_filtering.py::TestTargetFiltering::test_make_test_excludes_slow_marker
tests/test_makefile_target_filtering.py::TestTargetFiltering::test_pytest_args_narrows_test_run
tests/test_makefile_target_install_test.py::TestTargetInstallTest::test_venv_test_installs_pytest_and_flake8
tests/test_makefile_target_install_test.py::TestTargetInstallTest::test_test_succeeds_after_install
```

### PYPOST-1299: Exit-policy worker timeout

**NON-BLOCKER — pre-existing** — [PYPOST-1299][exit-policy]. The full gate and bounded narrow
retry exceeded the exit-policy worker budget; the observed failing/running nodes were:

```text
tests/test_pytest_exit_policy.py::test_make_test_fails_closed_when_parallel_runner_is_missing
tests/test_pytest_exit_policy.py::test_make_test_cov_fails_closed_when_parallel_runner_is_missing
```

## Validation Evidence

The initial full gate reported 389 files: 368 passed, 14 failed, seven skipped. Its task-caused
presenter size-cap violation was corrected by extracting the creation helper; focused audit-cap
verification passed. The final focused 11-module run passed, and the Step 6 repro/presenter/gateway
run also passed. Static analysis, mypy baseline comparison, and task artifact verification passed.
Earlier sprint baseline tickets PYPOST-1358, PYPOST-1359, and PYPOST-1360 describe different
historical checks; they are not used to classify the failures listed above.

[snapshots]: https://pypost.atlassian.net/browse/PYPOST-1361
[registry-race]: https://pypost.atlassian.net/browse/PYPOST-1362
[make-timeouts]: https://pypost.atlassian.net/browse/PYPOST-1298
[exit-policy]: https://pypost.atlassian.net/browse/PYPOST-1299
