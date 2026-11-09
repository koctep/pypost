# PYPOST-1493: Observability

## Scope

Test-harness only (`tests/helpers/mcp_stdio_harness.py`). No production MCP
listen-path changes.

## Logging Added

| Location | Level | Event / fields |
| --- | --- | --- |
| `wait_for_stderr` (success) | DEBUG | `mcp_stdio_harness_stderr_ready substring=%r bytes=%d` |
| `wait_for_stderr` (timeout) | WARNING | `mcp_stdio_harness_stderr_wait_timeout substring=%r timeout=%s stderr_bytes=%d` |

No large payloads or credentials are logged (substring preview via `%r`, byte
counts only).

## Metrics

N/A — test helper; no Prometheus/OTel counters for suite-only stderr waits.

## Validation

- Success path exercised by
  `test_harness_stderr_collection` and
  `test_harness_stderr_visible_when_emitted_after_response`.
- Timeout path raises `TimeoutError` with stderr snapshot in the message.

## Checklist

- [x] Structured context on stderr wait ready/timeout
- [x] No sensitive data in logs
- [x] N/A production metrics for this debt fix
