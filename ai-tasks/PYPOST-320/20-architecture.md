# PYPOST-320: Architecture — Save Flow GUI Integration Tests

## Research

- `RequestWidget` exposes `handle_save_menu_action`, `handle_save_request_shortcut`,
  `handle_save_as_menu_action`, and `handle_save_as_shortcut` as GUI entry points.
- `TabsPresenter.add_new_tab` wires `save_requested` / `save_as_requested` to handlers.
- Existing tests in `test_tabs_presenter.py` call handlers or emit signals directly.
- `test_delete_open_tabs_integration.py` and `test_new_variable_flow_integration.py` establish
  the integration-test pattern for presenter wiring.

## Implementation Plan

1. Add `tests/test_save_flow_integration.py` with `TestSaveFlowIntegration`.
2. Reuse `FakeRequestManager`, `FakeStateManager`, and `_mock_save_dialog` from sibling tests.
3. Drive menu/shortcut callbacks on the active tab's `RequestWidget`.
4. Mock `SaveRequestDialog` and `QMessageBox` at orchestrator import paths.
5. Assert persistence, signals, and tab identity after each flow.

## Test Matrix

| Test | Entry point | Path | Expected outcome |
| ---- | ----------- | ---- | ---------------- |
| `test_save_menu_action_overwrites_existing_request` | menu | happy | persist + `request_saved` |
| `test_save_menu_action_cancelled_when_dialog_dismissed` | menu | cancel | no persist |
| `test_save_shortcut_cancelled_on_overwrite_decline` | shortcut | cancel | no persist |
| `test_save_as_shortcut_persists_copy_with_new_id` | shortcut | happy | new ID + signal |
| `test_save_as_menu_action_cancelled_when_dialog_dismissed` | menu | cancel | tab unchanged |

## Q&A

| Question | Answer |
| -------- | ------ |
| Production code changes? | None expected; tests document and guard existing wiring. |
| Why patch orchestrator dialog path? | Keeps tests fast and headless while exercising real widget → presenter flow. |
