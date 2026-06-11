# PYPOST-67: Observability

## Summary

No observability changes required. `reload_current_env()` delegates to `_on_env_changed`, which
already logs `env_selected`, `env_deselected`, and MCP lifecycle events.

## Existing coverage

| Event | Logger | Level |
|-------|--------|-------|
| Environment selected | `env_presenter` | INFO |
| Environment deselected | `env_presenter` | INFO |
| MCP start/stop | `env_presenter` | INFO |
| Settings applied | `main_window` | INFO |

## Decision

No new log lines or metrics — behavior path is unchanged; only the call boundary moved.
