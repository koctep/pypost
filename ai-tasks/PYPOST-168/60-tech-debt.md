# PYPOST-168: Technical Debt Analysis

## Resolution

Metrics optional via constructor injection (`metrics=None`). Residual import coupling to
`pypost.core.metrics` is documented and accepted for current scope.

## Artifacts

- `pypost/core/http_client.py`
- `pypost/core/mcp_server.py`
- `pypost/core/mcp_server_impl.py`

## Blocker Review

**Verdict: SAFE TO CLOSE** — optional injection in place; accepted coupling documented.
