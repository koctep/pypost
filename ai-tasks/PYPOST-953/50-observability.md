# PYPOST-953: Observability

## Runtime logging / metrics

**N/A** — test-only guard; no new production code paths, logs, or metrics.

## CI signal

- Failure message includes sorted offending tool names for quick diagnosis.
- Run target:

```bash
make test PYTEST_ARGS='tests/test_mcp_server_impl.py::TestMCPServerImpl::test_list_tools_excludes_agent_ui_action_names -v'
```

## Checklist

- [x] No new DEBUG/INFO emission required
- [x] Test failure is self-describing (assert message lists overlap / `ui_*` names)
