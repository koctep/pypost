# PYPOST-420 — Developer Documentation

> Team Lead: team_lead
> Date: 2026-03-26
> Sprint: 167

---

## 1. What Changed and Why

`AlertManager` previously had a latent handler-accumulation bug caused by two related
defects:

1. **CPython `id()` reuse**: Python's logging manager caches named loggers for the process
   lifetime. When an `AlertManager` was garbage-collected without calling `close()`, its
   `RotatingFileHandler` remained in the cached logger. If CPython later reused the same
   memory address for a new `AlertManager`, `addHandler()` was called on an already-populated
   logger, doubling (or further multiplying) log output per `emit()` call.

2. **No resource-release path**: There was no `close()` method, leaving file descriptors and
   logger entries unreleased for the process lifetime.

This ticket adds a handler guard in `__init__`, a `close()` method, and a context-manager
interface — the minimal set of changes needed to make `AlertManager` safe for use in code
that creates more than one instance per process.

---

## 2. API Changes

All changes are **additive**. The existing constructor signature is unchanged.

### `AlertManager.close() -> None`

Releases the `RotatingFileHandler` created by this instance: closes the underlying file
descriptor and removes the handler from the instance's logger. Safe to call multiple times.

```python
mgr = AlertManager(log_path=Path("/var/log/pypost/alerts.log"))
mgr.emit(payload)
mgr.close()  # handler released
```

### Context-manager support

`AlertManager` implements `__enter__` / `__exit__`, so it can be used with `with`:

```python
with AlertManager(log_path=Path("/var/log/pypost/alerts.log")) as mgr:
    mgr.emit(payload)
# handler automatically released on exit
```

`__exit__` calls `close()` regardless of whether an exception was raised inside the block.
Exceptions propagate normally (the context manager does not suppress them).

---

## 3. Handler Guard

On every `__init__`, before adding the new `RotatingFileHandler`, the constructor inspects
`self._logger.handlers`. If any handlers are already present (left over by a prior instance
whose memory address was reused by CPython), they are closed and removed. This guarantees
exactly one handler per logger at all times.

In practice this guard fires only in CPython environments under memory pressure or when many
short-lived `AlertManager` instances are created without calling `close()`. In a healthy
application (where `close()` or a `with` block is used), the guard is a no-op.

**If you see `alert_manager_stale_handlers_evicted` in production logs**, it means an
`AlertManager` instance was discarded without being closed. Investigate the call site and
add `close()` / `with` usage.

---

## 4. Log Events

All events are emitted via the module-level logger (`pypost.core.alert_manager`).

| Event key | Level | When emitted |
|-----------|-------|--------------|
| `alert_manager_init` | DEBUG | Every successful `__init__` |
| `alert_manager_stale_handlers_evicted` | WARNING | `__init__` found leftover handlers (id reuse path) |
| `alert_emitted` | WARNING | Every `emit()` call |
| `alert_webhook_ok` | DEBUG | Webhook POST completed |
| `alert_webhook_failed` | WARNING | Webhook POST raised an exception |
| `alert_manager_close` | DEBUG | Every `close()` call |

Enable `DEBUG` on `pypost.core.alert_manager` to trace the full lifecycle of each instance.
In production, only WARNING-level events are visible under typical log configuration.

---

## 5. Correct Usage Patterns

### Short-lived instance (preferred)

```python
with AlertManager(log_path=alerts_path) as mgr:
    mgr.emit(payload)
```

### Long-lived instance (e.g. application service class)

```python
class MyService:
    def __init__(self):
        self._alert_mgr = AlertManager()

    def shutdown(self):
        self._alert_mgr.close()
```

### Anti-pattern to avoid

```python
# BAD — handler accumulates if the process creates many AlertManagers without close()
for item in large_collection:
    mgr = AlertManager()
    mgr.emit(build_payload(item))
    # missing: mgr.close()
```

Always pair each `AlertManager()` with a `close()` call or use the `with` statement.

---

## 6. File Locations

| File | Role |
|------|------|
| `pypost/core/alert_manager.py` | `AlertManager` and `AlertPayload` implementation |
| `tests/test_alert_manager.py` | Unit and regression tests |

---

## 7. Testing

Run the full test suite:

```bash
pytest tests/test_alert_manager.py -v
```

Expected output: **17 passed**.

The `TestAlertManagerAccumulation` class contains two regression tests specific to this fix:

- `test_no_accumulation_via_close` — verifies the normal close path.
- `test_no_accumulation_via_gc_id_reuse` — verifies the handler guard by forcing CPython
  address reuse via `del` + `gc.collect()`.

---

## 8. Related Tickets

| Ticket | Description | Dependency |
|--------|-------------|------------|
| PYPOST-418 | Logger injection for `AlertManager` | Depends on this fix |
| PYPOST-419 | Webhook retry policy | Depends on PYPOST-418 |
| PYPOST-402 | Parent tech-debt epic | This ticket is a child |
