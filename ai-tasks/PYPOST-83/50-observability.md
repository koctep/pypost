# Observability Review — PYPOST-83: Fix Fragile Positional call_args in test_request_service

**Author:** Senior Engineer
**Date:** 2026-03-25
**Status:** Complete — no new instrumentation required

---

## 1. Scope of the Review

PYPOST-83 is a pure syntactic refactor limited to two files:

| File | Change |
|---|---|
| `pypost/core/request_service.py` | `send_request` call switched from positional to keyword arguments (lines 129–135) |
| `tests/test_request_service.py` | Three test assertions switched from `call_args[0][N]` to `call_args.kwargs["name"]` |

No logic, control flow, error handling, retry behaviour, or data paths were altered.

---

## 2. Existing Observability Inventory

`request_service.py` already carries comprehensive logging and metrics coverage. The table
below maps each instrumentation point to its log level and the metrics method called.

### 2.1 Logging

| Location | Level | Log key |
|---|---|---|
| `__init__` — injected `TemplateService` | `DEBUG` | `RequestService: using injected TemplateService id=…` |
| `_execute_http_with_retry` — start of each attempt | `DEBUG` | `http_attempt method=… url=… attempt=… max_retries=…` |
| `_execute_http_with_retry` — retryable HTTP status | `WARNING` | `retryable_status method=… url=… status=… attempt=…` |
| `_execute_http_with_retry` — retryable exception | `WARNING` | `retryable_error method=… url=… category=… attempt=…` |
| `_execute_http_with_retry` — backoff start | `DEBUG` | `retry_backoff method=… url=… attempt=… wait_seconds=…` |
| `_execute_http_with_retry` — cancel during backoff | `DEBUG` | `retry_cancelled_during_backoff method=… url=… attempt=…` |
| `_emit_exhaustion_alert` — all retries exhausted | `WARNING` | `retry_exhausted method=… url=… request_name=… retries=…` |
| `execute` — template render failure | `ERROR` | `template_render_failed url=… detail=…` |
| `execute` — `ExecutionError` caught | `ERROR` | `request_execution_failed method=… url=… category=… detail=…` |
| `execute` — history entry written | `DEBUG` | `history_entry_recorded method=… url=… status=… response_time_ms=…` |
| `execute` — history write failure | `ERROR` | `history_record_failed error=…` |

### 2.2 Metrics

| Method | Triggered on |
|---|---|
| `track_request_sent` | MCP request dispatched |
| `track_response_received` | MCP response received |
| `track_retry_attempt` | HTTP retry (before back-off wait) |
| `track_request_error` | `ExecutionError` caught in `execute` (HTTP or MCP) |
| `track_request_error(SCRIPT)` | Post-script execution failure |
| `track_email_notification_failure` | Retry exhaustion event |
| `track_history_entry_appended` | History entry successfully written |
| `track_history_record_error` | History write failure |

### 2.3 Alerting

`_emit_exhaustion_alert` emits an `AlertPayload` via `AlertManager` on retry exhaustion,
capturing `request_name`, `endpoint`, `retries_attempted`, `final_error_category`, and
`final_error_message`.

---

## 3. Impact Assessment of PYPOST-83

The refactored call site:

```python
# Before (PYPOST-83)
response = self.http_client.send_request(
    request, variables, stream_callback, stop_flag, headers_callback
)

# After (PYPOST-83)
response = self.http_client.send_request(
    request,
    variables=variables,
    stream_callback=stream_callback,
    stop_flag=stop_flag,
    headers_callback=headers_callback,
)
```

Python resolves keyword arguments to identical parameter slots at runtime. The call
produces the same `args`/`kwargs` mapping to `HTTPClient.send_request`; no observable
behaviour change occurs. All existing log statements and metrics calls surrounding this
line (the `http_attempt` debug log immediately before it, the retry/error paths
immediately after it) remain intact and continue to fire as before.

---

## 4. Gaps Identified

None. The refactor:

- Introduced no new code paths that could fail silently.
- Did not remove any existing log or metrics call.
- Did not add error-prone constructs (e.g., new exception types, new async paths, new
  external calls) that would warrant additional instrumentation.

---

## 5. Conclusion

No new logging, metrics, or monitoring is required for PYPOST-83. The existing
observability layer fully covers the execution path touched by this refactor. The review
confirms that the implementation is production-ready from an observability standpoint.
