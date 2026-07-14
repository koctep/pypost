# PYPOST-695: Observability

## Startup logs (main.py)

| Event | Level | Fields |
| --- | --- | --- |
| `storage_created` | INFO | `id`, `encryption_applied=true` |
| `request_manager_created` | INFO | `id` |
| `mcp_manager_created` | INFO | `id` |

## MainWindow debug logs

| Event | When |
| --- | --- |
| `storage_source source=injected\|new` | Constructor |
| `request_manager_source source=injected\|new` | Constructor |
| `mcp_manager_source source=injected\|new` | Constructor |

Existing `storage_encryption_config_applied` logs from `open_settings()` unchanged.
