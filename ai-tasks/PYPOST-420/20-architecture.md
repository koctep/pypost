# PYPOST-420 — Architecture: Logger Accumulation in AlertManager

> Senior Engineer: senior_engineer
> Date: 2026-03-26
> Sprint: 167

---

## 1. Summary

Two targeted changes are required, both confined to two files:

| File | Change |
|------|--------|
| `pypost/core/alert_manager.py` | Handler guard, `close()`, `__enter__` / `__exit__` |
| `tests/test_alert_manager.py` | New test class `TestAlertManagerAccumulation` |

No new dependencies. No public API surface changes.

---

## 2. Root-Cause Recap

`logging.Manager` caches all named loggers for the process lifetime. The current logger name
`f"pypost.alerts.{id(self)}"` is vulnerable to CPython address reuse: after GC collects an
`AlertManager` instance, its logger (and its open `RotatingFileHandler`) remain alive in the
cache. A new `AlertManager` constructed at the same memory address retrieves the same cached
logger and calls `addHandler()` a second time, yielding duplicate log lines per `emit()` call.

Secondary problem: no `close()` means `RotatingFileHandler` objects (and their file
descriptors) are never released.

---

## 3. Design

### 3.1 Handler Guard in `__init__`

Before calling `addHandler()`, iterate over any handlers already present on the logger and
close + remove each one. Stale handlers arrive only via CPython `id()` reuse; purging them
before adding the fresh handler is the correct remediation.

```
__init__:
  resolved = ...
  handler  = RotatingFileHandler(resolved, ...)
  self._logger = logging.getLogger(f"pypost.alerts.{id(self)}")
  self._logger.propagate = False
  self._logger.setLevel(logging.INFO)

  # --- Guard: remove stale handlers left by a GC'd instance at this address ---
  for stale in list(self._logger.handlers):   # snapshot; mutate safely
      try:
          stale.close()
      except Exception:
          pass
      self._logger.removeHandler(stale)
  # --- End guard ---

  self._logger.addHandler(handler)
  self._handler = handler               # owned reference for close()
```

The check is performed (and stale handlers cleared) **before** `addHandler()` is called,
satisfying FR-1. After the loop the logger is guaranteed to have zero handlers, so exactly one
is added.

`self._handler` stores the handler created by **this** instance. It is the only handle
`close()` will act on.

### 3.2 `close()` Method

```python
def close(self) -> None:
    try:
        self._handler.close()
    except Exception:
        pass
    try:
        self._logger.removeHandler(self._handler)
    except Exception:
        pass
```

- Each `try/except` is independent so a failure in one step does not prevent the other.
- Both operations are idempotent in Python's logging library: closing an already-closed
  handler is safe; `removeHandler` on a handler not in the list is a no-op.
- No exception escapes (NFR-5).

### 3.3 Context-Manager Interface

```python
def __enter__(self) -> "AlertManager":
    return self

def __exit__(self, *_: object) -> None:
    self.close()
```

`__exit__` accepts but ignores all exception-info arguments, allowing exceptions to propagate
normally from the `with` block while still guaranteeing `close()` is called.

### 3.4 `emit()` — No Change

`emit()` is unchanged. All four behaviours (file write, module-level WARNING, webhook
dispatch, exception suppression) are preserved exactly (FR-4, G3).

---

## 4. Test Design

### 4.1 `TestAlertManagerAccumulation`

Two test methods are added to `tests/test_alert_manager.py`.

#### Method 1 — Normal close path (primary regression)

```
N = 5
for i in range(N):
    create AlertManager → emit → close
create AlertManager → emit → close
assert line_count == N + 1
```

Verifies that `close()` properly releases handlers so the next instance starts clean.

#### Method 2 — Handler guard path (id() reuse scenario)

```
import gc
N = 5
for i in range(N):
    create AlertManager → emit → del → gc.collect()
create AlertManager → emit → close
assert line_count == N + 1
```

`del` + `gc.collect()` makes CPython eligible to reuse the memory address on the next
allocation. The guard in `__init__` must detect and evict any stale handler before adding
the fresh one. If the guard is absent, accumulated handlers cause duplicate writes and
`line_count > N + 1`.

Both methods use the same `self.log_path` (single file) so line counts are deterministic.

### 4.2 Existing Tests

All tests in `TestAlertManagerLogFile` and `TestAlertManagerWebhook` pass unchanged.
`test_emit_multiple_entries` already creates one manager and emits three payloads; it remains
a valid single-instance test. The new class is additive only.

---

## 5. Invariants & Contracts

| Invariant | How enforced |
|-----------|--------------|
| Exactly one handler per logger at all times | Guard loop in `__init__` clears stale handlers before `addHandler()` |
| Handler released on discard | `close()` removes and closes `self._handler` |
| `close()` is idempotent | Both operations are safe when repeated; exceptions swallowed |
| `emit()` unchanged | No modifications to that method |
| No new public API incompatibility | Signature unchanged; `close()`, `__enter__`, `__exit__` are additive |

---

## 6. Sequence Diagram — id() Reuse Path

```
Iteration 1:
  AlertManager(A)   id=0xABCD  → logger["pypost.alerts.0xABCD"].handlers = [H1]
  A.emit(p)         → H1 writes 1 line
  del A             → CPython GC; logger cache still holds logger + H1

Iteration 2:
  AlertManager(B)   id=0xABCD  (reused!)
    → getLogger("pypost.alerts.0xABCD") returns cached logger with [H1]
    → Guard: close(H1), removeHandler(H1) → handlers = []
    → addHandler(H2)              → handlers = [H2]
  B.emit(p)         → H2 writes 1 line  ✓  (not 2)
  B.close()         → close(H2), removeHandler(H2) → handlers = []
```

Without the guard, step "addHandler(H2)" would append to `[H1]`, yielding `[H1, H2]` and
two writes per `emit()`.

---

## 7. Affected Files (exact list)

```
pypost/core/alert_manager.py     — modified (guard + close + ctx-manager)
tests/test_alert_manager.py      — modified (new test class, additive only)
```

No other files are touched.
