# PYPOST-695: Developer Documentation

## Summary

Documented `StorageManager`, `RequestManager`, and `MCPServerManager` in the composition-root
table and MainWindow injectable dependencies in `doc/dev/testability.md`. Updated
`doc/dev/architecture.md` composition-root diagram.

## Files Updated

| File | Change |
| --- | --- |
| `doc/dev/testability.md` | Added three service rows; MainWindow injection params |
| `doc/dev/architecture.md` | Updated composition-root flow; removed services from MainWindow list |

## Production wiring

```python
storage = StorageManager(metrics=metrics_manager)
storage.apply_encryption_settings(settings)
request_manager = RequestManager(storage, defer_initial_load=True)
mcp_manager = MCPServerManager(metrics=metrics_manager, template_service=template_service)
window = MainWindow(
    ...,
    storage=storage,
    request_manager=request_manager,
    mcp_manager=mcp_manager,
)
```

Tests should inject `MagicMock` or fakes via constructor rather than patching classes at
`main_window` when asserting DI retention.
