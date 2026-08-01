# PYPOST-914: Observability Implementation

## Existing events (unchanged semantics for best-effort kinds)

| Event | Level | When |
| --- | --- | --- |
| `agent_session_failure_dump_hook_failed` | WARNING | Hook raises a best-effort type from `_DUMP_HOOK_BEST_EFFORT_ERRORS` |

## Behavior change

| Scenario | Before (PYPOST-875/912) | After (PYPOST-914) |
| --- | --- | --- |
| Hook raises `RuntimeError` | WARNING + shutdown | Same |
| Hook raises `LookupError` | WARNING + shutdown (bug hidden) | Propagates from `__exit__` |

## Verification

```bash
make test-agent-e2e PYTEST_ARGS="tests/test_agent_e2e_failure_artifacts.py::test_dump_hook_propagates_unexpected_exception -v"
make test-agent-e2e PYTEST_ARGS="tests/test_agent_e2e_failure_artifacts.py::test_dump_hook_failure_logs_warning -v"
```

Catalog: `doc/dev/logging.md` cross-link updated for PYPOST-914 catch set.
