# Method → Body Tab Auto-Switch

## Overview

When the user selects **POST** or **PUT** as the HTTP method in the request editor, the
active tab automatically switches to **Body**. This eliminates the extra click required
to navigate to the body input after choosing a method that typically carries a request body.

Behaviour:
- Selecting POST or PUT switches the detail tab to **Body**.
- Selecting any other method (GET, DELETE, PATCH, MCP) does **not** change the active tab.
- The auto-switch only fires on explicit user interaction via the method combo box.
- Loading a saved request (regardless of method) does **not** trigger the switch.

## Architecture

- **`RequestWidget` (`pypost/ui/widgets/request_editor.py`)**:
  - `_loading: bool` — guard flag set to `True` during `load_data()` to suppress the
    auto-switch while data is being loaded programmatically.
  - `_on_method_changed(method: str)` — slot connected to `method_combo.currentTextChanged`.
    Sets placeholder text for the MCP method and, when `_loading` is `False` and `method`
    is `"POST"` or `"PUT"`, calls `detail_tabs.setCurrentWidget(body_edit)`.
  - `load_data()` — wraps all UI updates in `try/finally` with `_loading = True/False`.
    Also calls `_on_method_changed` explicitly to refresh placeholder text when the method
    value is unchanged (Qt does not fire `currentTextChanged` for a no-op `setCurrentText`).

- **`MetricsManager` (`pypost/core/metrics.py`)**:
  - Tracks auto-switch events: `gui_method_body_autoswitches_total{method}`

## Key Design Decision: `_loading` Guard

`method_combo.currentTextChanged` fires whenever the combo value changes. During
`load_data()` this would trigger an unwanted tab switch. Rather than
disconnecting/reconnecting the signal, a boolean guard is used — simpler and harder to
misuse.

The explicit `_on_method_changed` call inside `load_data()` (after `setCurrentText`) is
intentional: if the loaded method equals the current combo value, Qt does not emit the
signal, so placeholder text would not be refreshed without the direct call.

## Metrics

| Metric | Labels | Description |
|--------|--------|-------------|
| `gui_method_body_autoswitches_total` | `method` (POST \| PUT) | Fires each time the Body tab is auto-selected due to method change |

Example Prometheus query:

```promql
sum by (method) (gui_method_body_autoswitches_total)
```

## Troubleshooting

### Body tab does not switch when I select POST/PUT

- Confirm the method is being selected via the combo box (not loaded from a saved request).
- Check that `RequestWidget._loading` is `False` at the time of selection — if something
  calls `load_data()` without restoring the flag, the guard will be stuck. This should not
  happen in normal usage due to `try/finally`.

### Tab switches unexpectedly when opening a saved POST/PUT request

- This indicates the `_loading` guard is not active. Verify `load_data()` sets
  `self._loading = True` before calling `method_combo.setCurrentText(...)`.
