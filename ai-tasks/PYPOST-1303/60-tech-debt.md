# PYPOST-1303: Technical Debt Analysis

## Shortcuts Taken

The issue explicitly authorizes correcting or transparently baselining legacy test findings.
The implementation freezes 409 pre-existing occurrences in 375 exact identities instead of
rewriting hundreds of unrelated behavioral-test lines. Each entry carries its deferred-adoption
reason. This is disclosed existing debt, not permission to add findings or suppress a category.

The initial capture asserted the measured 409-occurrence total before the new checker tests
were added. `make lint` and the full gate retain that exact count. Production lint and docs
checks remain; F401/E501/T201 detection is active for new test findings. No test assertions,
inclusion rules, or deadlines were weakened.

## Code Quality Issues and Trade-offs

### Narrow Occurrence Baseline

Identity combines relative test path, code, normalized diagnostic text, and stripped physical
source text. A multiset count handles duplicate occurrences. Current row/column are diagnostic
output only; they are excluded from identity to tolerate unrelated preceding edits. Only F811
`from line N` references are normalized. Source/message fragments keep JSON readable within
100 columns, and validation limits individual fragments to 60 characters.

An identical replacement in the same file with unchanged code/message/source/count is
inherently indistinguishable from the accepted occurrence. Moving such an occurrence within
the same file is also indistinguishable. This is the documented identity boundary, not a new
untracked defect. Different source statements and increased duplicate counts fail. Resolved
allowances fail until explicitly pruned, closing the ordinary remove/reintroduce sequence.

Pruning removes only resolved counts after a validated scan. It refuses new findings and
tool/schema/source errors, preserves remaining reasons, and replaces the baseline atomically.
Normal lint is read-only. There is no automatic growth or baseline-acceptance command;
deliberate policy or inventory edits remain subject to code review and Jira scope.

### Tool and Workspace Assumptions

- The installed dev environment supplies flake8 and flake8-print. The scan explicitly requires
  the latter, preventing silent loss of T201. Measured versions were 7.4.1 and 5.0.0 respectively.
- Diagnostic text and source locations come from that installed tool/configuration. A future
  tool/config change may cause new/fixed identity differences and requires deliberate review;
  the checker will fail rather than silently accepting drift.
- The finite 60-second timeout bounds the flake8 subprocess. Process launch, local source
  reads, JSON parsing, and atomic filesystem operations assume a responsive local OS/filesystem;
  there is no claim of a hard total wall-clock bound under an unresponsive filesystem.
- Scans and explicit pruning assume a stable checkout. Atomic replacement prevents a partial
  baseline file, but there is no concurrent-edit transaction spanning flake8, source lookup,
  and a separate developer's modifications. Such concurrent mutation is not a supported gate
  workflow or a requirement of this issue.
- Isolated Make fixtures receive the real checker/config and an empty inventory for their
  miniature tree. Missing assets or plugin failures are errors; no checker bypass was added.

No additional concrete refactoring or new task-caused quality defect was identified.

## Missing Tests

No acceptance-critical coverage gap or missing explicit timeout was found. Actual offline Make
regressions cover clean success, new F401/E501/T201 rejection, and production F401 protection.
Checker regressions cover identities/counts, stale debt, prune-only writes and atomic failure,
schema/duplicate validation, source failures/escapes, plugin requirement, contradictory or
unparseable tool output, timeout/launch failures, and unchanged baseline bytes on normal runs.

The Make prune target's small CLI wiring was inspected; prune policy and file replacement are
exercised through the same CLI in private workspaces. A separate real-process test for every
schema/error permutation is unnecessary alongside those unit checks and actual Make scans.
All task-owned tests declare timeout markers; subprocess waits are bounded.

## Performance Concerns

The checker runs flake8 with one job, matching the existing lint policy, then performs linear
diagnostic parsing and Counter comparisons. Parsed source lines are cached per file. The
baseline size is modest (375 identities); no measured optimization need was found. Success
prints one count summary rather than dumping baseline entries or source fragments.

Accepted full verification: normal eight-worker `make check`, 395 files, 383 passed, 5 existing
failures, 7 unchanged skips, 250.31 seconds. No task-caused failure or timeout occurred.
Log: `/tmp/pypost-1303-step4-check.log`. The checker suite and static checks also pass after
cleanup; see `/tmp/pypost-1303-step5-tests.log` and `/tmp/pypost-1303-step5-lint.log`.

## Follow-up Tasks

No new follow-up issue is necessary for this implementation. The authorized legacy adoption
does not justify fabricating one ticket per finding or broad unrelated cleanup. Existing
tracked full-gate failures remain NON-BLOCKER — pre-existing, as recorded below.

### Reporter Failures: PYPOST-1363

[PYPOST-1363](https://pypost.atlassian.net/browse/PYPOST-1363) already owns these exact nodes.
Join each module and suffix with `::`:

- `tests/test_makefile_exit_behavior.py` +
  `TestExitBehavior::test_lint_succeeds_from_bare_venv_via_venv_test`.
- `tests/test_makefile_target_filtering.py` +
  `TestTargetFiltering::test_lint_succeeds_after_install`.

Current failures report flake8 reporter `KeyError: 'default'` and nested Make exit 2. Current
logs: `/tmp/pypost-1303-step4-fixtures.log` and `/tmp/pypost-1303-step4-check.log`. The new
checker propagates that unavailable diagnostic capability rather than treating it as success.

### Audit/Snapshot Failures: PYPOST-1361

[PYPOST-1361](https://pypost.atlassian.net/browse/PYPOST-1361) already owns these exact nodes.
Join each module and suffix with `::`:

- `tests/test_pypost_1077_verification_artifacts.py` +
  `test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`.
- `tests/test_pypost_1287_failing_repro.py` +
  `test_live_report_inventory_loc_matches_discovery`.
- `tests/test_solid_audit_baseline.py` +
  `TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`.

Current inventory/LOC and Markdown snapshot assertion failures appear in
`/tmp/pypost-1303-step4-check.log`. This task changes no application source or audit snapshots.

### Baseline Provenance

All five nodes already failed with matching causes in `/tmp/pypost-1299-step4-check.log`, the
normal gate run on the tree subsequently committed as task base `be94b7e4`. Historical
isolated `fd830ea8` evidence additionally confirms the reporter pair in
`/tmp/pypost-1298-step4-baseline-reporter.log`. This record does not claim a fresh
`be94b7e4` worktree rerun. Exact reproduction commands and classifications are preserved in
the roadmap and the earlier tasks' debt records; the current full reproduction is `make check`.
