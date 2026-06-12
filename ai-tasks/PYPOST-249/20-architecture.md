# PYPOST-249: StateManager design documentation

## Research

### Current wiring

```text
main.py / MainWindow
    ConfigManager (load/save settings.json)
    StateManager(config_manager)
        settings ← same AppSettings instance as MainWindow.settings
        manages: expanded_collections, open_tabs, last_environment_id
        debounced save → config_manager.save_config(settings)
    Settings dialog → MainWindow.open_settings()
        config_manager.save_config(settings)  # immediate, all fields
```

### Fields by owner

| Field group | Owner | Save path |
| --- | --- | --- |
| `expanded_collections`, `open_tabs`, `last_environment_id` | `StateManager` | Debounced / flush / `save()` |
| All other `AppSettings` fields | `MainWindow` / dialogs | Immediate `ConfigManager.save_config` |

### Granular updates (existing)

- Each `set_*` compares new value to current; no-op skips scheduling.
- Rapid changes coalesce via 300 ms debounce (PYPOST-386).
- Disk write still serializes full `AppSettings` — acceptable for small JSON.

## Decision

**Document, do not rewrite.**

Rationale:

1. Shared mutable `AppSettings` is intentional: one on-disk file, one in-memory object.
2. `StateManager` already provides granular *API* updates for its three fields.
3. Partial JSON persistence adds complexity without measurable benefit today.
4. Tests and debounce behavior are established (PYPOST-252, PYPOST-386).

## Implementation Plan

1. Add module-level design contract and `_UI_STATE_FIELDS` in `state_manager.py`.
2. Create `doc/dev/state_manager.md` (overview, architecture, API, troubleshooting).
3. Link from `doc/dev/architecture.md` StateManager bullet.

No behavior changes required.
