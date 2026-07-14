# PYPOST-695: Architecture

## Composition root (after)

```text
main.py
  ConfigManager.load_config() → AppSettings
  StorageManager(metrics)
  storage.apply_encryption_settings(settings)   # before RequestManager / UI loads
  RequestManager(storage, defer_initial_load=True)
  MCPServerManager(metrics, template_service)
  MainWindow(..., storage=, request_manager=, mcp_manager=)
```

## MainWindow injection

| Parameter | Production | Fallback (tests) |
| --- | --- | --- |
| `storage` | injected from `main.py` | `StorageManager(metrics=…)` + init `apply_encryption_settings` |
| `request_manager` | injected from `main.py` | `RequestManager(storage, defer_initial_load=True)` |
| `mcp_manager` | injected from `main.py` | `MCPServerManager(metrics, template_service)` |

When `storage` is injected, `MainWindow` skips init-time `apply_encryption_settings` because
`main.py` already applied policy with the same `AppSettings`. Settings save still calls
`apply_encryption_settings` after `wait_storage_idle()`.

## Files touched

- `pypost/main.py` — wire three services
- `pypost/ui/main_window.py` — optional constructor params
- `doc/dev/architecture.md`, `doc/dev/testability.md`
- MainWindow-related tests
