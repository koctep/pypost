# PYPOST-164: Architecture — ResponseView context menu tests

## Current State

| Area | Coverage |
| --- | --- |
| `ResponseView.show_context_menu` | No dedicated tests |
| Env dialog context menus | `test_env_dialog.py` |
| Collection tree context menus | `test_collection_tree_actions.py`, presenter tests |
| History panel context menu | `test_history_panel.py` |
| Response search | `test_response_view_search.py` |

`ResponseView` builds a custom `QMenu` with optional Set Variable submenu, Copy, and Select All.

## Planned Changes

### Test module: `tests/test_response_view_context_menu.py`

| Scenario | Setup | Expected |
| --- | --- | --- |
| No env keys | `current_env_keys` default `None`, text selected | No `addMenu`; Copy + Select All |
| Env keys + selection | `set_env_keys([...])`, select text | `addMenu("Set Variable")`, key actions, New Variable |
| Env key chosen | Trigger connected key action | `variable_set_requested(key, value)` |
| New Variable chosen | Trigger New Variable action | `variable_set_requested(None, value)` |
| Copy chosen | Trigger Copy action | `body_view.copy()` called |
| Select All chosen | Trigger Select All action | `body_view.selectAll()` called |
| Whitespace selection | Select spaces only | No Set Variable submenu |

### Patterns

- Patch `pypost.ui.widgets.response_view.QMenu` at widget module (same as history panel).
- Use `qapp` fixture from `tests/conftest.py`.
- Select text via `QTextCursor` before calling `show_context_menu`.
- Invoke action callbacks captured from `action.triggered.connect`.

### Documentation

- Add module to `doc/dev/gui_testing.md` representative table.
- Add testing row to `doc/dev/response_search.md` (ResponseView doc).

## Out of Scope

- `pytest-qt` / `qtbot`.
- MainWindow signal handler tests.

## Risks

| Risk | Mitigation |
| --- | --- |
| Submenu mock ordering | Explicit `side_effect` lists per scenario |
| QAction partial callbacks | `_trigger_connected` helper invokes first connect arg |
