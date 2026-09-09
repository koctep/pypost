# StateManager

## Overview

`StateManager` persists high-frequency UI session state (expanded tree nodes, open tabs, last
environment) to the user settings file. It sits between UI presenters and `ConfigManager`,
providing typed getters/setters and debounced saves so rapid UI interactions do not trigger
redundant disk I/O. Debounced persistence closed debt
[PYPOST-90](https://pypost.atlassian.net/browse/PYPOST-90) and
[PYPOST-96](https://pypost.atlassian.net/browse/PYPOST-96) (implemented in
[PYPOST-386](https://pypost.atlassian.net/browse/PYPOST-386)).

User preferences (font size, metrics ports, encryption options, etc.) are **not** routed through
`StateManager`; the Settings dialog saves them immediately via `ConfigManager`.

## Architecture

```text
ConfigManager.load_config() → AppSettings (single in-memory object)
         ↑                              ↑
         │                              │
  save_config (immediate)         StateManager.set_* (debounced)
         │                              │
  MainWindow.open_settings()      CollectionsPresenter, TabsPresenter, …
```

### Shared `AppSettings` object

The composition root loads one `AppSettings`, passes it to `StateManager`, and injects both into
`MainWindow`. The window exposes a read-only `settings` property, and rejects a state manager
backed by a different object. Presenters and dialogs therefore read the same authoritative
snapshot.

Settings-dialog results are first persisted as a candidate. Only after that atomic write succeeds
are their fields copied into the authoritative object; the object itself is never replaced. This
keeps presenters and an already scheduled debounce on the current preferences.

`StateManager` does **not** duplicate or subset the model on disk. It restricts **which fields
it mutates through its public API** (`_UI_STATE_FIELDS` in `state_manager.py`).

### Save paths

| Trigger | Path | Timing |
| --- | --- | --- |
| Tree expand/collapse, tab open/close, env switch | `StateManager.set_*` | Debounced (300 ms) |
| Settings dialog OK | `config_manager.save_config` | Immediate |
| Application exit | `state_manager.flush_pending_save()` | Immediate flush of pending UI state |
| Tests / forced persist | `StateManager.save()` or `flush_pending_save()` | Immediate |

Full settings JSON is written on every save. `ConfigManager` serializes writes with a lock, writes
and fsyncs a temporary file in the config directory, then replaces `settings.json`. A failed write
raises `ConfigPersistenceError`, does not advance the in-memory revision, and leaves the previous
primary file intact. Malformed JSON is moved to a timestamped quarantine file before defaults are
used, and the startup UI reports that recovery.

## API / Usage

### Managed fields

- `expanded_collections` — collection tree expansion ids
- `open_tabs` — open HTTP request ids and **saved** WebSocket profile
  ids. Unsaved WebSocket drafts are omitted (registry gate; see
  [websocket_draft_tab.md](websocket_draft_tab.md)). Unsaved MCP Client
  drafts are omitted (see [mcp_client_draft_tab.md](mcp_client_draft_tab.md))
- `last_environment_id` — last selected environment

### Public methods

| Method | Purpose |
| --- | --- |
| `get_expanded_collections()` / `set_expanded_collections(ids)` | Tree expansion state |
| `get_open_tabs()` / `set_open_tabs(ids)` | Tab bar state |
| `get_last_environment_id()` / `set_last_environment_id(env_id)` | Environment selection |
| `save()` | Persist immediately (stops debounce timer) |
| `flush_pending_save()` | Write pending debounced changes before shutdown |

All `set_*` methods no-op when the value is unchanged (no save scheduled).

### Example (presenter)

```python
if self.state_manager.get_open_tabs() != tab_ids:
    self.state_manager.set_open_tabs(tab_ids)
```

### Example (test)

```python
sm = StateManager(config_manager, authoritative_settings)
sm.set_expanded_collections(["c1"])
sm.flush_pending_save()  # required before asserting on disk
```

## Configuration

Debounce interval: `_UI_STATE_SAVE_DEBOUNCE_MS = 300` in `pypost/core/qt/state_manager.py`
(not user-configurable).

## Related documentation

- [architecture.md](architecture.md) — core module overview
- [collection_tree_actions.md](collection_tree_actions.md) — tree expand persistence
- [testing.md](testing.md) — `TestStateManagerPersistence` run commands
- [websocket_draft_tab.md](websocket_draft_tab.md) — registry-gated WS `open_tabs`
- [mcp_client_draft_tab.md](mcp_client_draft_tab.md) — MCP Client draft omit

## Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Test expects immediate disk write after `set_*` | Debounce defers write | Call `flush_pending_save()` or process Qt event loop until timer fires |
| Preference change not visible in UI | Wrong object reference | Verify composition injected the same object into `MainWindow` and `StateManager` |
| UI state lost on normal quit | Flush not called | Verify `MainWindow.handle_exit()` calls `flush_pending_save()` |
| Unsaved WS draft id in `open_tabs` | Persist skipped registry gate | Omit ids not in `WebSocketRegistry` |
| Settings dialog change overwritten | Saving UI state after dialog | Settings path uses immediate save; UI fields should not reset preferences |

## Future work (non-blocking)

- Split `AppSettings` into preference vs session models if the settings surface grows
  significantly.
- Partial JSON writes only if profiling shows settings save latency matters.

See Jira [PYPOST-249](https://pypost.atlassian.net/browse/PYPOST-249) for the documented
decision to defer these refactors.
