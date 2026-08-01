# PYPOST-949: Code Cleanup

## Lint / format

- `make lint` — clean (flake8 on `pypost/`).
- Scoped tests: `make test PYTEST_ARGS='tests/test_ui_wait.py tests/test_agent_e2e_http_seed_post.py'` — 12 passed.

## Changes reviewed

| File | Notes |
| --- | --- |
| `pypost/agent/lifecycle.py` | Reused `_action_root`; no duplicate tab-resolution logic |
| `tests/test_ui_wait.py` | Imports grouped; multi-tab test mirrors golden fixtures |
| `tests/helpers/agent_e2e_send_settle.py` | Removed free-function import; delegates to session API |

## Intentional deferrals

- Golden e2e still uses module-level `wait_for_text(tab, …)` — valid, not migrated.
- Full `make check` not run (scoped gate sufficient for this narrow API change).

## Worklog

```
tokens_used: 4000
role: execution
step: 5
step_name: Code Cleanup
```
