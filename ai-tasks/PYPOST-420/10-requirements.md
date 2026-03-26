# PYPOST-420 — Requirements: Logger Accumulation in AlertManager

> Analyst: analyst
> Date: 2026-03-26
> Sprint: 167
> Type: Tech Debt (child of PYPOST-402)

---

## 1. Background

`AlertManager` (`pypost/core/alert_manager.py`) is responsible for emitting structured
alerts to a rotating log file and optionally to an HTTP webhook. Each `AlertManager`
instance creates a named Python logger and attaches a `RotatingFileHandler` to it during
`__init__`.

The original bug (as described in the Jira ticket PM comment) was that
`logging.getLogger().addHandler()` was called on the **root logger** on every instantiation,
causing handler accumulation. The current code partially mitigated this by using a unique
per-instance logger name (`f"pypost.alerts.{id(self)}"`). However, the underlying
accumulation risk remains due to two related defects described below.

---

## 2. Problem Analysis

### 2.1 CPython `id()` Reuse — Latent Accumulation Bug

Python's `id()` returns the memory address of the live object. CPython reuses memory
addresses after garbage collection. Python's `logging.Manager` keeps a persistent
in-process cache of all named loggers (a dict keyed by logger name). When an
`AlertManager` instance is garbage-collected, its logger (`pypost.alerts.<id>`) remains
in the cache with its `RotatingFileHandler` still attached.

When a new `AlertManager` is subsequently created and CPython reuses the same memory
address, `logging.getLogger(f"pypost.alerts.{id(self)}")` returns the **same cached
logger object**, which already has a handler. `addHandler()` is called again, creating a
duplicate handler. From that point on every `emit()` call produces two (or more) log
lines from the same logger — the exact accumulation symptom described in the ticket.

**Reproduction scenario**: create and discard several `AlertManager` instances; with
CPython's bump-pointer allocator the id collision can occur within tens of iterations in
a tight loop.

### 2.2 Handler and File-Descriptor Leak

There is no `close()`, `__del__`, or context-manager interface on `AlertManager`. Each
discarded instance leaves behind:

- A `RotatingFileHandler` in the logger's handler list (open file descriptor).
- A stale logger entry in the logging module's global manager cache.

Over time, in long-running processes that create many short-lived `AlertManager` instances,
this exhausts available file descriptors and inflates memory.

### 2.3 Missing Test Coverage for the Accumulation Scenario

The existing test suite (`tests/test_alert_manager.py`) does not exercise multiple
sequential instantiations to verify that no duplicate log lines are produced. There is no
regression guard for the `id()` reuse scenario.

---

## 3. Goals

| # | Goal |
|---|------|
| G1 | Each `AlertManager` instance attaches **exactly one** handler regardless of how many instances are created or discarded in the process lifetime. |
| G2 | Handlers and file descriptors are properly released when an instance is no longer needed. |
| G3 | All existing `AlertManager` behaviour (log-file write, rotating policy, webhook dispatch, propagation=False, level=INFO) is preserved unchanged. |
| G4 | A regression test demonstrates that creating multiple sequential `AlertManager` instances targeting the same log file produces no duplicate log lines. |

---

## 4. Non-Goals

- Changing the rotating-file policy, file location logic, or webhook behaviour.
- Converting `AlertManager` to a singleton or global registry.
- Altering `AlertPayload` in any way.
- Addressing PYPOST-418 (dependency injection) or PYPOST-419 (retry policy) — those are
  separate tickets in the same sprint.

---

## 5. Functional Requirements

### FR-1 — Handler Guard on `__init__`

`AlertManager.__init__` MUST NOT add a new `RotatingFileHandler` to its internal logger
if one is already attached. This guards against the `id()` reuse path. The check MUST be
performed before calling `addHandler()`.

### FR-2 — `close()` Method

`AlertManager` MUST expose a `close()` method that:
1. Calls `handler.close()` on each handler attached by this instance.
2. Calls `self._logger.removeHandler(handler)` to deregister it.

The method MUST be idempotent (safe to call multiple times).

### FR-3 — Context-Manager Support

`AlertManager` MUST implement `__enter__` / `__exit__` so it can be used as a context
manager. `__exit__` MUST call `self.close()`.

### FR-4 — No Behaviour Change for `emit()`

`emit()` MUST continue to:
- Write one JSON line per call to the rotating file logger.
- Log one structured `WARNING` via the module-level `logger`.
- Dispatch to the webhook when `_webhook_url` is set.
- Suppress all exceptions from `_send_webhook`.

### FR-5 — Regression Test: No Duplicate Lines on Re-instantiation

A new test MUST create at least **N=5** sequential `AlertManager` instances targeting the
same log file (each emitting one payload and then being discarded). After all instances
have been discarded and a final instance emits one payload, the log file MUST contain
**exactly N+1 lines** (one per `emit()` call, no duplicates).

The test MUST force CPython `id()` reuse by holding the same memory slot (e.g., by
constructing and immediately dereferencing instances in a loop without holding extra
references).

### FR-6 — Existing Tests Must Continue to Pass

All tests in `tests/test_alert_manager.py` MUST pass without modification. No test may be
removed or weakened.

---

## 6. Non-Functional Requirements

| # | Requirement |
|---|-------------|
| NFR-1 | The fix must not introduce any new public API incompatible with the existing `AlertManager(log_path, webhook_url, webhook_auth_header)` signature. |
| NFR-2 | Maximum line length: 100 characters (project standard). |
| NFR-3 | Encoding: UTF-8. Line endings: LF. |
| NFR-4 | No new third-party dependencies. |
| NFR-5 | `close()` MUST NOT raise exceptions; failures MUST be silently swallowed or logged at DEBUG level. |

---

## 7. Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC-1 | Creating 100 `AlertManager` instances sequentially against the same log file and emitting one payload each results in exactly 100 log lines (no duplicates). |
| AC-2 | After calling `close()` (or exiting a `with` block), the underlying `RotatingFileHandler` is removed from the logger's handler list. |
| AC-3 | Calling `close()` twice does not raise any exception. |
| AC-4 | All pre-existing tests in `tests/test_alert_manager.py` pass unchanged. |
| AC-5 | The new regression test (FR-5) passes. |
| AC-6 | No new `import` statement introduces a third-party dependency. |

---

## 8. Affected Files

| File | Change |
|------|--------|
| `pypost/core/alert_manager.py` | Add handler guard, `close()`, `__enter__`/`__exit__` |
| `tests/test_alert_manager.py` | Add regression test class for accumulation scenario |

---

## 9. Dependencies & Execution Order

This ticket is **first** in sprint 167's execution order:

```
PYPOST-420 (this) → PYPOST-418 (logger injection) → PYPOST-419 (retry policy)
```

There are no upstream blockers. PYPOST-418 depends on this fix being in place.
