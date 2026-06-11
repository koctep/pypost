# PYPOST-49: Developer Documentation

## Purpose

Close PYPOST-40 audit R7 by documenting verification of the metrics module split (implemented
in PYPOST-75).

## Modified Files

| File | Change |
|------|--------|
| `doc/dev/tech-debt/PYPOST-40.md` | Mark PYPOST-49 / R7 resolved |
| `doc/dev/architecture.md` | Update MetricsManager description (facade, not singleton) |
| `doc/dev/solid_audit.md` | Strike through R7 split recommendation |

## Existing Documentation (unchanged)

| File | Content |
|------|---------|
| `doc/dev/mcp_integration.md` | Three-module metrics stack (PYPOST-75) |
| `doc/dev/testability.md` | Registry vs server split at composition root |
| `doc/dev/testing.md` | Metrics test matrix including registry and server tests |

## Key Takeaways for Developers

- Import `MetricsRegistry` for counter-only unit tests (no server thread).
- Import `MetricsManager` at composition root and injection sites (unchanged).
- `MetricsServer` is internal to the facade; do not start uvicorn outside `MetricsManager`
  unless testing server endpoints via `MetricsServer._create_app()`.

## Related Tests

```bash
.venv/bin/python -m pytest \
  tests/test_metrics_manager.py \
  tests/test_metrics_registry.py \
  tests/test_metrics_server_endpoint.py -v
```
