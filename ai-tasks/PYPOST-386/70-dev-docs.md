# PYPOST-386: Developer Documentation

## Overview

Updated developer docs to describe debounced UI-state persistence in `StateManager`.

## Files Updated

| File | Change |
| --- | --- |
| `doc/dev/architecture.md` | StateManager debounce + flush-on-exit behavior |
| `doc/dev/collection_tree_actions.md` | Expand/collapse persistence note and test coverage |

## Key Points for Developers

- **Debounced fields:** `expanded_collections`, `open_tabs`, `last_environment_id` via
  `StateManager.set_*` methods.
- **Immediate saves:** Settings dialog OK → `MainWindow.open_settings()` →
  `config_manager.save_config()` (unchanged).
- **Shutdown:** `MainWindow.handle_exit()` calls `state_manager.flush_pending_save()` before
  quit.
- **Testing:** After `set_*` calls in unit tests, call `flush_pending_save()` or process the Qt
  event loop until the debounce timer fires.

## Configuration

Debounce interval: `_UI_STATE_SAVE_DEBOUNCE_MS = 300` in `pypost/core/state_manager.py` (not
user-configurable).

## Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Test expects immediate disk write after `set_*` | Debounce defers write | Call `flush_pending_save()` or wait for timer |
| Expansion lost after normal quit | Flush not called on exit | Verify `handle_exit()` path |
| Settings not saved from dialog | Unrelated to debounce | Check `open_settings()` / dialog accept path |
