# PYPOST-1162: Code Cleanup

## Scope

Hotkey routing extraction and WebSocket Session registration (Step 4).

## Checklist

- [x] `make lint` — no new flake8 violations
- [x] `tabs_presenter_hotkeys.py` extracted to keep presenter LOC manageable
- [x] No duplicate shortcut bindings (WS Connect/Send/Focus use help-only rows)
- [x] Targeted tests: `tests/test_main_window_hotkeys.py` (7 cases)

## Notes

`register_hotkey_documentation` added to `hotkeys.py` for Help rows that share
global bindings with Request Editor shortcuts.
