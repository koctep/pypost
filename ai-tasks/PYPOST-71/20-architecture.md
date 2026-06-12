# PYPOST-71 — Architecture

## Current Flow

```
_wire_tab_signals(tab)
  └── send_requested → _handle_send_request(request_data)
        └── loop tabs; match tab.request_editor == self.sender()
```

## Target Flow

```
_wire_tab_signals(tab)
  └── send_requested → lambda data, t=tab: _handle_send_request(t, data)
        └── use sender_tab directly (no sender lookup)
```

## Design Notes

- Default-arg closure `t=tab` binds the tab at connection time (safe for per-tab wiring).
- `handle_send_request_global` unchanged: it calls `tab.request_editor.on_send()`, which
  still emits `send_requested` and hits the closure-bound handler.
- `_find_tab_for_sender` remains for save/copy paths; out of scope for PYPOST-71.

## Files

| File | Change |
|------|--------|
| `pypost/ui/presenters/tabs_presenter.py` | Closure connect; new handler signature |
| `tests/test_tabs_presenter.py` | Direct-call test without sender context |

## Test Design

| Test | Purpose |
|------|---------|
| `test_handle_send_request_accepts_explicit_tab_without_sender` | AC-4: direct call routes worker to given tab |
| Existing `test_worker_race.py` / send propagation tests | Regression: signal path unchanged |
