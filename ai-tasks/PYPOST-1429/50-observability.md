# PYPOST-1429: Observability Implementation

## Logging Implementation

### Scope and Context

`tests/helpers/mcp_stdio_harness.py` is a dedicated test infrastructure harness supporting child process lifecycle management, non-blocking asynchronous standard I/O draining, response registry synchronization, and timeout enforcement. As a shared test harness module, observability is primarily realized through deterministic exception diagnostics, stderr buffer capturing, and clean test-runner compatibility (zero unstructured stdout pollution or noisy debug prints).

### Added Logs

Mapped logging levels and diagnostic event reporting across the `McpStdioHarness` lifecycle:

- **EMERG**: N/A - Test harness does not manage kernel or host-level infrastructure emergencies.
- **ALERT**: N/A - Test harness does not manage operator alerting infrastructure.
- **CRIT**: N/A - Critical system failures in test execution surface directly as fatal test harness exceptions.
- **ERR**:
  - `tests/helpers/mcp_stdio_harness.py:wait_for_response` - `TimeoutError` raised when expected response ID fails to arrive within deadline; diagnostic message includes request ID, timeout threshold, and full captured child stderr.
  - `tests/helpers/mcp_stdio_harness.py:wait_for_responses` - `TimeoutError` raised when batch response count threshold is not met; message reports expected count, collected count, timeout duration, and captured child stderr.
  - `tests/helpers/mcp_stdio_harness.py:wait_for_predicate` - `TimeoutError` raised when custom state predicate fails to evaluate to `True` before timeout; message includes timeout threshold and captured child stderr.
  - `tests/helpers/mcp_stdio_harness.py:wait_for_exit` - `TimeoutError` chained from `subprocess.TimeoutExpired` when process does not exit within deadline.
  - `tests/helpers/mcp_stdio_harness.py:send_raw` - `RuntimeError` raised on broken pipe (`BrokenPipeError` / `OSError`) or writes to dead/closed processes.
  - `tests/helpers/mcp_stdio_harness.py:_stdout_worker` - Captures unparsable child stdout lines into `_stdout_decode_errors` and diagnostic stderr buffer (`stdout decode error: <exc>`).
- **WARNING**:
  - `tests/helpers/mcp_stdio_harness.py:stop` - Graceful exit timeout expired during child process shutdown; falls back to immediate forceful termination (`kill()`).
  - `tests/helpers/mcp_stdio_harness.py:close_stdin` - Handled `BrokenPipeError`/`OSError` during stdin pipe flush/close if child process terminated prematurely.
- **NOTICE**:
  - `tests/helpers/mcp_stdio_harness.py:start` - Child process successfully spawned (`subprocess.Popen` with pipe redirection) and worker threads started.
  - `tests/helpers/mcp_stdio_harness.py:stop` / `kill` - Child process terminated, background threads joined, and exit returncode recorded.
- **INFO**:
  - `tests/helpers/mcp_stdio_harness.py:__enter__` / `__exit__` - Test context lifecycle boundary entry and exit with guaranteed process teardown.
  - `tests/helpers/mcp_stdio_harness.py:send_request` / `send_notification` - High-level JSON-RPC protocol message dispatch.
- **DEBUG**:
  - `tests/helpers/mcp_stdio_harness.py:_stdout_worker` - Inbound line read from child stdout, decoded, and matched to response registry.
  - `tests/helpers/mcp_stdio_harness.py:_stderr_worker` - Inbound line read from child stderr and appended to captured stderr buffer.

### Log Structure

Log format and diagnostic error structure:
- Structured logs: Yes (structured JSON-RPC messages decoded and stored in `_messages` and `_responses`; exception diagnostics follow standard parameterized formats).
- Includes context: Yes (exceptions explicitly include `request_id`, total counts, elapsed timeout seconds, and captured child process `stderr` contents).
- Log levels: `ERR`, `WARNING`, `NOTICE`, `INFO`, `DEBUG` (mapped via syslog convention and standard Python exceptions).
- Sanitization & Payload Protection:
  - Zero leakage of auth tokens or credentials: Only protocol envelope parameters and error messages are captured.
  - Oversized binary dump prevention: Large payload tests (e.g. 1MB-5MB bursts) do not dump raw payloads into exception strings; only discrete counts, IDs, and stderr error text are retained.

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance and operational metrics (accessible via harness APIs for test assertions and CI diagnostics):
- **Response time**: Measured via bounded condition wait deadlines (`wait_for_response`, `wait_for_responses`, `wait_for_predicate`).
- **Throughput**: Burst processing of multiple simultaneous requests verified without pipe buffer exhaustion (>64KB OS pipe capacity).
- **Error rate**: Tracked via `_stdout_decode_errors` list and child process exit code (`returncode`).

### Business Metrics

Operational test harness metrics:
- **Total messages received**: Exposed via `harness.get_messages()` (`list[dict[str, Any]]`).
- **Total responses correlated**: Exposed via `harness.get_all_responses()` (`dict[Any, dict[str, Any]]`).
- **Stderr diagnostic length**: Exposed via `len(harness.get_stderr())`.

### System Health Metrics

System health metrics:
- **Resource usage**: OS pipe buffers drained continuously in non-blocking daemon threads to prevent deadlocks and memory bloat; thread joins enforce bounded wait times (1.0s maximum join wait).
- **Component status**: Child process alive status exposed via `harness.is_alive` property; exit code via `harness.returncode`.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics (N/A - test helper module running within transient pytest suites)
- [ ] Grafana dashboards (N/A - test helper module)
- [x] Alerting rules (Failures surface immediately as standard pytest assertion/timeout errors in CI)
- [x] Log aggregation (Captured child process stderr and stdout errors aggregated directly into pytest failure outputs)

## Validation Results

Validation results:
- [x] Logs are correctly formatted: Exceptions provide deterministic, structured diagnostic messages.
- [x] Metrics are collected correctly: Internal message counters, response registry, and return codes accurately reflect subprocess state.
- [x] Logging works in error scenarios: Stderr capture attached to `TimeoutError` and `_stdout_decode_errors` caught safely.
- [x] Large data structures are not logged: Raw multibyte/burst message payloads are not dumped into exception diagnostics.
- [x] Metrics are available for monitoring: Internal inspection properties (`is_alive`, `returncode`, `get_stderr()`, `get_messages()`, `get_all_responses()`) fully accessible.

## Notes

- `McpStdioHarness` adheres to `lsr-python` and `do-testing` rules: no raw `print()` statements are emitted to pollute stdout.
- All waiting routines enforce explicit timeout parameters, eliminating non-deterministic test hangs during CI runs.
