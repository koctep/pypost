# PYPOST-44: Observability

## Summary

This document records the logging and monitoring additions made during the observability step for
PYPOST-44 (MetricsManager singleton removal). All changes are additive and do not alter runtime
behaviour.

---

## Changes Made

### 1. `pypost/core/metrics.py` — Replace `print()` with structured logging

**Problem:** `start_server` and `stop_server` used `print()` for lifecycle events, which cannot
be redirected, filtered, or captured by standard log handlers.

**Fix:**
- Added `import logging` and `logger = logging.getLogger(__name__)`.
- Replaced `print(f"Metrics server started on {host}:{port}")` with
  `logger.info("Metrics server started on %s:%d", host, port)`.
- Replaced `print("Metrics server stopped")` with `logger.info("Metrics server stopped")`.

---

### 2. `pypost/main.py` — Add logging setup and application lifecycle events

**Problem:** The application entry point had no logging configuration, so log records from all
modules were silently discarded by the root logger's default `WARNING` level.

**Fix:**
- Added `import logging`.
- Added `logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s ...")`.
- Added `logger = logging.getLogger(__name__)`.
- Added `logger.info("PyPost starting up")` at the start of `main()`.
- Added `logger.info("PyPost shutting down")` before `metrics_manager.stop_server()`.

---

### 3. `pypost/core/http_client.py` — Log request failures before re-raising

**Problem:** The `except` block in `send_request` caught and immediately re-raised exceptions
with no diagnostic information logged, making network failures invisible in application logs.

**Fix:**
- Added `import logging` and `logger = logging.getLogger(__name__)`.
- Changed `except Exception as e: raise e` to log the method, URL, and exception at ERROR level
  before re-raising with a bare `raise` (preserves original traceback).

```python
except Exception as e:
    logger.error("Request failed: %s %s — %s", request_data.method, url, e)
    raise
```

---

### 4. `pypost/core/worker.py` — Log worker thread exceptions

**Problem:** `RequestWorker.run()` caught all exceptions and emitted them as a Qt signal, but
never logged them. Exceptions in the worker thread were invisible unless the UI happened to
display them.

**Fix:**
- Added `import logging` and `logger = logging.getLogger(__name__)`.
- Added `logger.error("RequestWorker failed: %s", e, exc_info=True)` before `self.error.emit()`.
  `exc_info=True` includes the full traceback in the log record.

---

### 5. `pypost/core/mcp_server.py` — Log MCP server lifecycle

**Problem:** `MCPServerManager.start_server()` and `stop_server()` emitted Qt signals but wrote
nothing to the application log, making MCP server lifecycle invisible in structured logs.

**Fix:**
- Added `import logging` and `logger = logging.getLogger(__name__)`.
- Added `logger.info("MCP server started on %s:%d", host, port)` in `start_server`.
- Added `logger.info("MCP server stopped")` in `stop_server`.

---

## What Was Not Added

| Candidate | Decision |
|-----------|----------|
| DEBUG log when `metrics=None` in constructors | Skipped — `None` is a valid test-time value by design (§6 of architecture). Logging it would generate noise in every test run. |
| Metrics counters for logging volume | Out of scope for this task. |
| Structured JSON logging | Out of scope; `basicConfig` format is sufficient for a desktop app. |

---

## Test Result

```
103 passed in 1.68s
```

No regressions. All logging calls are outside the test hot paths and do not affect test
assertions.
