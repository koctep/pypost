# PYPOST-733: Architecture

## Approach

Minimal, in-place handler narrowing — no new abstractions or exception hierarchies.

### storage.py

| Site | Before | After |
| --- | --- | --- |
| `_ensure_paths` (×3) | `Exception` | `OSError` |
| `load_collections` | `Exception` | `OSError`, `json.JSONDecodeError`, `ValidationError` |
| `save_environments` replace | `Exception` | `OSError` |
| `_read_environment_records` | `Exception` | `OSError`, `json.JSONDecodeError` |
| `deserialize_environment_records` | `Exception` + `logger.error` | `Exception` + `logger.exception` (defensive last resort) |

### alert_manager.py

| Site | Before | After |
| --- | --- | --- |
| stale handler `close()` | `Exception` | `OSError` |
| `close()` handler | `Exception` | `OSError` |
| `removeHandler()` | `Exception` | removed (stdlib no-op when absent) |
| `_send_webhook` | `Exception` | `requests.Timeout`, `ConnectionError`, `RequestException` |

### request_manager.py

No `except` blocks — delegates to `StorageManager.load_collections()`; no change required.

## Tests

- `tests/test_storage_environments.py` — invalid JSON, non-list root
- `tests/test_storage_collections.py` — corrupt JSON, invalid schema
- `tests/test_alert_manager.py` — `RequestException` webhook path
