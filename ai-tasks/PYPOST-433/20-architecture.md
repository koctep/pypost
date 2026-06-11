# PYPOST-433 Architecture — EnvironmentDialog test expansion

## 1. Problem Summary

Copy/duplicate and several validation branches live in `EnvironmentListWidget`; variable
sync edge cases live in `EnvironmentVariablesWidget`. Existing dialog tests invoke
delegated methods on `EnvironmentDialog` but never exercise the copy loop or reprompt
branches.

## 2. Solution Overview

Add focused pytest methods to `tests/test_env_dialog.py` using the existing patterns:

| Area | Target | Test approach |
| --- | --- | --- |
| Copy success | `EnvironmentListWidget._duplicate_environment_at_row` | Patch `QInputDialog.getText` → valid name; assert clone via `dlg.environments` |
| Copy cancel | Same | `getText` returns `(name, False)`; length unchanged |
| Empty / duplicate name | Copy validation loop | `side_effect` on `getText`; patch `show_copy_environment_*_error` |
| Copy observability | `environment_copied` log | `caplog.at_level(logging.INFO)` |
| Variable trailing row | `on_var_changed` | Set item on last row; assert model + trailing row preserved |
| Invalid rename revert | `_sync_env_variables_from_table` | Edit existing key to invalid identifier; assert revert |
| No selection | `on_env_selected(-1)` / `load_environment(None)` | Table cleared, MCP disabled |

Access widget internals via `dlg._env_list_widget` and existing dialog delegates
(`on_var_changed`, `on_env_selected`).

## 3. Mocking Strategy

- Patch at **definition site**: `pypost.ui.widgets.environments.environment_list_widget.QInputDialog.getText`
- Error helpers: `show_copy_environment_empty_name_error`, `show_copy_environment_duplicate_name_error`
- No real modal dialogs; no event-loop polling beyond synchronous Qt calls

## 4. Risks

| Risk | Mitigation |
| --- | --- |
| Brittle menu wiring tests | Prefer direct `_duplicate_environment_at_row` for logic; optional thin context-menu smoke |
| Flaky Qt | Module `pytestmark = pytest.mark.timeout(60)`; no unbounded waits |

## 5. Files Changed

| File | Change |
| --- | --- |
| `tests/test_env_dialog.py` | New test methods only |
| `doc/dev/environments_dialog.md` | Testing section (Step 7) |

No production code changes required.
