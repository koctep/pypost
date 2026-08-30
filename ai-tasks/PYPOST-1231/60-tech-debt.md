# PYPOST-1231: Technical Debt Analysis

## Shortcuts Taken

None. This task's implementation is a pure documentation-table append: three missing rows
were added to the "Harness modules under the marker" table in `doc/dev/agent_e2e.md`
(`tests/test_agent_session_event_settle.py`, `tests/test_agent_ui_actions_mcp_seed.py`,
`tests/test_ui_actions_tree_no_model_mutation.py`). No production code, test code, or
configuration was touched. There was no temporary solution, workaround, or compromise made
for development speed — the fix is the complete, correct closure of the Step 3 red gate
(`tests/test_agent_e2e_harness_table_doc.py::test_agent_e2e_harness_table_matches_marked_modules`).

## Code Quality Issues

None introduced. No code was changed by this task; there is nothing to refactor, rename, or
break down as a result of this change.

## Missing Tests

None. The existing guard test
`tests/test_agent_e2e_harness_table_doc.py::test_agent_e2e_harness_table_matches_marked_modules`
already enforces that the harness table stays in sync with `agent_e2e`-marked modules, and it
now passes against the corrected table. No new test coverage is required for a doc-only
table append.

## Performance Concerns

None. The change affects only a Markdown documentation file and has no runtime, build, or
performance impact.

## Follow-up Tasks

No new Jira follow-ups are needed for this task — the pure doc-table append introduces no new
technical debt, and every pre-existing failure surfaced by the full-suite triage below is
already tracked under an existing Jira key. No new issues were filed.

### Pre-existing failures found during Step 4 full-suite run (`make test`)

Full-suite result: 311 files collected, 304 passed / 6 failed / 1 skipped. All 6 failures are
pre-existing, unrelated to this task's doc-only change, and already tracked in Jira:

- `tests/test_environment_export.py::test_write_encrypted_export_file_round_trips_through_import`
  — **NON-BLOCKER — pre-existing**.
  Jira: [PYPOST-1232](https://pypost.atlassian.net/browse/PYPOST-1232)
- `tests/test_lint_pytestmark_e402.py::test_no_e402_findings_in_tests_dir`
  — **NON-BLOCKER — pre-existing**.
  Jira: [PYPOST-1233](https://pypost.atlassian.net/browse/PYPOST-1233)
- `tests/test_main_window_alert_reload.py::test_open_settings_reloads_alert_manager_when_webhook_changes`
  (SIGSEGV, exit -11) — **NON-BLOCKER — pre-existing**.
  Jira: [PYPOST-1251](https://pypost.atlassian.net/browse/PYPOST-1251)
- `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
  — **NON-BLOCKER — pre-existing**.
  Jira: [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111) (also referenced by
  [PYPOST-1252](https://pypost.atlassian.net/browse/PYPOST-1252))
- `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_audit_module_inventory_within_caps`
  — **NON-BLOCKER — pre-existing**.
  Jira: [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111) (tracked via comment on
  that issue)
- `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
  — **NON-BLOCKER — pre-existing**.
  Jira: [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111)
- `tests/test_makefile.py::test_test_succeeds_from_bare_venv_via_venv_test` (120s
  `WORKER_TIMEOUT`) — **NON-BLOCKER — pre-existing**.
  Jira: [PYPOST-1234](https://pypost.atlassian.net/browse/PYPOST-1234)

All 6 node ids are already filed under the Jira keys above; no new issues were created for
this task.
