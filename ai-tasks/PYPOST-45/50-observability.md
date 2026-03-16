# PYPOST-45 Observability: `template_service` Constructor Injection

## Summary

This document records the logging additions made after the PYPOST-45 refactor, which replaced the
`template_service` module-level singleton with constructor injection across `HTTPClient`,
`RequestService`, and `MCPServerImpl`.

---

## Changes Made

### 1. `pypost/core/template_service.py` — replace `print()` with structured logging

**Before:**
```python
print(f"Template rendering error: {e}")
```

**After:**
```python
logger = logging.getLogger(__name__)
# ...
logger.error("Template rendering error: %s", e)
```

**Why:** `print()` bypasses the application's logging configuration (level filters, handlers,
formatters). Using `logger.error` ensures render failures are captured by the root handler,
appear in log files, and can be suppressed in tests via `--log-level`.

---

### 2. `pypost/core/http_client.py` — debug log injection vs. default creation

**Added to `__init__`:**
```python
if template_service is not None:
    self._template_service = template_service
    logger.debug("HTTPClient: using injected TemplateService id=%d", id(template_service))
else:
    self._template_service = TemplateService()
    logger.debug("HTTPClient: created default TemplateService id=%d", id(self._template_service))
```

**Why:** When diagnosing rendering bugs, it is critical to know whether a shared or a private
`TemplateService` instance is in use. The `id()` value lets an operator verify that all three
layers (`MCPServerImpl`, `RequestService`, `HTTPClient`) hold the same instance when injection is
used.

---

### 3. `pypost/core/request_service.py` — add logger + debug log injection path

**Added at module level:**
```python
import logging
logger = logging.getLogger(__name__)
```

**Added to `__init__`:**
```python
if template_service is not None:
    self._template_service = template_service
    logger.debug("RequestService: using injected TemplateService id=%d", id(template_service))
else:
    self._template_service = TemplateService()
    logger.debug(
        "RequestService: created default TemplateService id=%d", id(self._template_service)
    )
```

**Why:** `RequestService` had no logger at all before this change. Without it, exceptions and
state transitions in this central execution path were invisible at the structured-logging level.

---

### 4. `pypost/core/mcp_server_impl.py` — add logger + debug log injection path

**Added at module level:**
```python
import logging
logger = logging.getLogger(__name__)
```

**Added to `__init__`:**
```python
if template_service is not None:
    self._template_service = template_service
    logger.debug("MCPServerImpl: using injected TemplateService id=%d", id(template_service))
else:
    self._template_service = TemplateService()
    logger.debug(
        "MCPServerImpl: created default TemplateService id=%d", id(self._template_service)
    )
```

**Why:** Same rationale as `RequestService`. `MCPServerImpl` is the root of the injection chain;
logging here closes the observability loop for the full dependency graph.

---

## Log Levels Used

| Level   | Location                          | Trigger                                      |
|---------|-----------------------------------|----------------------------------------------|
| `DEBUG` | `HTTPClient.__init__`             | Construction — injected or default instance  |
| `DEBUG` | `RequestService.__init__`         | Construction — injected or default instance  |
| `DEBUG` | `MCPServerImpl.__init__`          | Construction — injected or default instance  |
| `ERROR` | `TemplateService.render_string`   | Jinja2 render exception                      |

The `DEBUG` lines are silent under the default `WARNING` level and only appear when the operator
sets `--log-level=DEBUG` or configures a `DEBUG` handler explicitly. No noise is added to normal
operation.

---

## No New Metrics Added

The existing `MetricsManager` calls (`track_request_sent`, `track_response_received`,
`track_mcp_request_received`, `track_mcp_response_sent`) already provide sufficient counters for
the request lifecycle. The PYPOST-45 refactor is a pure structural change; no new metric
dimensions were introduced.

---

## Verification

All 19 unit tests in `tests/test_http_client.py` and `tests/test_request_service.py` pass after
these changes:

```
19 passed in 0.98s
```
