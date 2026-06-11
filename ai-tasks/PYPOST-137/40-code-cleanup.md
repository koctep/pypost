# PYPOST-137: Code Cleanup

## Lint and format

- No new linter issues in touched modules.
- Line length within 100 characters.

## Scope review

- Single helper `_track_mcp_active_env_changed` in `EnvPresenter` — no extra abstraction.
- Metric wired through existing `MetricsTrackerProtocol` → `MetricsRegistry` → `MetricsManager`.
- No unrelated refactors.

## Notes

Updated outdated `_current_variables` references in `doc/dev/mcp_integration.md` to
`EnvVariableSnapshot` while editing MCP docs.
