# PYPOST-74: Code cleanup

## Guard removal

Removed all `if self._metrics:` / `if self._metrics is not None:` wrappers from:

| Module | Calls unguarded |
| --- | --- |
| `request_service.py` | MCP/HTTP track, retry, history, errors |
| `http_client.py` | send/response, YAML conversion failure |
| `template_service.py` | render attempt / validation / error paths |
| `environment_variables_adapter.py` | encrypt/decrypt/error counters |
| `mcp_server_impl.py` | MCP request/response/duration/gauge |
| `request_editor.py` | GUI send/save/copy/method autoswitch |
| `response_view.py` | response search actions |
| `tabs_presenter.py` | new tab, send, history load, response received |
| `request_save_orchestrator.py` | save overwrite/new |

## Retained business guards

| Location | Condition kept |
| --- | --- |
| `_emit_history_masking_observability` | `hidden_key_count > 0` |
| `execute` error path | `exc.category != ErrorCategory.CANCELLED` |
| `_fallback_content_after_render_exception` | `not isinstance(exc, ValueError)` |

## Constructor normalization

All updated consumers assign `self._metrics = resolve_metrics(metrics)` (or propagate resolved
instance to composed objects via existing injection).

## Import fix

`environment_variables_adapter.py`: moved `resolve_metrics` to runtime import (was incorrectly
under `TYPE_CHECKING`).
