# Test Log Guardrails and Capture (PYPOST-1081)

## Overview

PyPost enforces an automated **test log guardrail** during continuous integration (CI) and local
testing. The guardrail acts as a release safety gate by actively inspecting runtime logs emitted
during test suite execution. It audits all `ERROR` level events against a curated allowlist and
verifies that total error counts do not exceed approved baseline margins.

This mechanism ensures that unintended runtime errors, uncaught exceptions, and unhandled worker
failures fail the build rather than slipping through undetected.

## Architecture

### System Diagram

```text
+-----------------------------------------------------------------------+
|                            Pytest Session                             |
|                                                                       |
|  pytest --log-file=pytest.log --log-file-level=WARNING                |
|  +-----------------------------------------------------------------+  |
|  |                     _FileHandler (pytest.log)                   |  |
|  +-----------------------------------------------------------------+  |
|         ^                                            ^                |
|         | log records                                | log records    |
|  +---------------+                          +---------------------+   |
|  | Negative/Unit |                          | Embedded Servers    |   |
|  | Test Suites   |                          | (Metrics / MCP)     |   |
|  +---------------+                          +---------------------+   |
|                                             | log_config=None     |   |
|                                             +---------------------+   |
+-----------------------------------------------------------------------+
                                  |
                           writes pytest.log
                                  v
+-----------------------------------------------------------------------+
|                          CI Guardrail Gate                            |
|                                                                       |
|  scripts/verify_test_log_guardrails.py pytest.log                     |
|  +-----------------------------------------------------------------+  |
|  | 1. Parses log lines via parse_test_log_inventory.py             |  |
|  | 2. Matches ERROR lines against tests/expected_log_allowlist.yaml |  |
|  | 3. Checks count <= baseline_error_count + error_margin          |  |
|  | 4. Returns exit 0 (PASS) or exit 1 (FAIL)                       |  |
|  +-----------------------------------------------------------------+  |
+-----------------------------------------------------------------------+
```

### Logging Ownership & Handler Persistence

1. **Logging Ownership Invariant**: The host process (PyPost entrypoint `pypost/main.py` in
   production, or the pytest test runner in tests) owns process-wide logging configuration.
   Embedded background servers must treat host logging configuration as external and immutable.
2. **Handler Persistence Invariant**: Starting, stopping, or importing any module, fixture, or
   embedded server must never detach, mutate, or close handlers attached to the Python standard
   library root logger (`logging.getLogger()`).

### The Embedded Uvicorn `log_config=None` Contract

When background ASGI services (such as `MetricsServer` or `MCPServerManager`) start within the
PyPost desktop application or during test execution, they instantiate `uvicorn.Config`.

By default, `uvicorn.Config.__init__` sets `log_config=LOGGING_CONFIG` and invokes
`self.configure_logging()`. This internal setup performs:

1. `logging.config.dictConfig(self.log_config)`
2. `logging.config._clearExistingHandlers()`
3. `logging.shutdown(logging._handlerList[:])`

When `logging.shutdown()` runs, it calls `handler.close()` on every active handler in the process.
This closes pytest's internal file handler (`_pytest.logging._FileHandler`) and sets its file stream
to `None`. Subsequent log records emitted by tests or application code are silently discarded,
leaving `pytest.log` empty (0 bytes).

#### The Solution

All embedded uvicorn configurations in PyPost must pass `log_config=None`:

```python
config = uvicorn.Config(
    self.app,
    host=self.host,
    port=self.port,
    loop="asyncio",
    log_config=None,
    log_level="warning",
)
```

With `log_config=None`, uvicorn bypasses `dictConfig()`. The host logging hierarchy and pytest file
handlers remain open and fully functional throughout the entire test session. Uvicorn continues to
log via `logging.getLogger("uvicorn")` and `logging.getLogger("uvicorn.error")`, propagating
messages cleanly to root handlers.

#### Code Locations

- `pypost/core/metrics_server.py` (`MetricsServer._run_uvicorn`)
- `pypost/core/qt/mcp_server.py` (`MCPServerManager._run_uvicorn`)
- `tests/helpers/mcp_live_server.py` (`_run_uvicorn_in_thread`)

## Guardrail Verifier Tooling

### `scripts/verify_test_log_guardrails.py`

The verification script audits the captured test log file against the error allowlist:

```bash
python scripts/verify_test_log_guardrails.py pytest.log
```

#### Evaluation Rules

1. **Log Parsing**: Parses live log entries matching format
   `%(asctime)s %(levelname)s %(name)s: %(message)s` using `scripts/parse_test_log_inventory.py`.
2. **Error Filtering**: Extracts all records where `level == "ERROR"`.
3. **Allowlist Matching**: Checks each error record against `tests/expected_log_allowlist.yaml`:
   - **Logger + Prefix Rule**: Matches if `entry.logger == rule.logger` AND `entry.message` contains
     or starts with `rule.message_prefix`.
   - **Prefix-Only Rule**: Matches if `rule.logger` is omitted and `entry.message` contains or
     starts with `rule.message_prefix` regardless of logger name.
4. **Count Budget Enforcement**: Verifies that total error count does not exceed
   `baseline_error_count + error_margin` (e.g., 146 + 5 = 151).
5. **Exit Status**:
   - `0`: PASS — all error records match allowlist rules and total count is within budget.
   - `1`: FAIL — unlisted error lines detected or total error count exceeds maximum allowed.

## Allowlist Configuration (`tests/expected_log_allowlist.yaml`)

### Structure

```yaml
baseline_error_count: 146
error_margin: 5

rules:
  # Logger + prefix matching
  - logger: pypost.core.request_service
    message_prefix: request_execution_failed

  # Prefix-only matching across any logger
  - logger: test.guardrail
    message_prefix: guardrail_
```

### Approved Rule Domains

- `pypost.core.request_service`: `request_execution_failed`, `history_record_failed` (network)
- `pypost.core.qt.worker`: `RequestWorker unexpected error` (worker exception safety)
- `pypost.ui.presenters.tabs_presenter*`: `request_error` (UI error presentation)
- `pypost.ui.presenters.collection_tree_actions`: `collection_item_*_failed` (tree actions)
- `pypost.core.storage`: `load_environments_*`, `save_environments_*` (storage failures)
- `pypost.core.encryption_migration`: `encryption_migration_*` (migration error paths)
- `pypost.core.mcp_client_service`: `mcp_operation_failed`, `mcp_operation_timeout`
- `pypost.core.mcp_proxy_server_impl`: `mcp_proxy_*` (reverse proxy error handling)
- `pypost.core.http_client`: `http_*`, `yaml_to_json_*`, `template_integer_*`
- `pypost.core.key_provider`: `encryption_key_*` (missing key scenarios)
- `pypost.core.environment_secrets_codec`: `env_value_decrypt_failed`
- `pypost.core.qt.*_worker`: `*_worker_failed` (background worker failure paths)
- `uvicorn.error`: `[Errno 98]` (intentional port bind collision tests)
- `test.guardrail`: `guardrail_` (guardrail test suite emissions)
- `asyncio`: `Task was destroyed but it is pending` (async teardown noise)

### Caplog & Allowlist Contract (Rule C2)

Per `do-testing` rules, when introducing intentional negative test cases that trigger `ERROR` logs:
1. Assert log emission locally via pytest `caplog` or `unittest.TestCase.assertLogs`, **OR**
2. Register the structured event prefix in `tests/expected_log_allowlist.yaml` in the same PR.
3. If new tests increase the steady-state error count across the full suite, adjust
   `baseline_error_count` with documented rationale.

## Usage & Verification

### Running Tests with Log Capture

Run the test suite capturing warnings and errors to a log file:

```bash
# Fast test suite
pytest tests/ -m "not slow" --log-file=pytest.log --log-file-level=WARNING

# Run guardrail verification
python scripts/verify_test_log_guardrails.py pytest.log
```

### Running Dedicated Repro and Verifier Unit Tests

```bash
pytest tests/test_log_capture_guardrail_repro.py tests/test_verify_test_log_guardrails.py -v
```

## Troubleshooting

### 1. `pytest.log` is 0 bytes after running tests

- **Cause**: An embedded server or test module reconfigured logging using `dictConfig()`, closing
  active file handlers.
- **Fix**: Check any `uvicorn.Config` instantiations in new or modified code and ensure
  `log_config=None` is explicitly set.

### 2. Guardrail fails with "unlisted ERROR line(s)"

- **Example Output**:
  ```text
  ERROR count: 147 (max allowed: 151)
  FAIL: 1 unlisted ERROR line(s):
    line 42: [unknown] pypost.core.example: unexpected_service_error error=Connection reset
  ```
- **Diagnostics**:
  1. Inspect the reported line in `pytest.log`.
  2. Determine whether the error is an unintended regression or an intentional negative test.
  3. If it is an unintended regression, fix the underlying defect.
  4. If it is a legitimate negative test, add an entry to `tests/expected_log_allowlist.yaml`
     under `rules:` using the structured event prefix.

### 3. Guardrail fails with "ERROR count exceeds baseline + margin"

- **Example Output**:
  ```text
  ERROR count: 153 (max allowed: 151)
  FAIL: ERROR count 153 exceeds baseline + margin (151)
  ```
- **Diagnostics**:
  1. Check if multiple new error-path tests were added.
  2. Verify that no loop or retry logic is leaking runaway error logs.
  3. If all errors are valid, update `baseline_error_count` in `tests/expected_log_allowlist.yaml`
     and update the assertion in `tests/test_verify_test_log_guardrails.py`.
