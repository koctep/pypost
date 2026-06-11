# PYPOST-516: Architecture

## Approach

Add `tests/test_request_editor_body_gutter.py` following patterns from
`test_request_editor_method_tab_switch.py` and gutter assertions from `test_code_editor.py`.

## Test Cases

| Test | Asserts |
|------|---------|
| `test_body_editor_is_code_editor_with_gutter` | Body tab uses `CodeEditor`; margin equals `line_number_area_width()` |
| `test_gutter_width_grows_with_line_count_in_widget_hierarchy` | 9→10 lines widens gutter inside `RequestWidget` |
| `test_gutter_click_does_not_modify_body_in_widget_hierarchy` | Gutter click is read-only in full hierarchy |

## Navigation

Use `method_combo.setCurrentText("POST")` to auto-switch to Body tab (existing behaviour).

## No Production Changes

Expected unless a test reveals a wiring bug.
