# PYPOST-961: Observability

## Existing events (unchanged)

| Event | Level | When |
| --- | --- | --- |
| `agent_session_failure_dump_hook_failed` | WARNING | Hook raises a `DUMP_BEST_EFFORT_ERRORS` member |

Parametrized test asserts `error=<ExcType>` for each tuple member.

## Verification commands

```bash
make test-agent-e2e PYTEST_ARGS="tests/test_agent_e2e_failure_artifacts.py::test_dump_hook_best_effort_per_type -v"
make test-agent-e2e PYTEST_ARGS="tests/test_agent_e2e_failure_artifacts.py::test_dump_hook_failure_logs_warning tests/test_agent_e2e_failure_artifacts.py::test_dump_hook_propagates_unexpected_exception -v"
```

## Caplog contract

- Logger: `pypost.agent.lifecycle`
- Level: `logging.WARNING`
- Assert prefix: `agent_session_failure_dump_hook_failed error=`

Original test `AssertionError` must propagate (hook must not replace primary
failure).
