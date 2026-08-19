# PYPOST-1081: Observability Implementation

## Logging Implementation

### Scope and Context

PYPOST-1081 addresses a critical gap in testing observability and CI release guardrails:
during pytest test execution, starting embedded ASGI servers (such as `MetricsServer` or
`MCPServerManager` via `AgentAppSession` / `uvicorn`) triggered `uvicorn.Config`'s default
logging initialization (`dictConfig`), which invoked `logging.shutdown()` and closed all active
file logging handlers. Consequently, pytest's `--log-file=pytest.log` handler had its stream set
to `None`, silencing all subsequent log capture for the remainder of the test session.

By configuring `log_config=None` in all embedded `uvicorn.Config` instantiations
(`pypost/core/metrics_server.py`, `pypost/core/qt/mcp_server.py`, `tests/helpers/mcp_live_server.py`),
root logging handlers and test log capture remain fully preserved and active throughout the entire
test lifecycle.

### Added Logs

No new runtime logging statements were introduced into production application paths by this task.
The core application already possessed structured logging at all critical execution and error
points; the defect was that emitted logs were silenced during test sessions.

In test harness and repro verification paths:
- **WARNING**: `tests/test_log_capture_guardrail_repro.py` — emits `guardrail_*` warning records
  on logger `test.guardrail` to verify pre-server startup logging capture.
- **ERROR**: `tests/test_log_capture_guardrail_repro.py` — emits `guardrail_*` error records
  on logger `test.guardrail` during and post-server shutdown to verify end-to-end capture persistence.

Existing application log levels preserved and verified:
- **EMERG / ALERT / CRIT**: Not used in PyPost's standard desktop client logging hierarchy.
- **ERR (ERROR)**: Emitted on operation failures, network errors, serialization/deserialization
  errors, bind collisions, and security/crypto errors across `pypost.core.*` and `pypost.ui.*`.
- **WARNING**: Emitted on non-fatal fallbacks, retries, deprecated configurations, and recoverable
  state anomalies.
- **NOTICE / INFO**: Emitted on key lifecycle events, session startup/shutdown, environment selection,
  dialog interactions, and MCP tool registration.
- **DEBUG**: Emitted on detailed diagnostics, raw payload parsing, and composition root injection
  sources.

### Log Structure

Log format used across application and test execution:
- Structured logs: **yes** — standard format follows `<event_name> key=value ...` with snake_case
  event names as the first token, or `%` formatting per `doc/dev/logging.md`.
- Includes context: **yes** — event parameters include `reason`, `instance_id`, `count`,
  `category`, `error_msg`, and relevant entity identifiers.
- Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
- Log record format in pytest capture:
  ```text
  %(asctime)s %(levelname)-8s %(name)s: %(message)s
  ```
  Example captured lines:
  ```text
  19:39:28 WARNING  test.guardrail: guardrail_metrics_before_start
  19:39:28 ERROR    test.guardrail: guardrail_metrics_after_start
  19:39:29 ERROR    pypost.ui.presenters.env_presenter: storage_save_failed error=Encryption key is unavailable.
  ```

### Sensitive Data Protection

Restoring log capture maintains all established data protection invariants:
- Secrets, tokens, unencrypted environment variables, and private payload contents are masked
  or excluded from log records prior to emission.
- MCP tool parameters log counts only (`doc/dev/mcp_secrets_policy.md`).
- Large data structures (such as complete collection hierarchies or raw network buffers) are
  never formatted directly into log messages.

---

## Metrics Implementation

### Performance Metrics

- **Response time**: `track_request_duration`, `track_mcp_tool_call_duration` (pre-existing in
  `pypost/core/request_service.py` and `pypost/core/mcp_client_service.py`).
- **Throughput**: Request execution throughput and MCP tool call frequencies monitored via
  Prometheus metrics server.
- **Error rate**: Error rates across HTTP requests and MCP operations tracked via metrics
  counters and verified via CI error guardrails.

### Business Metrics

- Active environment changes (`track_mcp_active_env_changed`).
- Collection operations and import/export events.

### System Health Metrics

- **Component status**: `set_mcp_server_instance_counts({stopped, starting, running, failed})`
  tracks lifecycle states of all managed MCP endpoints (`pypost/core/mcp_server_registry.py`).
- **Metrics Server health**: Embedded Prometheus ASGI endpoint exposed on configured port
  (default `:9108`) with endpoint scraping support.

### Guardrail Diagnostics (`scripts/verify_test_log_guardrails.py`)

The CI test log guardrail verification tool (`scripts/verify_test_log_guardrails.py`) provides
comprehensive diagnostics over the captured test log stream:
1. **Total Error Count Tracking**: Counts total `ERROR` level entries in `pytest.log`.
2. **Baseline and Margin Enforcement**: Compares observed `error_count` against `max_allowed`
   (`baseline_error_count` + `error_margin`, currently 146 + 5 = 151).
3. **Allowlist Matching**: Checks each emitted ERROR line against structured rules in
   `tests/expected_log_allowlist.yaml` by `message_prefix` and optional `logger` name.
4. **Unknown Error Reporting**: Identifies any unlisted ERROR line, reporting line number,
   inventory classification tag (`[expected]`, `[suspicious]`, `[unknown]`), logger name, and
   message snippet (up to 120 characters).
5. **Deterministic Exit Codes**: Returns exit code `0` on PASS (all errors allowed and count <= max),
   or exit code `1` on FAIL (unlisted errors found or count exceeded).

---

## Monitoring Integration

- [x] **Prometheus metrics**: Embedded `MetricsServer` running on background daemon thread,
      serving Prometheus metric collectors.
- [ ] **Grafana dashboards**: Repository contains client-side desktop application; dashboard
      templates managed externally.
- [x] **Alerting rules / Error Guardrails**: CI release gate enforces error allowlist and baseline
      budget on every test run.
- [x] **Log aggregation & CI verification**:
      - Pytest executes with `--log-file=pytest.log --log-file-level=WARNING` in `.github/workflows/test.yml:147`.
      - CI workflow runs `python scripts/verify_test_log_guardrails.py pytest.log` (`.github/workflows/test.yml:152`)
        as a required build step.
      - Any unexpected runtime ERROR or spike in error counts fails the workflow step immediately.

---

## Validation Results

- [x] **Logs are correctly formatted**: Structured log records retain time, level, logger name,
      and message content across all log levels.
- [x] **Metrics are collected correctly**: Prometheus metrics server and tracker protocols function
      without handler conflicts.
- [x] **Logging works in error scenarios**: Negative tests and failure handling scenarios
      consistently emit ERROR logs into `pytest.log`.
- [x] **Large data structures are not logged**: Only concise error summaries, prefixes, and counts
      are logged.
- [x] **Metrics are available for monitoring**: Guardrail verifier and metrics endpoints pass validation.
- [x] **CI gate is non-vacuous**: Verified that `scripts/verify_test_log_guardrails.py` processes
      146 real ERROR events on full test runs rather than evaluating an empty (0-byte) log file.

### Test Execution Verification

1. **Repro and Guardrail Tests**:
   ```sh
   .venv/bin/pytest tests/test_log_capture_guardrail_repro.py tests/test_verify_test_log_guardrails.py
   ```
   Output: **9 passed in 0.89s**.

2. **Test Slice Log Capture & Guardrail Verification**:
   ```sh
   .venv/bin/pytest tests/test_log_capture_guardrail_repro.py tests/test_env_presenter.py \
       --log-file=test_slice.log --log-file-level=WARNING
   .venv/bin/python scripts/verify_test_log_guardrails.py test_slice.log
   ```
   Output:
   ```text
   ERROR count: 5 (max allowed: 151)
   PASS: all ERROR lines match allowlist and count within margin
   ```

3. **Full Suite Log Capture & Guardrail Verification**:
   ```sh
   .venv/bin/pytest tests/ -m "not slow" -o log_cli=false --log-file=pytest.log --log-file-level=WARNING
   .venv/bin/python scripts/verify_test_log_guardrails.py pytest.log
   ```
   Result: Full test suite captures 146 real ERROR lines matching allowlist rules with exit code 0.

---

## Notes

### Non-Vacuous Guardrail Protection

Prior to PYPOST-1081, `scripts/verify_test_log_guardrails.py` evaluated a 0-byte log file because
uvicorn's `dictConfig` closed `_pytest.logging._FileHandler`. The verifier reported `ERROR count: 0`
and passed vacuously regardless of runtime regressions.

With `log_config=None` configured on all uvicorn servers:
- File handler file descriptors remain open and active across test collection and execution.
- 146 legitimate ERROR events emitted by intentional negative test cases (such as HTTP request failures,
  crypto key rotation errors, storage save failures, and bind collisions) are actively captured and audited.
- Any future regression that introduces an unexpected ERROR log or causes excessive error emissions
  will fail `scripts/verify_test_log_guardrails.py` in CI, restoring full guardrail protection.
