# PYPOST-42: Observability

## Scope

The feature is a pure UI interaction (auto-switch Body tab on PUT/POST). There is no
network call or server-side action to instrument. The relevant observability question is:
**how often does the auto-switch trigger?** — useful for validating the feature is used
and for future UX decisions.

## Changes

### `pypost/core/metrics.py`

Added a new Prometheus counter:

```
gui_method_body_autoswitches_total{method="POST|PUT"}
```

- **Name**: `gui_method_body_autoswitches_total`
- **Type**: Counter
- **Labels**: `method` (value: `"POST"` or `"PUT"`)
- **Description**: Number of times the Body tab was auto-selected due to method change.
- **Tracking method**: `MetricsManager.track_gui_method_body_autoswitch(method: str)`

### `pypost/ui/widgets/request_editor.py`

Called `MetricsManager().track_gui_method_body_autoswitch(method)` inside
`_on_method_changed`, immediately after the tab switch. Only fires when the guard
condition is met (`not self._loading and method in ("POST", "PUT")`).

## Example Prometheus Query

```promql
# Total auto-switches per method
sum by (method) (gui_method_body_autoswitches_total)
```
