# PYPOST-162 — Architecture

## Current Flow

```
add_new_tab
  ├── RequestTab(...)
  ├── indent/env/template setup (inline)
  └── _wire_tab_signals(tab)
        ├── send_requested → closure (PYPOST-71)
        ├── save_requested → _handle_save_request(data) → _find_tab_for_sender()
        └── save_as_requested → _handle_save_as_request(data) → _find_tab_for_sender()
```

## Target Flow

```
add_new_tab
  └── _create_request_tab(data)
        ├── RequestTab(...)
        ├── indent/env/template setup
        └── _wire_tab_signals(tab)
              ├── send_requested → lambda data, t=tab: _handle_send_request(t, data)
              ├── save_requested → lambda data, t=tab: _handle_save_request(t, data)
              └── save_as_requested → lambda data, t=tab: _handle_save_as_request(t, data)
```

## Design Notes

- `_create_request_tab` is the only production entry point for new `RequestTab` instances.
- Default-arg closure `t=tab` binds the tab at connection time (project convention).
- `_request_tab_before_dialog` and `_find_tab_for_sender` removed — explicit tab makes them
  redundant after PYPOST-72.
- `copy_curl_requested` unchanged (handler needs only `RequestData`).

## Files

| File | Change |
|------|--------|
| `pypost/ui/presenters/tabs_presenter.py` | Factory method; closure wiring; handler signatures |
| `tests/test_tabs_presenter.py` | Direct-call test; update handler invocations |
| `doc/dev/request_execution.md` | Document save/save-as tab binding |

## Test Design

| Test | Purpose |
|------|---------|
| `test_handle_save_request_accepts_explicit_tab_without_sender` | AC-4: direct call routes save to given tab |
| PYPOST-72 dialog tab-switch tests | Regression: save still targets source tab |
| Save-flow integration tests | Regression: menu/shortcut paths unchanged |
