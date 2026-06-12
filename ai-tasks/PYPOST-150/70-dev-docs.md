# PYPOST-150: Dev Docs

## Updates

| File | Change |
| --- | --- |
| `doc/dev/testing.md` | Added MCP/metrics host-bind integration row for `test_server_bind_host_integration.py` |

## Verification

```bash
make test
.venv/bin/python -m pytest tests/test_server_bind_host_integration.py -v
```
