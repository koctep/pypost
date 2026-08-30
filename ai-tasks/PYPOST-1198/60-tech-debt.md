# PYPOST-1198: Technical Debt Analysis

## Shortcuts Taken

None. The change is a 2-line addition (one log field + its positional arg) that follows the
exact pattern already used by every other field on the `parallel_test_run_started` INFO log
(`scripts/run_parallel_tests.py:537-543`). No temporary workaround or "crutch" was introduced.

## Code Quality Issues

- The new `worker_timeout=%s` field uses `%s` (default `float.__repr__`/`str` formatting), same
  as the rest of the line and the same style already used by the existing `worker_timeout`
  WARNING log at line 369-371. This is consistent with local convention, but it means
  `worker_timeout=30.0` and a hypothetical `worker_timeout=30` (if the field type ever changed to
  `int`) would render differently between call sites — not a fixed-precision format. Not worth
  fixing in isolation; would only matter if a future change touches log formatting broadly.
- No other issues — the diff only extends an existing, well-named log statement.

## Missing Tests

- No missing coverage for the changed behavior: `tests/test_run_parallel_tests.py::test_parallel_runner_logs_run_config`
  now asserts `worker_timeout=30.0` appears in the `parallel_test_run_started` log message,
  matching Step 3's repro and Step 4's implementation.
- Minor brittleness (not a gap, just worth naming): the new assertion checks the literal
  substring `"worker_timeout=30.0"`, which is tied to `ParallelRunConfig.worker_timeout`'s
  current default (`30.0`, `scripts/run_parallel_tests.py:87`). If that default is ever changed,
  this assertion (and the sibling WARNING-log assertions it sits next to) will need updating in
  lockstep — same pattern already accepted for the other fields in that test, so no new pattern
  introduced.

## Performance Concerns

None. Adding one field to an already-emitted INFO log line has no measurable performance impact.

## Follow-up Tasks

No follow-up tasks are needed for the implemented change itself.

Full-suite run (`make test`, two consecutive runs on the unmodified working tree) surfaced
pre-existing failures unrelated to this task's diff (`scripts/run_parallel_tests.py`,
`tests/test_run_parallel_tests.py` — logging-only change). None of the failing tests touch
parallel-runner logging or config; verdict for all is **NON-BLOCKER — pre-existing**.

Consistent across both runs (same failure both times → pre-existing, not flaky):

- `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
  — dialog-module LOC/inventory drift (`mcp_servers_dialog.py` at 446 LOC not reflected in the
  frozen audit expectation).
  Jira: [PYPOST-1252](https://pypost.atlassian.net/browse/PYPOST-1252) (new — no existing open
  issue matched this test by JQL search; filed in Phase D)
- `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_audit_module_inventory_within_caps`
  and `::test_markdown_snapshot_matches_current_metrics` — `pypost/core/template_service.py` now
  241 LOC vs. the recorded cap/snapshot of 225.
  Jira: [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111) (existing — "Regenerate
  audit/baseline metrics snapshots drifted by recent MCP refactors (2 pre-existing failures)")
- `tests/test_makefile.py::TestTargetExecution::test_make_test_excludes_slow_marker` — worker
  timed out after 120.0s inside the parallel runner's own subprocess-based Makefile test; not
  related to the `worker_timeout` log field added in this task.
  Jira: [PYPOST-1234](https://pypost.atlassian.net/browse/PYPOST-1234) (existing)

Observed only on one of the two runs (differing failure set between runs → re-run confirmed
flaky under parallel execution, likely resource contention):

- `tests/test_agent_e2e_harness_table_doc.py::test_agent_e2e_harness_table_matches_marked_modules`
  Jira: [PYPOST-1231](https://pypost.atlassian.net/browse/PYPOST-1231) (existing)
- `tests/test_environment_export.py::test_write_encrypted_export_file_round_trips_through_import`
  Jira: [PYPOST-1232](https://pypost.atlassian.net/browse/PYPOST-1232) (existing)
- `tests/test_lint_pytestmark_e402.py::test_no_e402_findings_in_tests_dir`
  Jira: [PYPOST-1233](https://pypost.atlassian.net/browse/PYPOST-1233) (existing)
- `tests/test_main_window_alert_reload.py` (whole file, exit code -11 / segfault — GUI test,
  plausibly Qt/offscreen-platform contention under parallel workers)
  Jira: [PYPOST-1251](https://pypost.atlassian.net/browse/PYPOST-1251) (existing)

Dedupe performed in Phase D via `jira_search_issues_jql` (`project = PYPOST AND statusCategory
!= Done AND key in (...)` against the sibling keys named by Step 7, plus a text search for the
dialog-audit test) — 7 of 8 failures matched already-open sprint issues; one
(`test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`) had no existing tracker
coverage and was filed as PYPOST-1252 (Debt, Low, 2 SP) via the jira-create-issue skill. No
duplicates were created. PYPOST-1193/1194/1195/1196/1181 (also named as plausible sibling keys
by Step 7) did not match any of this run's 8 failures and were left untouched.

No failure is caused by this task's change — the diff touches only the `parallel_test_run_started`
log statement in `scripts/run_parallel_tests.py` and its accompanying test assertion, neither of
which any failing test above exercises.
