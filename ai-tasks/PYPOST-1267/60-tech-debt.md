# PYPOST-1267: Technical Debt Analysis

## Shortcuts Taken

No temporary workaround or implementation blocker was identified. Cooperative preparation
checkpoints implement the accepted architecture; they retain the existing worker lifecycle,
callback shape, JSON-first fallback, safe YAML construction, and file-error translation.

The bounded JSON scanner became an instance-local iterative container parser during review.
This documented refinement avoids multiplying Python recursion frames and preserves successful
600/900-level JSON inputs accepted by the standard decoder. It deliberately does not enforce
the standard decoder's incidental recursion ceiling: with a callback, deeper valid containers
can be decoded where `json.loads()` without a callback would raise `RecursionError`. This is a
broader acceptance boundary, not a promise of arbitrary-depth collection-model validation.
The process recursion limit is unchanged. See the [architecture](20-architecture.md) and
roadmap's Step 4 review-fix evidence.

The `(0, 0)` preparation sentinel extends direct progress callback observations; the worker
suppresses it from GUI progress. Direct callback consumers need its documented meaning. Step 8
must carry this accepted interface extension into developer documentation; no new Jira task is
needed for work already assigned to this issue.

## Code Quality Issues

The local adapter in `pypost/core/collection_import_decode.py` carries an ongoing maintenance
cost: JSON lexical/grammar behavior adapts CPython internals, including private `_decode_uXXXX`,
and YAML checkpoints override PyYAML reader/composer/constructor methods and merge flattening.
Python or PyYAML upgrades should rerun the existing differential tests and compare affected
upstream behavior. CPython and PyYAML attribution, adaptation notes, and licenses are retained.
This dependency coupling is an explicit design choice, not an unfinished upgrade or duplicate
parsing framework requiring immediate replacement.

State remains instance-local; simultaneous imports do not mutate global decoder functions.
The private checkpoint carrier preserves callback exception identity across file/parser error
translation and fallback. Context-manager/finally paths close streams and dispose loaders,
including initialization interruption. No additional cleanup/refactoring task was identified.

The 4096-character/lookahead/assembly window and 64 Ki-character read size are intentional
bounded-work constants. They are not unexplained application limits or a maximum file size.

## Missing Tests

No missing acceptance regression or missing explicit timeout marker was identified in the
changed tests. Decoder coverage declares 30 seconds, real-file cancellation declares 150
seconds, and the modified existing progress module declares 60 seconds. Event, barrier, thread,
and future waits are bounded.

Coverage includes JSON values/errors/integer limits, Unicode and escape boundaries, long
keys/scalars/whitespace, 600/900-level arrays/objects/mixed nesting, deep ignored fields,
10,000-level cancellation and incomplete-input termination, YAML safe scalars and errors,
alias identity/recursive aliases, merge precedence and assembly cancellation, callback-origin
exception identity/cleanup, concurrent decoder isolation, and record progress/newlines.

The 11 unchanged real-file regressions exercise active loading and active lexical scanning
using files of at least 16 MiB. They include JSON, YAML, fallback YAML, bundles and retained
large scalar values, and check worker termination and cancellation outcomes. The recorded final
latencies are 1.197-1.985 ms for loading, 0.412-0.636 ms for JSON scanning, and 0.295-0.832 ms for
YAML/fallback scanning, against the accepted 1000 ms limit; see the roadmap and Step 4 evidence.

The suite does not exhaustively enumerate every possible CPython/PyYAML input or guarantee
interruptibility inside native operations. Arbitrary-depth successful model validation,
resource-exhaustion behavior, and hard real-time cancellation under storage/scheduler stalls
are outside the accepted requirements. Those boundaries do not create a missing required test.

## Performance Concerns

Cooperative JSON parsing adds Python scanning/container work and callbacks compared with the
native decoder. YAML adds bounded checkpoint counters and construction/merge checks. Imports
still retain the whole input and decoded tree; chunk lists/string pieces and merge assembly can
add temporary allocations. No streaming-memory or throughput guarantee was introduced.
The implementation avoids per-character GUI signals, logs, or metrics.

Native allocation, final joins/list assembly, numeric conversion, and inherited YAML scalar
resolver/constructor work cannot be preempted mid-operation. Checks surround these operations,
but measured large-file cancellation establishes the documented local regression bound rather
than an arbitrary-size real-time guarantee. Native operations, unresponsive storage, and
scheduling can still dominate latency outside that environment. These residual limits are
explicitly accepted in [requirements](10-requirements.md) and [architecture](20-architecture.md);
no observed acceptance-bound violation remains to justify a new optimization ticket.

## Follow-up Tasks

No new task-specific actionable follow-up or blocker was identified. Step 8 documentation
remains within PYPOST-1267. Existing unrelated flakes retain their existing Jira owners; no
additional fixes or duplicate issues are proposed.

### Existing full-suite flakes

All entries below are **NON-BLOCKER — pre-existing/flaky**, tracked by existing tickets.
Classification uses unchanged-tree reruns, not reproduction at base `0345e88c`; this report
does not claim base-commit reproduction or an entirely green full `make check` run. The full
run had 363 passed, 5 failed, and 6 skipped modules. All five failed modules passed unchanged
reruns, and all collection-import modules passed in the original run. Exact commands, traces,
and timing are in [Step 5 failure evidence](40-code-cleanup.md#full-suite-failure-evidence);
original output is `/tmp/pypost-1267-step5-check.log`.

- [PYPOST-1315](https://pypost.atlassian.net/browse/PYPOST-1315): environment-export worker
  exited with signal 11 after all eight items passed; no assertion failed. Last exact node:
  `tests/test_environment_export_ui.py::TestExportEnvironments::test_logs_completed_event`.
  Unchanged module rerun passed in 2.06 seconds.
- [PYPOST-1298](https://pypost.atlassian.net/browse/PYPOST-1298): Makefile recipe setup and
  install subprocess timeouts plus target-filtering worker timeout. Root cause/lock ownership
  was not established. Recipes/install passed unchanged in 27.86/34.62 seconds; filtering
  passed unchanged in 49.64 seconds. Exact nodes are listed below using module-qualified
  prefixes so each node is unambiguous without overlong lines.
- [PYPOST-1299](https://pypost.atlassian.net/browse/PYPOST-1299): exit-policy worker reached
  120.06 seconds; first item failed at 60.06 seconds, coverage item was active at worker kill.
  Unchanged module rerun passed in 103.56 seconds. Exact nodes use the prefix below.

For `tests/test_makefile_recipes.py::TestDependencyChain::`, the 18 setup-error node suffixes
were:

```text
test_install_depends_on_marker_only
test_test_depends_on_venv_test_venv_otel_and_marker
test_test_cov_depends_on_venv_test_venv_otel_and_marker
test_venv_test_stamp_depends_on_marker_and_pyproject
test_venv_otel_stamp_depends_on_marker_and_pyproject
test_security_audit_depends_on_install
test_lock_target_has_no_venv_prerequisites
test_lock_dev_target_has_no_venv_prerequisites
test_lock_otel_target_has_no_venv_prerequisites
test_generate_mcp_fixtures_depends_on_marker
test_check_mcp_fixtures_depends_on_marker
test_generate_license_inventory_depends_on_install
test_check_license_inventory_depends_on_install
test_run_depends_on_marker_only
test_lint_depends_on_marker_and_venv_test
test_typecheck_depends_on_marker_and_venv_test
test_test_slow_depends_on_venv_test_venv_otel_and_marker
test_test_agent_e2e_depends_on_venv_test_venv_otel_and_marker
```

For `tests/test_makefile_install_stamp_contract.py::TestInstallExtraStampContract::`, the
failed node suffix was `test_install_touches_both_extra_stamps` (60-second item timeout).

For `tests/test_makefile_target_filtering.py::TestTargetFiltering::`, the failed node suffix
was `test_make_test_excludes_slow_marker`; `test_lint_succeeds_after_install` was active at
the 120-second worker kill, without a completed assertion traceback.

For `tests/test_pytest_exit_policy.py::`, the failed node suffix was
`test_make_test_fails_closed_when_parallel_runner_is_missing`;
`test_make_test_cov_fails_closed_when_parallel_runner_is_missing` was active at worker kill,
without a completed traceback.
