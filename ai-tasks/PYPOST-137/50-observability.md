# PYPOST-137: Observability

## Logging

| Level | Message | When |
| --- | --- | --- |
| INFO | `mcp_active_env_changed prev_env_id=%s new_env_id=%s` | Active environment **identity** changed while MCP was already running |

Existing `env_selected` logs unchanged. Same-env variable edits still log via `env_selected`
without `mcp_active_env_changed`.

## Metrics

| Metric | Type | Description |
| --- | --- | --- |
| `mcp_active_env_changes_total` | Counter | Environment identity changed while MCP server was running |

Access via Prometheus scrape on metrics port (9080) / MCP metrics resource.

## Validation

- [x] `test_tracks_mcp_active_env_changed_when_switching_while_running`
- [x] `test_does_not_track_mcp_active_env_changed_on_same_env_refresh`
- [x] `test_tracks_mcp_active_env_changed_when_deselecting_while_running` + caplog
- [x] `test_track_mcp_active_env_changed` (registry scrape)

No secret values in logs (env ids only).
