# PYPOST-833: Dev Docs Update

## Changes

### `doc/dev/agent_lifecycle.md`

Expanded the Step 3 stub into full developer docs:

- Overview, architecture (shared `compose_app`, event-loop model, ready gate,
  isolation, dependency rules)
- API / usage for `AgentAppSession`, `is_ui_ready`, and `compose_app`
- Configuration knobs (offscreen, temp dirs, ephemeral metrics, ready timeout)
- Observability pointer to the logging catalog
- Smoke coverage note
- Troubleshooting table
- Sibling out-of-scope and related-docs links

### `doc/dev/logging.md`

Added Application lifecycle catalog rows (deferred from Step 5):

- `main_window_ui_ready`
- `agent_session_started` / `agent_session_ready` / `agent_session_ready_timeout`
- `agent_session_shutdown_started` / `agent_session_shutdown_completed`
- `agent_session_*_failed` (MCP stop, handle_exit, window close, metrics stop,
  temp cleanup)

Cross-link to `doc/dev/agent_lifecycle.md` from the catalog section and Related
Documentation table.

### Cross-links (already present; verified)

- `doc/dev/README.md` — Testing section lists Agent App Lifecycle
- `doc/dev/gui_testing.md` — Agent lifecycle section points at
  `agent_lifecycle.md` and the smoke test

### Roadmap / observability artifact

- Step 7 marked `[x]` in `00-roadmap.md`
- Step 5 deferred catalog checkbox marked done in `50-observability.md`

## Step 7 review fix

- Removed duplicate `## Troubleshooting` heading in `agent_lifecycle.md`
- Documented post-shutdown accurately: `window` raises `RuntimeError`;
  `app` may still return `QApplication` (`_app` not cleared)
- Logging catalog: `agent_session_started` fields `dirs` → `config_dir`,
  `data_dir`

## Validation

- [x] Docs match `pypost/agent/lifecycle.py` and `MainWindow.is_ui_ready`
- [x] Event names/fields match Step 5 observability implementation
- [x] Template sections covered (Overview, Architecture, Usage, Configuration,
  Troubleshooting)
- [x] Post-shutdown `app` / `window` behavior matches `lifecycle.py`
