# PYPOST-1295: Technical Debt Analysis

## Shortcuts Taken

None. The implementation directly resolves TD-8 from `ai-tasks/PYPOST-1285/60-tech-debt.md`.
The Makefile now defines standard targets `baseline-metrics` and `check-baseline-metrics`,
and the generation script outputs `make baseline-metrics` under the `Regenerate:` section.
Developers and agents no longer need to hand-edit LOC numbers or invoke forbidden `.venv` binaries.

## Code Quality Issues

None introduced. All changes in `Makefile`, `scripts/audit_baseline_metrics.py`,
`ai-tasks/PYPOST-376/baseline-metrics.md`, and `tests/test_solid_audit_baseline.py` strictly
adhere to project standards, with all lines <= 100 characters.

## Missing Tests

None for this task's scope.
- `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_regeneration_instructions_prescribe_make_target`
  verifies that `format_markdown` produces `make baseline-metrics` and omits `.venv/bin/python`.
- `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_makefile_defines_baseline_metrics_targets`
  verifies that both `baseline-metrics:` and `check-baseline-metrics:` are defined in `Makefile`.
- `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
  verifies that the committed markdown matches the script output verbatim.
- All tests carry explicit timeout markers (`pytestmark = pytest.mark.timeout(30)`).

## Performance Concerns

None. `make baseline-metrics` and `make check-baseline-metrics` execute within ~1.3 seconds,
reading file lines without importing heavy graphical modules.

## Follow-up Tasks

No new follow-up tasks required from this change.

Pre-existing test failures in the repository are tracked under existing Jira issues:
- `NON-BLOCKER — pre-existing`: Coverage gate drops below 85% on `make test-cov` (tracked in
  PYPOST-1261).
- `NON-BLOCKER — pre-existing`:
  `tests/test_storage.py::test_storage_init_creates_default_request_when_no_active_requests`
  fails due to mock storage state behavior (tracked in PYPOST-1287).
- `NON-BLOCKER — pre-existing`:
  `tests/test_mcp_client_tab.py::TestMcpClientTabUiWiring::test_initial_form_hidden_and_populated_on_connect`
  and
  `tests/test_mcp_client_tab.py::TestMcpClientTabUiWiring::test_refresh_button_triggers_reconnect`
  fail on Qt event loop timings (tracked in PYPOST-1286).
- `NON-BLOCKER — pre-existing`:
  `tests/test_collection_runner.py::TestCollectionRunnerIntegration::test_runner_runs_entire_collection`
  fails in isolated runner execution (tracked in PYPOST-1262).
