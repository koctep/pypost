# PYPOST-403 Observability — [HP] Fix failing tests in CI

**Author**: senior_engineer
**Date**: 2026-03-25
**Status**: Complete

---

## 1. Overview

This document describes the logging enhancements added during the observability phase for
PYPOST-403. Both production files touched in Phase 5 (implementation) received targeted
additions: structured debug/warning log lines and save-timing instrumentation. No metrics
framework changes were required; the existing `MetricsManager` integration is unchanged.

---

## 2. `pypost/core/history_manager.py`

### 2.1 Added `import time`

`time.monotonic()` is now used to measure async save duration. This import was not
previously present.

### 2.2 Cap-enforcement warning (`append`)

**Before**: entries were silently dropped when the 500-entry cap was exceeded.

**After**: a `WARNING`-level log line is emitted whenever `append` trims the list:

```
history_cap_enforced max=500 oldest_entry_dropped=True
```

**Why it matters**: silent data loss is hard to diagnose in production. Operators can
monitor for this log line to detect abnormal write volumes.

### 2.3 Save timing in `_save_async._run()`

`time.monotonic()` is captured at the start of each write attempt. Both success and
failure log lines now include `elapsed_ms`:

```
history_manager_saved count=42 elapsed_ms=3.7
history_manager_save_failed elapsed_ms=1.2 error=<exc>
```

**Why it matters**: slow I/O (network drives, slow flash) is now observable in logs
without adding a metrics dependency to this module.

### 2.4 `flush()` lifecycle logging

`flush()` now emits debug lines when it begins waiting and when it completes:

```
history_manager_flush waiting thread_id=139...
history_manager_flush complete
```

**Why it matters**: if a test or teardown hangs inside `flush()`, the thread id in the
first log line can be correlated with a thread dump to identify the blocking save.

---

## 3. `pypost/core/http_client.py`

### 3.1 Default `TemplateService` construction log (`__init__`)

**Before**: only the *injected* path was logged; the new default-construction path
(introduced in PYPOST-403 Phase 5) was silent.

**After**: an `else` branch emits a debug line for the default path:

```
HTTPClient: using default TemplateService
```

**Why it matters**: makes it easy to confirm in logs whether the caller provided an
explicit `TemplateService` or relied on the default — useful when diagnosing
template-rendering issues.

### 3.2 SSE endpoint detection log (`send_request`)

When `is_sse_endpoint` evaluates to `True`, a debug line is now emitted before the
request is dispatched:

```
sse_probe_detected method=GET url=http://host/sse
```

**Why it matters**: SSE probes use a different timeout tuple and add an `Accept` header.
This log confirms the detection fired for a given request, aiding debugging of the
auto-detect heuristic.

### 3.3 Successful response log (`send_request`)

Non-SSE requests previously had no success log — only error paths were logged. A debug
line is now emitted after the response body is fully read:

```
request_complete method=POST status=201 elapsed_ms=142 size=512
```

**Why it matters**: closes the observability gap between `track_request_sent` (already
in place) and `track_response_received` (already in place). The log line gives
developers a plain-text view of the full request lifecycle even without a metrics backend
configured.

---

## 4. Log-level Summary

| Logger | Level | Event |
|--------|-------|-------|
| `pypost.core.history_manager` | `WARNING` | Cap enforced — entry dropped |
| `pypost.core.history_manager` | `DEBUG` | Save completed with timing |
| `pypost.core.history_manager` | `DEBUG` | Save failed with timing |
| `pypost.core.history_manager` | `DEBUG` | `flush()` waiting / complete |
| `pypost.core.http_client` | `DEBUG` | Default `TemplateService` constructed |
| `pypost.core.http_client` | `DEBUG` | SSE endpoint detected |
| `pypost.core.http_client` | `DEBUG` | Successful non-SSE response |

---

## 5. Test Impact

All 24 tests in the three affected test files continue to pass after these additions.
The new log lines are emitted at `DEBUG` level (except the cap warning), so no test
assertions needed updating.

```
24 passed in 1.33s
```
