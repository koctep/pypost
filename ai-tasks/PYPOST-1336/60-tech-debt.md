# PYPOST-1336: Technical Debt Analysis

## Shortcuts Taken

No production shortcut was introduced. This task delivers only decomposition notes and
estimated Jira issues; production code, tests and bundled fixtures remain outside its scope.
The coverage table in [decomposition.md](../PYPOST-1335/decomposition.md) maps E1–E8 to the
nine children and the explicit no-migration exclusion. All nine children have binding
estimates of at most 5 SP, totaling 37 SP, with an acyclic execution order.

C1a, C1b and C7 were planned as Tasks but created as Stories because Jira rejects Task in
this project. This documented type adjustment changes neither their scope nor acceptance
criteria. No implementation architecture deviation or temporary runtime workaround was added.

## Code Quality Issues

There is no changed production code to refactor. The approved design retains one examples
source, a shared locator, a filtered Built-in view and explicit legacy compatibility guards.
Stable library identifiers and the three curated collection entries are intentional domain
identities, not undocumented hardcoded replacements for configuration.

The existing ordinary-library lifecycle defect is tracked separately as PYPOST-1347 below.
Keeping it outside the Built-in epic follows E8; Built-in lifecycle behavior remains assigned
to PYPOST-1352. Its later fix can widen the Built-in branch rather than duplicate its logic.

## Missing Tests

No test was authored or edited. A failing behavioral repro is N/A because this planning
task changes no application behavior; its specified gate is `make verify-ai-tasks`.
No newly introduced test lacks an explicit timeout marker.

Epic implementation coverage is deferred to the assigned children, not silently omitted:
packaging and seed guards (PYPOST-1348), locator branches (PYPOST-1349), manifest consistency
(PYPOST-1350), runtime and daemon startup (PYPOST-1351), lifecycle and transactional save
(PYPOST-1352), dialog compatibility (PYPOST-1353), safe environment and collection copies
(PYPOST-1354/PYPOST-1355), and offline upgrade/copy end-to-end coverage (PYPOST-1356).
Each implementation task owns bounded tests and its own Make quality gate.

## Performance Concerns

No runtime path, request processing or resource usage changes, so no new performance debt
is introduced. Re-reading a shipped collection on start is the approved update behavior;
its runtime verification belongs to PYPOST-1351 and PYPOST-1356. The pre-existing test
worker and nested installation timeouts below are tracked execution reliability concerns.

## Follow-up Tasks

All follow-ups already have Jira issues. No new issue or unrelated repair is needed here.
The following filed baseline-relative failures do not block this documentation-only task.

### PYPOST-1347 — Ordinary library MCP lifecycle

**NON-BLOCKER — pre-existing.**
[PYPOST-1347](https://pypost.atlassian.net/browse/PYPOST-1347) is Debt, 3 SP, outside epic
PYPOST-1335 and sprint 2025. Ordinary library rows have `collection_id=None`; registry
reconciliation stops them as missing collections, replacement validation rejects them, and
environment refresh drops manifest defaults, preset and overlay values. This is the
read-only architecture finding recorded in `20-architecture.md`, not a new tested change.
The existing Debt acceptance criteria require red regressions for all three defects and
preservation of workspace behavior. No failing test node is claimed for this design finding.

### Shared test evidence and reproduction

The task base is `31f2b25a1fcacf490c5136c25ac4dac57ec41b06`. Original `make test`:
381 files, 364 passed, 10 failed, 7 skipped. Clean baseline evidence uses a throwaway
worktree at that commit and its own virtual environment, installed through `make install`.
The current and valid baseline focused command is exactly equivalent to:

```bash
make test WORKERS=4 PYTEST_ARGS='tests/test_collection_export_ui.py '\
'tests/test_makefile_exit_behavior.py tests/test_makefile_install_stamp_contract.py '\
'tests/test_makefile_markers.py tests/test_makefile_recipes.py '\
'tests/test_makefile_stamp_otel_idempotency.py tests/test_makefile_stamp_test_idempotency.py '\
'tests/test_makefile_target_filtering.py tests/test_makefile_target_install_test.py '\
'tests/test_pytest_exit_policy.py -m "not slow"'
```

The adjacent shell string fragments concatenate without added characters. Node arrays below
use the same syntax for long identifiers, preserving full node IDs within the 100-column
Markdown limit; each array element is one exact identifier.

The refreshed current run passes eight of the ten files; target-filtering and exit-policy
workers still time out. The clean baseline passes five; stamp modules, target-filtering,
target-install and exit-policy exceed their 120-second file budgets. File worker timeouts
are process failures, not evidence that every contained assertion failed.

An initial baseline invocation with an absolute shared `VENV` override is invalid and
excluded: nested Makefile clean removed the shared environment. Its pending UI invocation
was cancelled. The root environment was restored via `make install`; the editable package
again points to `/home/src`. The refreshed dependencies include PySide6 6.11.1 and
pydantic 2.14.0. These runs cannot establish dependency identity with the original failures.

Full logs referenced by [40-code-cleanup.md](40-code-cleanup.md):
`/tmp/pypost-sprint-2025-test.log`, `/tmp/pypost-1336-current-focused.log`,
`/tmp/pypost-1336-baseline-clean.log`, `/tmp/pypost-1336-exit-policy-node.log`, and
`/tmp/pypost-1336-exit-policy-baseline-node.log`. No test assertion was altered.

### PYPOST-1298 — Makefile shared-fixture and worker timeouts

**NON-BLOCKER — pre-existing.**
[PYPOST-1298](https://pypost.atlassian.net/browse/PYPOST-1298) tracks the existing shared
Makefile fixture locking failures. Refreshed fixture setup passes; baseline file worker
timeouts persist for stamp and target modules. The cumulative worker timeout root cause
has not been investigated; the existing fixture flock explains original setup failures
without proving that every later worker timeout has the same cause.

Baseline excerpts show `exit_code=-9`, `duration_seconds=120.04` for both stamp modules,
and `worker timeout after 120.0s` while their stale-stamp nodes are active. Target-filtering
has the same timeout while its narrowing node is active. Target-install times out at its
final node after three passes; its refreshed current run passes. The original fixture
node inventory is preserved in the linked PYPOST-1298 Jira evidence. The active nodes at
baseline worker termination are the following exact identifiers:

```bash
nodes=(
"tests/test_makefile_stamp_otel_idempotency.py::TestVenvOtelStampIdempotency::"\
"test_venv_otel_installs_when_stamp_stale"
"tests/test_makefile_stamp_test_idempotency.py::TestVenvTestStampIdempotency::"\
"test_venv_test_installs_when_stamp_stale"
"tests/test_makefile_target_filtering.py::TestTargetFiltering::test_pytest_args_narrows_test_run"
"tests/test_makefile_target_install_test.py::TestTargetInstallTest::test_test_succeeds_after_install"
)
```

### PYPOST-1299 — Missing parallel runner exit-policy installation hangs

**NON-BLOCKER — pre-existing.**
[PYPOST-1299](https://pypost.atlassian.net/browse/PYPOST-1299) tracks these exact nodes:

```bash
nodes=(
"tests/test_pytest_exit_policy.py::test_make_test_fails_closed_when_parallel_runner_is_missing"
"tests/test_pytest_exit_policy.py::"\
"test_make_test_cov_fails_closed_when_parallel_runner_is_missing"
)
```


The focused module worker fails its first node after 60 seconds and times out at 120 seconds
while the second is active. Independent current and clean-base reproduction of the first:

```bash
make test-slow PYTEST_ARGS='tests/test_pytest_exit_policy.py::'\
'test_make_test_fails_closed_when_parallel_runner_is_missing -vv'
```

Both raise `subprocess.TimeoutExpired` from nested `make install` after 60 seconds.
Current: `make PYTHON=/home/src/.venv/bin/python install`, 60.06-second test duration.
Base: `make PYTHON=/tmp/baseline-PYPOST-1336/.venv/bin/python install`, 60.26 seconds.
Both standalone runs end with one failed test and Make Error 1. This is the same exception
at the base commit; the installation hang root cause has not been investigated.

### PYPOST-1357 — Environment-sensitive collection-export worker crash

**NON-BLOCKER — pre-existing, environment-sensitive.**
[PYPOST-1357](https://pypost.atlassian.net/browse/PYPOST-1357) tracks the collection-export
worker crash, 5 SP, outside the epic and sprint. The original and two unchanged current
reruns exit -11 after all 19 assertions pass, failing the process-level gate. Reproduction:

```bash
make test WORKERS=1 PYTEST_ARGS='tests/test_collection_export_ui.py -m "not slow"'
```

The excerpt ends with the final forwarding test `PASSED [100%]`, followed by
`Total Files: 1 | Passed: 0 | Failed: 1 | Skipped: 0` and Make Error 1.
Refreshed current reruns and the valid clean baseline pass with worker exit 0. Dependency
refresh therefore limits the conclusion to an environment-sensitive pre-existing defect;
it does not prove the original environment's crash at base. The earlier triage draft's
baseline-pending note is superseded by Step 5's clean baseline evidence. Root cause has not
been investigated; teardown is only a suspicion. All 19 exact node IDs and the original
failure excerpt are preserved in the linked PYPOST-1357 Jira evidence. This is a module
worker failure after passing assertions, rather than an individual assertion failure.
The final node before termination is:

```bash
nodes=(
"tests/test_collection_export_ui.py::TestExportCollectionSourcePrecedence::"\
"test_presenter_export_collection_at_index_forwards_source_index"
)
```

## Validation and Review

This artifact documents no newly introduced blocker. Production changes, test fixes,
dependency pinning and user-facing documentation are not part of this step. Artifact
integrity is validated through `make verify-ai-tasks`; Step 7 remains in progress pending
the independent review gate.
