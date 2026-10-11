# Roadmap: PYPOST-1355

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Business requirements documented in `10-requirements.md`: private editable copy,
    immutable shipped source, collision safety, update warning, and Save/Cancel boundaries.
- [x] **STEP 2: High-Level Architecture Design**
  - [/] `20-architecture.md`: canonical synchronous creation, independent identities,
    persistence failure cleanup, editor Save/Cancel boundaries, and bounded red repro plan.
- [x] **STEP 3: Failing Repro Test**
  - [/] `tests/test_mcp_builtin_collection_copy.py`: bounded canonical creation and
    editor Save/Cancel contracts; 16 intended red failures, no fixture errors.
  - [/] `make test PYTEST_ARGS='tests/test_mcp_builtin_collection_copy.py -q'`:
    fails on missing `create_workspace_collection`, editor `create_collection` /
    `get_collections` capability, `Copy for editing` button, and MainWindow setter wiring.
    Evidence: `/tmp/pypost1355-step3-red.log`. All items declare a 30-second timeout;
    teardown waits are bounded to 5000 ms, with no polling or arbitrary sleeps.
  - [/] Coverage includes save-before-publish/tree/index lookup, request editing and
    repeated independent identities/names, source bytes, nested content, failure cleanup,
    busy/disposed rejection, environment preservation, actual dialog Save/Cancel callbacks,
    and controls/dialog/MainWindow forwarding. No production changes in this step.
  - [/] `make lint` passed (configured production/doc scope); independent red review pending.
  - [/] Step3 review fix: added simultaneous save/delete failure coverage. It requires
    preserving the original save exception, ID-only cleanup attempt, no publication or
    editor switch, and safe cleanup-failure diagnostics without credential-like error text.
    Re-ran the same targeted command: 16 intended red failures; no production changes.
- [x] **STEP 4: Development**
  - [/] Iteration 1: implement canonical synchronous collection creation and identity
    preparation, preserving save-before-publication and narrow failure cleanup.
  - [/] Iteration 1a: added typed callback and pure deep-copy/name/identity preparation,
    reusing the import planner and reserving MCP profile collisions separately.
  - [/] Iteration 1b: canonical owner rejects busy/teardown calls, saves before rebuilding
    the manager index/tree, and cleans only the fresh ID on failure with safe diagnostics.
  - [/] Iteration 2: optional typed creation capability wired from MainWindow's canonical
    collections presenter through controls and dialog; editor receives the live provider.
  - [/] Iteration 3: editor copy action and update note use a cohesive helper; success
    refreshes live choices, switches to the saved Workspace ID, and preserves environment.
    Failures retain Built-in selection and show safe retry feedback. Save/Cancel stay in
    the existing server configuration flow.
  - [/] Test harness correction: scoped the import-busy stub so it restores before the
    owner fixture's bounded teardown; all busy-rejection assertions remain unchanged.
  - [/] `make test PYTEST_ARGS='tests/test_mcp_builtin_collection_copy.py -q'` passed
    (all 16 reviewed items). Log: `/tmp/pypost1355-step4-repro.log`.
  - [/] Iteration 4: wrapped three task-added long lines found by lint; focused regression
    run passed all 10 modules (copy, paired environment, Built-in/server/control dialogs,
    collection import/apply/profile, RequestManager, and collection tree presenter).
    Command/log: `make test PYTEST_ARGS='tests/test_mcp_builtin_collection_copy.py
    tests/test_mcp_builtin_paired_env.py tests/test_mcp_builtin_dialog.py
    tests/test_mcp_servers_dialog.py tests/test_mcp_controls_presenter.py
    tests/test_collection_import.py tests/test_collection_import_apply.py
    tests/test_collection_import_profile.py tests/test_request_manager.py
    tests/test_collections_presenter.py -q'`; `/tmp/pypost1355-step4-regression.log`.
  - [/] `make lint typecheck` passed; mypy baseline remains 181 known errors.
    Log: `/tmp/pypost1355-step4-quality.log`. Existing module caps were unchanged;
    collection creation and editor presentation reside in cohesive helpers.
  - [/] Required full `make check` completed: 390 files, 369 passed, 14 failed,
    7 skipped, 361.54 seconds. It failed in the test target, so the combined gate did
    not reach artifact verification. Log: `/tmp/pypost1355-step4-check.log`.
  - [/] Iteration 5: moved the copy action helper to `ui/mcp_builtin_collection_copy.py`:
    it is editor presentation rather than a dialog. This prevents a task-added dialog
    inventory failure without editing historical audit reports; SOLID caps already pass.
  - [/] Iteration 6: composition treats creation as an optional capability for legacy
    presenter adapters; the real canonical presenter is still injected. This fixes the
    encrypted-startup regression's deferred presenter fixture without changing its tests.
  - [/] Follow-up validation passed all 3 modules: `make test
    PYTEST_ARGS='tests/test_mcp_builtin_collection_copy.py
    tests/test_main_window_encrypted_startup.py tests/test_audit_scripts_cli.py -q'`.
    Log: `/tmp/pypost1355-step4-followup.log`.
  - [/] `make test PYTEST_ARGS='tests/test_dialogs_audit.py -q'` passed after the
    helper relocation; `/tmp/pypost1355-step4-dialog-inventory.log`. All 3 task-caused
    failed modules from the full run now pass focused verification. The remaining
    11 failed modules match filed baseline clusters; exact evidence appears below.
  - [/] Final `make lint typecheck verify-ai-tasks check-baseline-metrics` passed after
    the fixes; `/tmp/pypost1355-step4-quality.log`. No broad suite repeat or historical
    snapshot edits were needed. Step4 remains in progress for independent review.
- [x] **STEP 5: Code Cleanup**
  - [/] `40-code-cleanup.md`: task import grouping and Make static/type/artifact checks;
    existing regression evidence and classified baseline failures retained.
  - [/] `make lint typecheck check-baseline-metrics` passed after import-only cleanup;
    `/tmp/pypost1355-step5-quality.log`. No behavior/test/cap changes or full suite repeat.
- [x] **STEP 6: Observability**
  - [/] `50-observability.md`: safe creation lifecycle fields and caplog success,
    rejection, save failure, cleanup failure, and privacy contracts.
  - [/] Added safe count fields to existing helper admission/success logs; strengthened
    the existing 16-case repro's exact lifecycle/error/privacy assertions. No metric
    schema was needed for the bounded local operation and no presenter cap changed.
  - [/] Focused four-module `make test` passed; `/tmp/pypost1355-step6-tests.log`.
    `make lint typecheck check-baseline-metrics` passed; `/tmp/pypost1355-step6-quality.log`.
- [x] **STEP 7: Technical Debt Analysis**
  - [/] `60-tech-debt.md`: accepted boundaries, bounded coverage, realistic storage
    rollback limitation, and exact filed baseline failures; no new implementation debt found.
- [x] **STEP 8: Dev Docs**
  - [/] Extended `doc/dev/predefined_collection_library.md` with the canonical collection
    copy API, identity/persistence/configuration boundaries, and troubleshooting.
  - [/] `make lint-docs check-docs-links verify-ai-tasks` passed;
    `/tmp/pypost1355-step8-docs.log`. Those default doc checks target user/README files.
    A temporary Make target invoked both existing validators with the developer guide
    explicitly: Markdown and link checks also passed for that single guide;
    `/tmp/pypost1355-step8-guide.log`. No Makefile, product, or user-doc changes were needed.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1355/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1355/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

Full gate failure classification (`/tmp/pypost1355-step4-check.log`):

| Failed module | Classification and exact evidence |
| --- | --- |
| `test_audit_scripts_cli.py` | Task-caused missing helper inventory; repaired and isolated module passed. Node: `TestAuditDialogsInventoryCLI::test_check_clean_returns_zero_and_reports_ok`. |
| `test_dialogs_audit.py` | Same repaired helper placement. Node: `TestDialogsAuditInventory::test_audit_report_lists_every_dialog_module`; isolated module passed. |
| `test_main_window_encrypted_startup.py` | Task-caused optional-capability adapter failure; repaired and isolated module passed. Node: `test_encrypted_startup_defers_restore_until_both_loads_complete`. |
| `test_makefile_install_stamp_contract.py` | [PYPOST-1298](https://pypost.atlassian.net/browse/PYPOST-1298): `TestInstallExtraStampContract::test_install_touches_both_extra_stamps` timed out at the 60-second pytest budget inside `_run_make`/subprocess communication. |
| `test_makefile_exit_behavior.py` | PYPOST-1298: 120-second worker timeout while `TestExitBehavior::test_lint_succeeds_from_bare_venv_via_venv_test` was executing. |
| `test_makefile_stamp_otel_idempotency.py` | PYPOST-1298: `TestVenvOtelStampIdempotency::test_venv_otel_skips_pip_when_current` failed; bounded worker stopped at 120 seconds during `test_venv_otel_installs_when_stamp_stale`. |
| `test_makefile_stamp_test_idempotency.py` | PYPOST-1298: `TestVenvTestStampIdempotency::test_venv_test_skips_pip_when_current` failed; bounded worker stopped at 120 seconds during `test_venv_test_installs_when_stamp_stale`. |
| `test_makefile_target_filtering.py` | PYPOST-1298: `TestTargetFiltering::test_make_test_excludes_slow_marker` failed; 120-second worker timeout during `test_pytest_args_narrows_test_run`. |
| `test_makefile_target_install_test.py` | PYPOST-1298: `TestTargetInstallTest::test_venv_test_installs_pytest_and_flake8` failed; 120-second worker timeout during `test_test_succeeds_after_install`. |
| `test_pytest_exit_policy.py` | [PYPOST-1299](https://pypost.atlassian.net/browse/PYPOST-1299): `test_make_test_fails_closed_when_parallel_runner_is_missing` failed; 120-second worker timeout during `test_make_test_cov_fails_closed_when_parallel_runner_is_missing`. |
| `test_mcp_server_registry.py` | [PYPOST-1362](https://pypost.atlassian.net/browse/PYPOST-1362): `test_failed_bind_is_reported_for_only_the_requested_instance`, same filed assertion that `beta-server` still reports running after failed-bind notification. |
| `test_pypost_1077_verification_artifacts.py` | [PYPOST-1361](https://pypost.atlassian.net/browse/PYPOST-1361): `test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`; stale dialog report records 1031 LOC versus 1219 live LOC. |
| `test_pypost_1287_failing_repro.py` | PYPOST-1361: `test_live_report_inventory_loc_matches_discovery`; same stale dialog row, 1031 versus 1219 LOC. |
| `test_solid_audit_baseline.py` | PYPOST-1361: `TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`; stored MainWindow/presenter LOC snapshot differs from current code. All module/class cap checks pass. |

These baseline nodes/causes are already recorded with base reproduction in
`ai-tasks/PYPOST-1354/60-tech-debt.md`. The Makefile, fixture helpers, registry, and historical
reports were not modified. The first failed nodes in killed workers have no complete traceback
because the runner stopped their processes; classify their observed bounded timeout cluster
without claiming a new isolated reproduction. No new failure cause remains after the two
implementation repairs. Historical PYPOST-1358/1359/1360 did not appear in this gate.

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1355/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1355/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1355/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
