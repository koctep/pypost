# PYPOST-1184: Technical Debt Analysis

## Shortcuts Taken

None. This is a pure, behavior-preserving extraction: the helper body in
`pypost/ui/presenters/tabs_presenter_insert.py::insert_tab_before_plus` is a verbatim
(variable-renamed) copy of the three previously duplicated blocks. No logic was altered, no
edge case was papered over, and no TODO/FIXME markers were introduced.

## Code Quality Issues

- None found. The new module follows the established `presenter: TabsPresenter`
  sibling-module extraction pattern already used by `tabs_presenter_close.py`,
  `tabs_presenter_request_close.py`, `tabs_presenter_ws_close.py`, and
  `tabs_presenter_mcp_close.py` (verified by direct comparison): `TYPE_CHECKING`-only import of
  `TabsPresenter` to avoid a runtime circular import, presenter passed as the first positional
  argument, and the function reaches into `presenter._header` / `presenter._tabs` /
  `presenter.save_tabs_state()` exactly as the three original call sites did.
- The three call sites (`add_new_tab`, `_insert_mcp_client_tab`, `_insert_websocket_tab`) now
  each reduce to a single `insert_tab_before_plus(self, tab, name, save_state=save_state)` line,
  confirmed by source inspection — no residual copy of the old `plus_idx = ...` /
  `insert_index_before_plus()` block remains at any of the three sites.
  `tabs_presenter.py` shrank from 1,064 to 1,039 lines (still 254 lines over the 785-line soft
  cap; this task's Definition of Done only required a measurable reduction, not closing the gap,
  and Step 1 already documented that the remaining gap is out of scope for this task).
- The pre-existing return-value asymmetry (`add_new_tab` returns `None`; the other two return
  `tab`) was intentionally preserved per the architecture decision, not "fixed," since changing
  it would be an unrelated behavioral change outside this task's scope.

## Missing Tests

None identified for the new code path. `tests/test_tabs_presenter_insert.py` covers the
helper's signature contract and confirms (via source inspection) that all three call sites
delegate to it instead of hand-rolling the sequence. Existing behavioral coverage in
`tests/test_tabs_presenter.py` (insertion position, focus, conditional `save_tabs_state()`
timing, for all three tab kinds) was verified by Step 3 to already exercise the helper's actual
runtime behavior through the three call sites, so no new behavioral/integration test was needed
per the Step 2 architecture decision. All new/changed tests carry explicit pytest timeout
markers: `tests/test_tabs_presenter_insert.py` sets `pytestmark = pytest.mark.timeout(30)` at
module level (line 24) — confirmed present, not a BLOCKER.

## Performance Concerns

None. The extraction is a direct code move with identical control flow, no additional
allocations, loops, or I/O introduced. `insert_tab_before_plus` performs the same single
`insert_index_before_plus()` lookup and one `insertTab`/`addTab` call the three original blocks
each performed once.

## Deviations from Architecture

None. The implementation matches `ai-tasks/PYPOST-1184/20-architecture.md` exactly: same module
name and location (`pypost/ui/presenters/tabs_presenter_insert.py`), same function signature
(`insert_tab_before_plus(presenter, tab, name, *, save_state=True) -> None`), same
`TYPE_CHECKING`-only import, same three call sites updated with the same one-line replacement,
and the same explicitly rejected alternatives (private method on `TabsPresenter`, expanding
`tabs_presenter_draft.py`) were not taken.

## Hardcoded Values

None introduced. No new magic numbers, strings, or configuration values appear in the helper;
it only forwards values already computed by each call site (`tab`, `name`, `save_state`).

## Follow-up Tasks

No new follow-up tasks are required from this task's own implementation — the tech-debt item it
was created to resolve ("Triplicated insert-before-plus" in
`ai-tasks/PYPOST-1166/60-tech-debt.md`) is fully closed by this change.

Pre-existing test failures found during this task's Step 4 full-suite run (triaged by the
orchestrator against baseline; unrelated to this task's diff, which touched only
`pypost/ui/presenters/tabs_presenter.py` and the new `tabs_presenter_insert.py` module):

- `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_malformed_nested_expressions` — NON-BLOCKER — pre-existing — Jira: PYPOST-1261
- `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_standalone_malformed_closing_paren` — NON-BLOCKER — pre-existing — Jira: PYPOST-1261
- `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics` — NON-BLOCKER — pre-existing — Jira: PYPOST-1261
- `tests/test_template_service.py::TestTemplateServiceValidationOutcomes::test_validate_malformed_nested_alignment` — NON-BLOCKER — pre-existing — Jira: PYPOST-1261
- `tests/test_template_service.py::TestTemplateServiceObservability::test_render_malformed_nested_validation_failure_tracks_validation_metrics_on_hover` — NON-BLOCKER — pre-existing — Jira: PYPOST-1261
- `tests/test_makefile_lifecycle.py` and `tests/test_makefile_targets.py` (120s worker timeout under full-suite parallel load) — NON-BLOCKER — pre-existing — Jira: PYPOST-1262
- `tests/test_collection_import_profile.py::test_plan_collection_import_large_dataset_performance` — NON-BLOCKER — flaky, pre-existing — Jira: PYPOST-1263
</content>
