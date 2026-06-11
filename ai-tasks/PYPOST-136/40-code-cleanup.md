# PYPOST-136: Code Cleanup

## Review

- Extracted `mcp_tools_signature()` as a module-level helper — single place for change
  detection, testable independently.
- `update_tools` return value avoids redundant UI "Starting" state when no restart occurs.
- No dead code removed; wired existing `update_tools` rather than duplicating restart logic.

## Items Addressed

| Item | Action |
| --- | --- |
| Unused `update_tools` | Wired from `EnvPresenter.refresh_mcp_tools` |
| Restart on identical save | Signature guard in manager |

## Worklog

role: execution, step: 4, step_name: Code Cleanup, tokens_used: 900
