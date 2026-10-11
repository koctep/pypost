# PYPOST-1355: Technical Debt Analysis

## Shortcuts Taken

No temporary stub, bypass, or demonstrated acceptance gap remains. The implementation follows
the accepted synchronous owner design: deep independent preparation, canonical save before
publication/index/tree refresh, optional callback injection, and server mutation only on Save.
Cancel retains the workspace asset. Content and metadata are preserved while identities can
change to prevent workspace lookup collisions. Shipped resources are never written.

The existing collection storage writes directly rather than atomically. The new owner attempts
one fresh-ID-only cleanup on save failure. If saving and deleting both fail, a partial file can
remain on disk, while no canonical collection/tree item is published and the editor stays on
Built-in. The original save exception remains the outcome and safe cleanup diagnostics identify
the fresh ID. This is the explicit filesystem limitation accepted in the architecture, not a
claim of crash-safe transactions. There is no observed unmet task requirement that justifies
expanding this task into a storage redesign or inventing a new follow-up.

Moving the non-dialog presentation helper to the UI directory and accepting a missing creation
capability in legacy presenter adapters were compatibility repairs, not deferred fixes.

## Code Quality Issues

The canonical public method remains on `CollectionsPresenter`; cohesive helpers own copy
preparation, persistence coordination, and editor presentation. The pure import planner is
reused for request/WebSocket reservation, with narrowly added MCP profile reservation for this
copy operation. Deep-copying before planning isolates nested presets despite the planner's
shallow preset dictionary materialization. No unrelated generic import behavior was changed.

Module/class caps remain unchanged and pass. Lint and the existing mypy baseline gate pass,
with 181 known type errors and no additions. Optional capability injection preserves older
adapters and manual editor operation. Logs contain fixed reasons, fresh IDs, and counts rather
than payloads or exception text. No task-added quality defect requiring a follow-up was found.

## Missing Tests

All 16 new repro items have an explicit module-level `pytest.mark.timeout(30)` and bounded
5000 ms fixture teardown. Busy stubs restore before teardown; no arbitrary sleep, unbounded
poll, xfail, or skipped acceptance assertion was introduced.

The tests exercise real temporary storage and canonical manager/tree behavior, editable request
lookup, repeated collection/item identity and name safety, nested content independence, source
bytes, optional capability behavior, actual dialog Save/Cancel callbacks, environment retention,
configuration association fields, and callback forwarding through application composition.
Failure tests cover admission rejection, load/save errors, partial-file cleanup, simultaneous
save/delete failure, retry, and safe diagnostic privacy. The 16-case repro and relevant regression
modules pass; independent reviews also reran the repro.

Coverage does not simulate every OS crash, disk corruption, or a complete application upgrade.
Those are outside this task's accepted storage guarantees and the broader upgrade scenario
belongs to PYPOST-1356. No demonstrated missing acceptance test or timeout blocker was found.

## Performance Concerns

Copy preparation scans workspace identities/names and deep-copies the selected collection;
canonical publication rebuilds the existing request index/tree. Storage remains synchronous
on the GUI thread as accepted. No measured slowdown or new latency requirement was observed,
so no speculative optimization issue is proposed. Admission rejects active loads/imports rather
than waiting or adding workers and lifecycle coordination.

## Follow-up Tasks

No new implementation follow-up is proposed. The full Step 4 gate reported 390 files: 369 passed,
14 failed, and 7 skipped in 361.54 seconds. Three task-caused failed modules were repaired and
focused reruns passed: `test_audit_scripts_cli.py`, `test_dialogs_audit.py`, and
`test_main_window_encrypted_startup.py`. They are not remaining debt.

The remaining 11 failed modules match the following filed pre-existing clusters. Their exact
evidence is in `/tmp/pypost1355-step4-check.log` and the [roadmap](00-roadmap.md). Prior base
reproduction/classification is retained in [PYPOST-1354 debt](../PYPOST-1354/60-tech-debt.md).
These findings do not substitute for meeting this task's acceptance requirements.

### PYPOST-1298: Make fixture infrastructure timeouts

**NON-BLOCKER - pre-existing** - [PYPOST-1298][make-timeouts]. The Makefile and fixture helpers
were not modified. The install-stamp test hit the 60-second pytest budget in `_run_make` /
subprocess communication. Other listed workers were stopped at their bounded 120-second budget.
For killed workers, the initial failed nodes have no complete traceback; the run demonstrates
the known bounded timeout cluster, not a new isolated cause reproduction.

Failed nodes and nodes executing when their workers were stopped:

```text
tests/test_makefile_install_stamp_contract.py::TestInstallExtraStampContract::test_install_touches_both_extra_stamps
tests/test_makefile_exit_behavior.py::TestExitBehavior::test_lint_succeeds_from_bare_venv_via_venv_test
tests/test_makefile_stamp_otel_idempotency.py::TestVenvOtelStampIdempotency::test_venv_otel_skips_pip_when_current
tests/test_makefile_stamp_otel_idempotency.py::TestVenvOtelStampIdempotency::test_venv_otel_installs_when_stamp_stale
tests/test_makefile_stamp_test_idempotency.py::TestVenvTestStampIdempotency::test_venv_test_skips_pip_when_current
tests/test_makefile_stamp_test_idempotency.py::TestVenvTestStampIdempotency::test_venv_test_installs_when_stamp_stale
tests/test_makefile_target_filtering.py::TestTargetFiltering::test_make_test_excludes_slow_marker
tests/test_makefile_target_filtering.py::TestTargetFiltering::test_pytest_args_narrows_test_run
tests/test_makefile_target_install_test.py::TestTargetInstallTest::test_venv_test_installs_pytest_and_flake8
tests/test_makefile_target_install_test.py::TestTargetInstallTest::test_test_succeeds_after_install
```

### PYPOST-1299: Exit-policy worker timeout

**NON-BLOCKER - pre-existing** - [PYPOST-1299][exit-policy]. The same unchanged infrastructure
suite failed its first Make exit-policy assertion and exceeded the 120-second worker budget
during the next node:

```text
tests/test_pytest_exit_policy.py::test_make_test_fails_closed_when_parallel_runner_is_missing
tests/test_pytest_exit_policy.py::test_make_test_cov_fails_closed_when_parallel_runner_is_missing
```

### PYPOST-1361: Stale dialog and SOLID snapshots

**NON-BLOCKER - pre-existing** - [PYPOST-1361][snapshots]. The historical dialog report records
1031 LOC versus the current dialog's 1219; the SOLID snapshot also stores outdated presenter /
MainWindow counts. The same snapshot drift predates this task. Actual module/class cap checks
pass; historical artifacts were not rewritten to conceal the baseline failures.

```text
tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates
tests/test_pypost_1287_failing_repro.py::test_live_report_inventory_loc_matches_discovery
tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics
```

### PYPOST-1362: Registry failed-bind race

**NON-BLOCKER - pre-existing** - [PYPOST-1362][registry-race]. The full run reproduced the exact
filed assertion: after the failed-bind signal, `beta-server` still reported running. Registry
lifecycle code was not modified by this task.

```text
tests/test_mcp_server_registry.py::test_failed_bind_is_reported_for_only_the_requested_instance
```

Historical PYPOST-1358/1359/1360 did not appear in this task's full gate and are not added as
new findings. This report leaves Step 7 in progress for independent acceptance review.

[make-timeouts]: https://pypost.atlassian.net/browse/PYPOST-1298
[exit-policy]: https://pypost.atlassian.net/browse/PYPOST-1299
[snapshots]: https://pypost.atlassian.net/browse/PYPOST-1361
[registry-race]: https://pypost.atlassian.net/browse/PYPOST-1362
