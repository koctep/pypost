# PYPOST-249: Developer Documentation

## Overview

Added dedicated developer documentation for the `StateManager` / `ConfigManager` boundary and
recorded the PYPOST-29 debt decision (document, do not rewrite).

## Files Created / Updated

| File | Change |
| --- | --- |
| `doc/dev/state_manager.md` | New — design contract, save paths, API, troubleshooting |
| `doc/dev/architecture.md` | StateManager bullet updated with link |
| `pypost/core/state_manager.py` | Module docstring, `_UI_STATE_FIELDS`, class docstring |

## Key Points for Developers

- **UI session fields:** `expanded_collections`, `open_tabs`, `last_environment_id` only.
- **Shared settings:** `MainWindow.settings` is `state_manager.settings` — by design.
- **Granular API updates:** `set_*` no-ops when unchanged; debounce coalesces writes.
- **Preferences:** Settings dialog → immediate `ConfigManager.save_config`.
- **Shutdown:** `flush_pending_save()` in `MainWindow.handle_exit()`.

## Configuration

See `doc/dev/state_manager.md` — debounce constant `_UI_STATE_SAVE_DEBOUNCE_MS = 300`.

## Troubleshooting

See the troubleshooting table in `doc/dev/state_manager.md`.
