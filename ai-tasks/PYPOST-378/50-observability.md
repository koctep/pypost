# PYPOST-378: Observability — TemplateService DI Chain Tracing

## Scope

This document describes the logging additions made to make the `TemplateService` dependency-
injection chain traceable at runtime. The implementation introduced in PYPOST-378 threads a single
`TemplateService` instance from `main.py` down to every consumer. Without log coverage at each
hop, a misconfigured chain (e.g. a `None` value silently propagated, or a stray second instance
created) would be invisible until a `NoneType` error surfaced at runtime.

---

## Existing Observability (pre-378)

The leaf-level classes already logged injection receipt at DEBUG:

| Class | Log message |
|-------|-------------|
| `HTTPClient.__init__` | `"HTTPClient: using injected TemplateService id=%d"` |
| `RequestService.__init__` | `"RequestService: using injected TemplateService id=%d"` |
| `MCPServerImpl.__init__` | `"MCPServerImpl: using injected TemplateService id=%d"` |

These three messages share the same `id()` value when the DI chain is correct, confirming a
single instance is in use.

---

## Additions in This Step

### 1. `pypost/main.py` — INFO on creation

```python
logger.info("template_service_created id=%d", id(template_service))
```

**Why:** The composition root is the authoritative source of the singleton. Logging the `id()`
at INFO level lets operators and developers quickly confirm which instance was created and
cross-reference it against the DEBUG logs from downstream consumers.

---

### 2. `pypost/core/mcp_server.py` — DEBUG on propagation

```python
if template_service is not None:
    logger.debug("MCPServerManager: propagating TemplateService id=%d", id(template_service))
```

**Why:** `MCPServerManager` is the first intermediate node in the MCP branch of the chain. A
log here confirms the instance reaches `MCPServerImpl` with the same id that was logged at the
root.

---

### 3. `pypost/core/worker.py` — DEBUG on propagation

```python
if template_service is not None:
    logger.debug("RequestWorker: propagating TemplateService id=%d", id(template_service))
```

**Why:** `RequestWorker` is the first intermediate node in the UI/request branch. One worker is
created per user-triggered request. Logging the id here confirms that each worker carries the
shared singleton into its `RequestService` and `HTTPClient`.

---

## Full Traceable Chain

With all log statements in place, a single request produces the following log trail (DEBUG level):

```
INFO  pypost.main  template_service_created id=140234567890
DEBUG pypost.core.mcp_server     MCPServerManager: propagating TemplateService id=140234567890
DEBUG pypost.core.mcp_server_impl MCPServerImpl: using injected TemplateService id=140234567890
DEBUG pypost.core.request_service RequestService: using injected TemplateService id=140234567890
DEBUG pypost.core.http_client     HTTPClient: using injected TemplateService id=140234567890

DEBUG pypost.core.worker          RequestWorker: propagating TemplateService id=140234567890
DEBUG pypost.core.request_service RequestService: using injected TemplateService id=140234567890
DEBUG pypost.core.http_client     HTTPClient: using injected TemplateService id=140234567890
```

All `id` values being identical confirms a single instance is flowing through both branches.

---

## No New Metrics

`TemplateService` is a stateless Jinja2 wrapper with no I/O and negligible cost. Adding
Prometheus counters or histograms for template rendering is out of scope for this ticket.
Metrics for HTTP and MCP request flows are already covered by `MetricsManager` in the leaf
classes.

---

## Files Modified

| File | Change |
|------|--------|
| `pypost/main.py` | Added `INFO` log after `TemplateService()` instantiation |
| `pypost/core/mcp_server.py` | Added `DEBUG` log in `MCPServerManager.__init__` |
| `pypost/core/worker.py` | Added `DEBUG` log in `RequestWorker.__init__` |
