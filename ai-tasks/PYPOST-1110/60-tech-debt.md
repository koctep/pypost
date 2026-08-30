# PYPOST-1110: Technical Debt Analysis

## Summary

This task required **zero code changes**. The defect PYPOST-1110 targeted — `tests/test_mcp_controls_presenter.py`
defining a local `qapp()` fixture that diverged from the shared `tests/conftest.py` fixture — was
already eliminated by unrelated prior commit `494eb857` (PYPOST-1176, "fix(tests): PYPOST-1176
restore green test suite on dev") before this task's own work began. Steps 1-6 independently
confirmed the target file already matches the desired pattern (no local `qapp()`, no `sys`/
`QApplication` imports, uses the shared module-scoped `qapp` fixture from `tests/conftest.py`),
and that the suite-wide guard test
(`tests/test_suite_qapp_alignment.py::test_suite_has_no_local_qapp_fixtures_or_setupclass_qapplication`)
already passes. No production or test code was written or modified by this task; the working tree
has zero diff from `dev` HEAD. See `ai-tasks/PYPOST-1110/20-architecture.md` for full evidence and
reasoning.

## Shortcuts Taken

None — no code was changed. The ticket's scope was already resolved upstream by commit `494eb857`
(PYPOST-1176), prior to this task starting.

## Code Quality Issues

None identified in the target file (`tests/test_mcp_controls_presenter.py`). It already conforms
to the shared-fixture pattern with no local `qapp()`, no stray `sys`/`QApplication` imports, and no
other issues observed during read-only inspection in Steps 1-2.

## Missing Tests

None. The existing guard test
(`tests/test_suite_qapp_alignment.py::test_suite_has_no_local_qapp_fixtures_or_setupclass_qapplication`)
already provides permanent, suite-wide regression coverage for the qapp-fixture pattern this
ticket cares about — it AST-inventories every `tests/test_*.py` module for local `qapp()`
fixtures, `_get_app()` lazy-QApplication helpers, and `TestCase.setUpClass` QApplication
construction. No additional test is needed for this ticket's own scope.

## Performance Concerns

None.

## Follow-up Tasks

During Step 4's full-suite verification run (`make test`, no args: 311 files, 303 passed, 7
failed, 1 skipped), 7 pre-existing failing test files/clusters were found. Since this task's
working tree has zero diff from `dev` HEAD (no code changed anywhere in this task), the base
commit and current HEAD are identical, so every failure below is pre-existing by definition — no
separate baseline-worktree comparison was needed per `_shared/failing-tests-triage.md`. None of
these are in this ticket's scope and none were caused by this task. Each is recorded here as
`NON-BLOCKER — pre-existing`; the orchestrator files one Jira Debt issue per cluster via
`jira-create-issue` in Phase D and should back-fill the issue keys into this file.

1. **NON-BLOCKER — pre-existing**
   `tests/test_agent_e2e_harness_table_doc.py::test_agent_e2e_harness_table_matches_marked_modules`
   Suspected cause: not investigated further than the node id in the Step 4 run log; likely an
   out-of-sync doc/table-vs-code drift check unrelated to qapp fixtures.
   Jira: [PYPOST-1231](https://pypost.atlassian.net/browse/PYPOST-1231) (pre-existing, already tracked)

2. **NON-BLOCKER — pre-existing**
   `tests/test_environment_export.py::test_write_encrypted_export_file_round_trips_through_import`
   Suspected cause: not investigated further than the node id in the Step 4 run log; possibly an
   environment/encryption round-trip regression unrelated to this ticket's scope.
   Jira: [PYPOST-1232](https://pypost.atlassian.net/browse/PYPOST-1232) (pre-existing, already tracked)

3. **NON-BLOCKER — pre-existing**
   `tests/test_lint_pytestmark_e402.py::test_no_e402_findings_in_tests_dir`
   Suspected cause: a lint-style E402 (module-import-not-at-top-of-file) finding somewhere in
   `tests/`, unrelated to this ticket's scope.
   Jira: [PYPOST-1233](https://pypost.atlassian.net/browse/PYPOST-1233) (pre-existing, already tracked)

4. **NON-BLOCKER — pre-existing**
   `tests/test_main_window_alert_reload.py` (file-level crash, exit_code=-11 / SIGSEGV)
   Suspected cause: a native/Qt-level segfault during this file's run, not a Python assertion
   failure — likely a Qt widget lifecycle or threading issue unrelated to this ticket's scope.
   Jira: [PYPOST-1251](https://pypost.atlassian.net/browse/PYPOST-1251) (newly created, 3 SP)

5. **NON-BLOCKER — pre-existing**
   `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
   Suspected cause: not investigated further than the node id in the Step 4 run log; likely a
   stale/incoherent audit-report aggregate from a prior ticket's artifact, unrelated to this
   ticket's scope.
   Jira: [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111) (pre-existing, already tracked)

6. **NON-BLOCKER — pre-existing**
   `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_audit_module_inventory_within_caps`
   Suspected cause: module inventory has likely grown past a hardcoded cap in the SOLID-audit
   baseline; unrelated to this ticket's scope.
   Jira: [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111) (added as a comment on the
   existing issue — same SOLID-audit-baseline cluster as item 7 below)

7. **NON-BLOCKER — pre-existing**
   `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
   Suspected cause: a markdown snapshot of SOLID-audit metrics is stale relative to current code
   metrics; unrelated to this ticket's scope.
   Jira: [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111) (pre-existing, already tracked)

8. **NON-BLOCKER — pre-existing**
   `tests/test_makefile.py::TestTargetExecution::test_make_test_agent_e2e_selects_agent_e2e_marker`
   (file-level timeout, exit_code=-9 after 120s)
   Suspected cause: the `make test-agent-e2e` marker-selection target appears to hang or run long
   enough to exceed the 120s test timeout; unrelated to this ticket's scope.
   Jira: [PYPOST-1234](https://pypost.atlassian.net/browse/PYPOST-1234) (pre-existing, already tracked)
