# PYPOST-1530: Technical Debt Analysis

## Shortcuts Taken

None. The implementation removes dormant activation state and uses the existing unsupported-role
fallbacks, following the approved architecture. No stubs or temporary compatibility paths remain.

## Code Quality Issues

No new debt identified. Selector editing, persistence, cached syntax, signals, and virtualization
retain their established behavior. Existing privacy-safe diagnostics remain sufficient.

## Missing Tests

No task-specific gap identified. The nine selector-only regression cases cover populated and
trailing rows, unsupported reads/writes, preserved selectors, and absent change signals. Their
module declares `pytest.mark.timeout(30)`. Existing selector/UI regression files passed.

## Performance Concerns

No new performance concern; removing unused per-row state and role branches adds no work.
The unrelated full-suite load failures below remain tracked separately.

## Follow-up Tasks

All follow-ups already have Jira issues. None blocks this task. Full node identifiers below
are formed by joining the stated module, optional class, and test name with `::`.

### Baseline failures

Each is **NON-BLOCKER — pre-existing**: the same failure reproduced at base `97e8dc5f` in an
isolated worktree, with targeted `make test VENV=/home/src/.venv WORKERS=1 PYTEST_ARGS=...`.

- [PYPOST-1474](https://pypost.atlassian.net/browse/PYPOST-1474): incomplete package/seed inventory.
  Module `tests/test_bundled_examples_packaging.py`, test
  `test_explicit_packages_cover_application_tree_and_examples`; module
  `tests/test_makefile_install_seed_contract.py`, test
  `test_committed_seed_covers_independent_source_inventory`.
- [PYPOST-1475](https://pypost.atlassian.net/browse/PYPOST-1475): dialog LOC inventory drift.
  Module `tests/test_pypost_1077_verification_artifacts.py`, test
  `test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`; module
  `tests/test_pypost_1287_failing_repro.py`, test
  `test_live_report_inventory_loc_matches_discovery`.
- [PYPOST-1553](https://pypost.atlassian.net/browse/PYPOST-1553): reserved-port bind fails with
  `OSError: [Errno 98] Address already in use`. Module
  `tests/test_mcp_process_autorestart_repro.py`, test
  `test_initial_start_failure_does_not_trigger_auto_restart`.
- [PYPOST-1554](https://pypost.atlassian.net/browse/PYPOST-1554): SOLID snapshot LOC drift
  (`395` versus `399`). Module `tests/test_solid_audit_baseline.py`, class
  `TestSolidAuditBaseline`, test `test_markdown_snapshot_matches_current_metrics`.

### Confirmed flaky failures

Each is **NON-BLOCKER — pre-existing flaky**: one full-run failure followed by two passes on
the unchanged task tree using targeted `make test WORKERS=1 PYTEST_ARGS=...` commands.

- [PYPOST-1555](https://pypost.atlassian.net/browse/PYPOST-1555): eleven 120-second worker
  timeouts and an install-stamp timeout; all twelve affected files passed both serial retries.
  Captured active node components:
  - `tests/test_makefile_install_stamp_contract.py`, `TestInstallExtraStampContract`,
    `test_install_stamps_allow_skip_pip_on_venv_test_otel`.
  - `tests/test_makefile_stamp_otel_idempotency.py`, `TestVenvOtelStampIdempotency`,
    `test_venv_otel_installs_when_stamp_missing`.
  - `tests/test_makefile_stamp_test_idempotency.py`, `TestVenvTestStampIdempotency`,
    `test_venv_test_installs_when_stamp_missing`.
  - `tests/test_makefile_target_install_test.py`, `TestTargetInstallTest`,
    `test_venv_test_installs_pytest_and_flake8` and `test_install_succeeds_with_minimal_pyproject`.
  - `tests/test_makefile_target_filtering.py`, `TestTargetFiltering`,
    `test_make_test_excludes_slow_marker` and `test_make_test_agent_e2e_selects_agent_e2e_marker`.
  - `tests/test_test_lint_baseline.py`,
    `test_invalid_source_location_is_not_dropped[tests/missing.py\t1\t1\tF401\terror]`.
  Additional modules timed out before node output was captured:
  `tests/test_ui_actions.py`, `tests/test_ui_identity_spotcheck.py`,
  `tests/test_ui_actions_tree_no_model_mutation.py`, `tests/test_ui_actions_mcp_packaging_doc.py`,
  `tests/test_ui_library_manager.py`, and `tests/test_ui_library_manager_pypost_1278_repro.py`.
  Root cause is not investigated; shared startup/I/O pressure is a hypothesis.
- [PYPOST-1556](https://pypost.atlassian.net/browse/PYPOST-1556): double-body settling race.
  Module `tests/test_agent_e2e_double_response_body.py`, test
  `test_agent_e2e_double_body_red_path_without_discard`. The exact-single-body wait timed out
  when the intentionally duplicated body was already present. This node also passed at base.

### Evidence

Original `make check`: lint passed; 454 passed, 19 failed, and 7 skipped files. The combined
command remains red; no task-caused failure remains. The linked issues retain exact commands,
failure excerpts, and retry rates. Local run logs are `/tmp/pypost-1530-make-check.log`,
`/tmp/pypost-1530-baseline.log`, `/tmp/pypost-1530-retry-timeouts.log`,
`/tmp/pypost-1530-retry-agent.log`, and `/tmp/pypost-1530-confirm-flaky.log`.
See [cleanup evidence](40-code-cleanup.md) and [the roadmap](00-roadmap.md) for task validation.
The baseline worktree was removed, root installation restored, and `make verify-ai-tasks` passed.
