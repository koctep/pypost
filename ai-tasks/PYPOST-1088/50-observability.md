# PYPOST-1088: Observability Implementation

## Overview

PYPOST-1088 addresses two distinct test-reliability defects — cross-platform `errno` hardcoding
and encryption-migration test-order flakiness — by changes that are entirely in **test
infrastructure and thin production helpers**. No new production runtime features were introduced,
so the observability focus is on:

1. How error-code translations surface in production error messages across operating systems.
2. How key-cache state transitions can be traced in logs.
3. How test-isolation fixtures and `os.utime` backdating are visible in CI output.

---

## Logging Implementation

### Added / Pre-existing Logs in Touched Production Code

All DEBUG-level log calls listed below were **pre-existing** in the production modules. The
PYPOST-1088 changes confirmed they are the correct observability hooks and did not remove any of
them.

#### `pypost/core/server_bind.py` — `format_bind_error`

No log calls inside this function (it is a pure formatter), but the **calling sites** in
`metrics_server.py` and `mcp_server.py` log at WARNING before emitting the formatted message to
the UI.

- **WARNING** — `pypost/core/qt/metrics.py` — logs the raw `OSError` before calling
  `format_bind_error`; operator sees: OS errno code + human-readable port-busy message.
- **WARNING** — `pypost/core/qt/mcp_server.py` — identical pattern for the MCP server path.

#### `pypost/core/key_sources/env.py` — `EnvKeySource`

- **DEBUG** `env_keys_file_load_failed path=<path> reason=<exc>` — file could not be read/parsed.
- **DEBUG** `env_keys_file_invalid path=<path>` — file lacks required fields.
- **DEBUG** `env_keys_file_active_key_invalid path=<path>` — active key ID absent from valid set.
- **DEBUG** `env_keys_file_missing path=<path>` — path does not exist on disk.
- **DEBUG** `env_encryption_key_resolved source=keys_file key_id=<id>` — key resolved from JSON
  registry file.
- **DEBUG** `env_encryption_key_resolved source=env_var key_id=<id>` — key resolved from env var.
- **DEBUG** `env_encryption_key_match source=keys_file key_id=<id>` — lookup by ID matched in
  registry file.
- **DEBUG** `env_encryption_key_match source=env_var key_id=<id>` — lookup by ID matched via env.

#### `pypost/core/key_sources/secret_store.py` — `SecretStoreKeySource` / backends

- **DEBUG** `secret_store_spec_load_failed path=<path> reason=<exc>`
- **DEBUG** `secret_store_spec_missing path=<path>`
- **DEBUG** `secret_backend_file_missing path=<path>`
- **DEBUG** `secret_backend_file_load_failed path=<path> reason=<exc>`
- **DEBUG** `vault_backend_token_missing token_env=<var>`
- **DEBUG** `vault_backend_fetch_failed url=<url> reason=<exc>`
- **DEBUG** `secret_backend_type_unsupported type=<type>`
- **WARNING** `secret_backend_chain_fallback failed_type=<t> next_type=<t>` — fallback to next
  backend.
- **INFO** `secret_backend_chain_resolved_via_fallback backend_type=<t> skipped_types=<list>` —
  resolved via non-primary backend.
- **DEBUG** `secret_store_encryption_key_resolved key_id=<id>`
- **DEBUG** `secret_store_encryption_key_match key_id=<id>`

### Log Structure

| Property | Value |
|---|---|
| Structured logs | Yes — key=value pairs within message strings |
| Includes context | Yes — path, key_id, reason, url, type fields present |
| Log levels used | DEBUG, INFO, WARNING |
| Logger names | `pypost.core.key_sources.env`, `pypost.core.key_sources.secret_store` |

To enable DEBUG output in development or CI:

```bash
pytest --log-cli-level=DEBUG tests/test_encryption_migration.py
```

---

## Observability Analysis by Change Area

### 1. Cross-platform `errno.EADDRINUSE` — macOS 48 vs Linux 98

**Where it surfaces:**

`pypost/core/server_bind.py` `format_bind_error()` receives the raw `OSError` from uvicorn's
asyncio event loop. The `exc.errno` value is platform-specific:

| OS | `errno.EADDRINUSE` value |
|---|---|
| macOS | 48 |
| Linux | 98 |
| Windows | 10048 (WSAEADDRINUSE) |

`format_bind_error` guards against all of these:

```python
exc.errno in (errno.EADDRINUSE, errno.EADDRNOTAVAIL, 48, 49, 10048, 10013)
    or "address already in use" in str(exc).lower()
```

**Observability:**

- The **numeric errno** appears in the raw `OSError.__str__()` before formatting — visible if the
  caller logs `str(exc)` at WARNING level.
- The **formatted message** surfaced to the operator is OS-agnostic: `"port is busy or
  unavailable"`.
- In the test suite, `errno.EADDRINUSE` is used symbolically (not as a literal integer), so the
  assertion `"busy" in message.lower()` passes on all platforms.

**How to diagnose in production logs:**

```
# Linux uvicorn thread (raw OSError before format_bind_error):
OSError: [Errno 98] Address already in use
# macOS:
OSError: [Errno 48] Address already in use
# Formatted user message (identical on both):
Cannot start MCP server on 127.0.0.1:1080: port is busy or unavailable. …
```

### 2. `MtimeFileCache.clear()` — Cache Invalidation State Transitions

**Cache state machine:**

| State | `_path` | `_mtime_ns` | `_value` | Trigger |
|---|---|---|---|---|
| Empty | `None` | `None` | `None` | After `clear()` / `_clear()` |
| Populated | `"<path>"` | `<int ns>` | `<T>` | After successful `get()` |
| Stale-evicted | `None` | `None` | `None` | `get()` finds mtime changed or file gone |

**Observable signals:**

`clear()` resets all three private attributes to `None` silently. State changes are **inferred**
from the next `get()` call's DEBUG log:

- A cache miss followed by `env_encryption_key_resolved` indicates the cache was cleared and the
  file was re-read.
- Absence of `env_encryption_key_resolved` after a `clear()` indicates the file was missing or
  invalid post-clear.

### 3. `_reset_key_source_caches` — CI / Log Traceability

**Location:** `tests/conftest.py` (autouse, function-scope fixture).

```python
@pytest.fixture(autouse=True)
def _reset_key_source_caches():
    """Reset key source in-process caches between tests to avoid state leakage."""
    from pypost.core.key_sources.env import clear_registry_cache
    from pypost.core.key_sources.secret_store import clear_spec_cache

    clear_registry_cache()
    clear_spec_cache()
    yield
    clear_registry_cache()
    clear_spec_cache()
```

The fixture runs **before and after every test** (autouse). Its effect is **indirectly
observable**:

- **Before yield**: `clear_registry_cache()` resets `_registry_cache._path = None`. If the very
  next test calls `_load_registry()`, it performs a fresh file read — the DEBUG log
  `env_encryption_key_resolved` appears with no preceding cache-hit.
- **After yield**: same reset; subsequent test's fixture setup starts from a clean slate.

**Potential enhancement (not in scope for this task):**

Adding a `DEBUG` log inside `clear_registry_cache()` and `clear_spec_cache()` would make fixture
lifecycle explicit in CI logs. Deferred as tech-debt improvement.

### 4. `os.utime` Mtime Backdating — Observability in Tests

**Location:** `tests/test_encryption_migration.py`, line 619.

```python
before_mtime = storage.environments_file.stat().st_mtime
os.utime(storage.environments_file, (before_mtime - 10, before_mtime - 10))
before_mtime = storage.environments_file.stat().st_mtime  # now 10s earlier

report = EncryptionMigrationService(storage).bulk_re_encrypt(settings, dry_run=False, backup=False)

assert report.success is True
assert storage.environments_file.stat().st_mtime > before_mtime  # file was rewritten
```

**Purpose:** Sets the file's mtime 10 seconds into the past so that `MtimeFileCache.get()` detects
a genuine mtime change when `bulk_re_encrypt` rewrites the file, preventing a stale-cache hit that
would return the pre-rotation key registry.

**Observable signals:**

`os.utime` itself produces no logs; its effect is validated via `stat().st_mtime` assertions in
the test. With `--log-cli-level=DEBUG` the observable sequence is:

1. Registry loaded → `env_encryption_key_resolved source=keys_file key_id=<old-id>`
2. `os.utime` called (silent — mtime backdated 10s)
3. `bulk_re_encrypt` writes new file (mtime advances past the backdated timestamp)
4. Next `_load_registry()` call detects `mtime_ns ≠ cached_mtime_ns` → re-reads file →
   `env_encryption_key_resolved source=keys_file key_id=<new-id>`

---

## Metrics Implementation

Not applicable. PYPOST-1088 is a test-reliability task; no new runtime performance or business
metrics were introduced. Existing application metrics are unaffected.

---

## Monitoring Integration

- [ ] Prometheus metrics — N/A
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A
- [ ] Log aggregation (ELK, Loki, etc.) — N/A

---

## Validation Results

- [x] Logs are correctly formatted (key=value structured DEBUG messages in `env.py` /
  `secret_store.py`)
- [x] No large data structures are logged (only `path`, `key_id`, `reason` scalars)
- [x] Logging works in error scenarios (`env_keys_file_load_failed`, `vault_backend_fetch_failed`)
- [x] `errno.EADDRINUSE` maps correctly across platforms — symbolic constant used in all tests
- [x] Cache-invalidation path observable via DEBUG log sequence after `clear()` + `get()`
- [x] `os.utime` effect validated by `st_mtime > before_mtime` assertion in the test
- [ ] Metrics collected correctly — N/A (no metrics changes in scope)
- [ ] Metrics available for monitoring — N/A

---

## Notes

- No new `logging` calls were added in PYPOST-1088; the pre-existing DEBUG instrumentation in
  `env.py` and `secret_store.py` is sufficient to trace all cache state transitions.
- The `format_bind_error` helper is a pure formatter with no side effects; its observability is
  entirely through the caller's WARNING log and the UI error message.
- Adding a `DEBUG` log inside `MtimeFileCache.clear()` would improve observability of the fixture
  lifecycle but is deferred as a future improvement (see `60-tech-debt.md`).
