# PYPOST-597: Technical Debt Analysis

## Blocker Review Verdict

**SAFE TO CLOSE** — save-as GUI behavior is covered without adding new tests.

| Layer | Evidence |
| --- | --- |
| TabsPresenter | `test_save_as_emits_request_save_as_completed_not_request_saved`, `test_save_as_preserves_original_request_id`, `test_save_as_applies_to_source_tab_when_index_changes_during_dialog` in `tests/test_tabs_presenter.py` |
| RequestWidget → presenter | `test_save_as_shortcut_persists_copy_with_new_id`, `test_save_as_menu_action_cancelled_when_dialog_dismissed` in `tests/test_save_flow_integration.py` (PYPOST-320) |
| Orchestrator | save-as happy/cancel/new-collection paths in `tests/test_request_save_orchestrator.py` |

Presenter and integration tests cover signal routing, new ID assignment, source preservation,
and dialog cancel paths. No gap warranting an additional test.

## Follow-up Tasks

None.
