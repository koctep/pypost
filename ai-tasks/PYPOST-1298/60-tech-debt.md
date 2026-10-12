# PYPOST-1298: Technical Debt Analysis

## Assessment

The accepted helper and runner implement the scoped requirements: readiness is published after
validation, lock waiting and prerequisite commands share a deadline, failed attempts permit retry,
and selected Make fixtures prepare before worker dispatch. No unresolved task-caused defect or
blocking debt was found. The full gate remains baseline-relative because the separately tracked
failures below persist. No application code, dependency versions, or test deadlines changed.

This analysis inspected the changed helper/runner code, readiness and dispatch regressions,
[requirements](10-requirements.md), [architecture](20-architecture.md), and prior Make evidence in
the [roadmap](00-roadmap.md). It does not claim the whole repository is debt-free.

## Shortcuts Taken

None requiring a follow-up. The existing `cp -al` materialization and Python-version-specific
shared temporary root remain the selected architecture. Prepared bases are reused through the
marker plus interpreter predicate; imports are validated before first publication rather than
on every cache hit. This relies on the documented immutable prepared-base assumption.

The helper retains the existing Unix/Linux tooling contract (`fcntl.flock`, `cp -al`, and
process groups). The descendant regression also reads Linux `/proc`. Cross-platform portability
is outside this issue's accepted scope; no portability layer or follow-up is newly promised.
Hardlinks preserve existing fixture semantics rather than introducing a new workspace copy model.

The runner selects preparation when the helper exists and discovery includes top-level
`tests/test_makefile_*.py` units. That deliberately includes some contract-only files. A future
fixture consumer outside this family must update the selection rule, as already required by the
architecture; no current uncovered consumer was identified that warrants a speculative ticket.

## Code Quality Issues

None introduced that require remediation. Deadline handling, cleanup, and failure conversion
remain narrow helper/runner functions. The helper polls only contention errors (`EACCES` and
`EAGAIN`); other lock errors propagate rather than silently retrying.

Scoped flake8 found two E203 diagnostics and one T201 CLI print in the inherited runner; the
unmodified baseline reproduced all three outside changed lines. Standard `make lint` passes.
These are recorded in [Code Cleanup](40-code-cleanup.md), with baseline/scoped logs, and are not
new debt attributed to this issue.

## Missing Tests

No blocking coverage gap was identified for the accepted requirements. The 13 readiness cases
cover concurrent independent consumers, single-builder publication, stale cache and marker-only
readiness, cumulative budgets, lock expiry/errors, bootstrap timeout/nonzero retry, partial-copy
retry, and real descendant termination on timeout and nonzero exit. The 60 runner cases include
normal/coverage preparation order, zero dispatch and failing reports after preparation rejection,
and unrelated/helper-free exclusions.

Both changed test modules declare explicit timeout markers (30-second readiness module,
60-second runner module, with existing narrower overrides). Event waits, subprocess calls,
process joins, and polling loops in the new regressions are bounded. No marker omission exists
in this change.

Preparation-stage ERROR logging is not newly introduced. Exact preparation event fields were
checked by source inspection; the new regressions primarily assert dispatch/report behavior,
while existing caplog tests exercise the shared lifecycle and validation event helpers. This is
an explicit validation limit, not a claim of a new dedicated preparation-event caplog test.

Offline bootstrap regressions mock package-service work. The normal full Make gate additionally
exercises actual fixture materialization and Make behavior. No live package-service fault
injection or real coverage-enabled full-suite run is claimed; coverage rejection and ordering are
tested at the runner boundary. No concrete missing requirement justifies a new follow-up here.

## Performance Concerns

No unresolved shared-preparation timeout remained in the final normal eight-worker full gate.
It dispatched 392 files: 378 passed, seven failed, seven filtered. There were zero shared
preparation or materialization timeouts. The later cleanup correction and formatting change
passed all 73 focused cases; the full suite was not repeated for those narrowly covered changes.

Cold runner preparation uses a 90-second cumulative budget and 95-second watchdog; ordinary
helper preparation uses 20 seconds plus reserved cleanup. The materialization command uses
20 seconds plus one second for termination. These explicit constants are chosen engineering
bounds, not accidental hardcoded business values.

The original five-second materialization bound failed even serial trials. A 14-second command
trial succeeded for affected fixtures but still timed out under normal full-suite load. The
accepted architecture was corrected to the final 21-second total bound, retaining nine seconds
of the shortest existing 30-second test deadline for recipe assertions. This is a reviewed design
adjustment rather than unresolved architecture deviation. Earlier trial logs and outcomes are
preserved in the roadmap. Network availability, process creation, and filesystem responsiveness
remain the documented environmental assumptions; no guarantee for a stalled OS is claimed.

The unstable collection-import CPU assertion remains tracked separately under PYPOST-1338.
No new application performance concern was found in this test-infrastructure change.

## Follow-up Tasks

No new follow-up issue is required for the implementation. Existing Jira issues were deduplicated
by the orchestrator; this step creates no Jira issues or changes their state. The following are
**NON-BLOCKER — pre-existing**, with the performance item specifically classified as flaky.
The task base is `fd830ea8`; baseline evidence came from
`/tmp/baseline-PYPOST-1298-step4` with its own relative `.venv`.

For each test below, join the module and suffix with `::` to obtain its exact node id.

### Flake8 Reporter: PYPOST-1363

[PYPOST-1363](https://pypost.atlassian.net/browse/PYPOST-1363) owns these two failures:

- Module: `tests/test_makefile_exit_behavior.py`.
  Suffix: `TestExitBehavior::test_lint_succeeds_from_bare_venv_via_venv_test`.
- Module: `tests/test_makefile_target_filtering.py`.
  Suffix: `TestTargetFiltering::test_lint_succeeds_after_install`.

Both reproduce at `fd830ea8` with flake8 reporter `KeyError: 'default'` and nested Make lint
exit 2. Baseline tracebacks: `/tmp/pypost-1298-step4-baseline-reporter.log`.
Current tracebacks: `/tmp/pypost-1298-step4-check-21s.log`. This is the existing reporter issue,
not readiness lock or materialization failure.

### Audit Snapshots: PYPOST-1361

[PYPOST-1361](https://pypost.atlassian.net/browse/PYPOST-1361) owns these three failures:

- Module: `tests/test_pypost_1077_verification_artifacts.py`.
  Suffix: `test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`.
- Module: `tests/test_pypost_1287_failing_repro.py`.
  Suffix: `test_live_report_inventory_loc_matches_discovery`.
- Module: `tests/test_solid_audit_baseline.py`.
  Suffix: `TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`.

All reproduce at `fd830ea8`: recorded dialog LOC 1031 versus discovered 1219, mismatched live
inventory LOC dictionary, and Markdown metrics 459 versus 462 respectively. Baseline assertions:
`/tmp/pypost-1298-step4-baseline-other.log`; current assertions:
`/tmp/pypost-1298-step4-check-21s.log`.

### Exit-Policy Installation Timeout: PYPOST-1299

[PYPOST-1299](https://pypost.atlassian.net/browse/PYPOST-1299) owns:

- Module: `tests/test_pytest_exit_policy.py`.
  Suffix: `test_make_test_fails_closed_when_parallel_runner_is_missing`.

The exact baseline node raises `subprocess.TimeoutExpired` after its fixture's nested
`make install` exceeds 60 seconds. The complete module also reaches the 120-second worker
watchdog at baseline and current tree. Exact-node baseline traceback:
`/tmp/pypost-1298-step4-baseline-precise.log`; baseline module watchdog:
`/tmp/pypost-1298-step4-baseline-other.log`; current gate:
`/tmp/pypost-1298-step4-check-21s.log`. This occurs in its separate install fixture and is not a
shared-preparation or copy timeout. Root cause beyond the observed install stall was not
investigated by this task.

### Collection-Import CPU Flake: PYPOST-1338

[PYPOST-1338](https://pypost.atlassian.net/browse/PYPOST-1338) owns:

- Module: `tests/test_collection_import_profile.py`.
  Suffix: `test_plan_collection_import_large_dataset_performance`.

Verdict: **NON-BLOCKER — pre-existing/flaky**. The first full gate passed this module; later
unchanged-tree gates failed at 108.83 and 138.11 ms against a 100 ms thread-CPU assertion.
The exact-node unchanged-tree rerun and baseline `fd830ea8` exact-node rerun both passed.
No failure rate beyond those observations is inferred. Failure:
`/tmp/pypost-1298-step4-check-21s.log`; unchanged-tree rerun:
`/tmp/pypost-1298-step4-performance-rerun.log`; baseline rerun:
`/tmp/pypost-1298-step4-baseline-precise.log`. The orchestrator added the new evidence to the
existing issue. Root cause was not investigated here.

## Make Verification Evidence

- Full normal gate: `make check`, log `/tmp/pypost-1298-step4-check-21s.log`.
  Lint passed; tests had only the seven documented failure files; fixture timeouts were zero.
- Focused final validation:
  `make test PYTEST_ARGS='tests/test_makefile_shared_readiness.py
  tests/test_run_parallel_tests.py --tb=short'` (arguments form one line).
  All 73 cases passed; log `/tmp/pypost-1298-step5-focused.log`.
- `make verify-ai-tasks` passed separately after the baseline-relative full-gate failure;
  log `/tmp/pypost-1298-step4-verify-final.log`.
- Step 5/6 `make lint` passed; scoped runner baseline diagnostics and supplemental Make
  checks are documented in [Code Cleanup](40-code-cleanup.md).
- Step 7 `make lint` passed, including Markdown lint and relative documentation links.

### Exact Baseline and Rerun Commands

These are the historical Make invocations supplied by the Step 4 executor. To recover each
single-line command below, concatenate its lines without inserting separators, preserving the
leading space on lines that start a new argument. Node-id fragments are split only for width.
All three baseline commands ran in `/tmp/baseline-PYPOST-1298-step4` at `fd830ea8`, with its own
relative `.venv` and no `VENV` override.

Reporter baseline, `/tmp/pypost-1298-step4-baseline-reporter.log`:

```text
make test PYTEST_ARGS='tests/test_makefile_exit_behavior.py::TestExitBehavior::
test_lint_succeeds_from_bare_venv_via_venv_test
 tests/test_makefile_target_filtering.py::TestTargetFiltering::test_lint_succeeds_after_install
 --tb=short'
```

Snapshot/module-watchdog baseline, `/tmp/pypost-1298-step4-baseline-other.log`:

```text
make test PYTEST_ARGS='tests/test_pypost_1077_verification_artifacts.py::
test_dialog_audit_report_has_full_discovery_and_coherent_aggregates
 tests/test_pypost_1287_failing_repro.py::test_live_report_inventory_loc_matches_discovery
 tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::
test_markdown_snapshot_matches_current_metrics
 tests/test_pytest_exit_policy.py --tb=short'
```

Exact exit-policy and performance baseline, `/tmp/pypost-1298-step4-baseline-precise.log`:

```text
make test PYTEST_ARGS='tests/test_collection_import_profile.py::
test_plan_collection_import_large_dataset_performance
 tests/test_pytest_exit_policy.py::test_make_test_fails_closed_when_parallel_runner_is_missing
 --tb=short'
```

Unchanged-tree performance rerun in `/home/src`,
`/tmp/pypost-1298-step4-performance-rerun.log`:

```text
make test PYTEST_ARGS='tests/test_collection_import_profile.py::
test_plan_collection_import_large_dataset_performance --tb=short'
```

The roadmap preserves earlier budget trials. No tests or code changed during this analysis;
repeated full-suite execution was unnecessary. STEP 7 stays in progress until independent review
and orchestrator acceptance.
