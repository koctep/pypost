# PYPOST-554: Code Cleanup

## Static analysis

- Removed dead `_extract_mcp_variables` from `mcp_server_impl.py` (logic moved to policy).
- Fixed missing imports (`Set`, `jinja2`) left by partial refactor.

## Formatting

- All new/edited files respect 100-character line limit.

## Tests

```bash
.venv/bin/python -m pytest \
  tests/test_mcp_secrets_policy.py \
  tests/test_mcp_server_impl.py \
  tests/test_env_presenter.py -v
```

## Files touched

| File | Notes |
| --- | --- |
| `pypost/core/mcp_secrets_policy.py` | New policy module |
| `pypost/core/mcp_server_impl.py` | Policy integration |
| `pypost/core/mcp_server.py` | Supplier forwarding |
| `pypost/ui/presenters/env_presenter.py` | Hidden keys cache + supplier |
