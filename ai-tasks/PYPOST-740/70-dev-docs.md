# PYPOST-740: Dev Docs

> Jira: [PYPOST-740](https://pypost.atlassian.net/browse/PYPOST-740)

## What Changed

Renamed `pypost/core/request_sync.py` to **`request_persisted_fields.py`** to reflect
persisted-field copy/compare helpers (not HTTP sync).

## Documentation Updated

| File | Change |
| --- | --- |
| `doc/dev/architecture.md` | Directory tree entry |
| `doc/dev/request_data_copy_policy.md` | Module path and test reference |
| `doc/dev/open_request_in_isolated_tab.md` | Module path and API section headings |
| `doc/dev/mcp_integration.md` | `_PERSISTED_FIELD_NAMES` module reference |

## For Maintainers

Import persisted-field helpers from:

```python
from pypost.core.request_persisted_fields import (
    copy_request_for_isolated_tab,
    persisted_fields_equal,
    snapshot_persisted_fields,
)
```

Do not confuse with `MCPServerImpl._execute_request_sync` (MCP tool execution path).

## Related Docs

- [request_data_copy_policy.md](../../doc/dev/request_data_copy_policy.md)
- [open_request_in_isolated_tab.md](../../doc/dev/open_request_in_isolated_tab.md)
- [PYPOST-687 audit](../../ai-tasks/PYPOST-687/30-audit-report.md) — R-P3-004 finding

## Checklist

- [x] Active dev docs reference `request_persisted_fields`
- [x] R-P3-004 remediation complete
