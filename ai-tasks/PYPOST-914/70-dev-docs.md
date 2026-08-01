# PYPOST-914: Dev Docs

## Updated

| Doc | Change |
| --- | --- |
| `doc/dev/agent_e2e_failure_artifacts.md` | Hook catch set (`_DUMP_HOOK_BEST_EFFORT_ERRORS`); PYPOST-914 test/troubleshooting |
| `doc/dev/logging.md` | `agent_session_failure_dump_hook_failed` narrowed to best-effort kinds |

## Verification

```bash
make test-agent-e2e PYTEST_ARGS="tests/test_agent_e2e_failure_artifacts.py::test_dump_hook_propagates_unexpected_exception -v"
make test-agent-e2e PYTEST_ARGS="tests/test_agent_e2e_failure_artifacts.py::test_dump_hook_failure_logs_warning -v"
```
