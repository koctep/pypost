# PYPOST-1112: Mirror isinstance(data, dict) guard from secret_store.py onto env.py registry loader

## Research

In `pypost/core/key_sources/`:
- `secret_store.py` (`SecretStoreKeySource._read_spec_file`):
  Guards against non-object JSON payloads with `return data if isinstance(data, dict) else None`.
- `env.py` (`EnvKeySource._read_registry_file`):
  Deserializes `data = json.load(handle)` and directly calls `data.get(...)`. If `data` is a `list`, `str`, `int`, etc., Python raises `AttributeError`.

Both loaders are structurally sibling implementations of the key registry loader pattern. Adding the `isinstance(data, dict)` guard in `env.py` restores symmetry, ensures consistent error handling, and satisfies all requirements.

## Implementation Plan

1. **Step 3 (Failing Repro):**
   - Location: `tests/test_key_sources_chain_coverage.py` (or a dedicated unit test in `tests/test_key_sources.py` / `tests/test_env_key_source.py`).
   - Test cases:
     1. Test `EnvKeySource._read_registry_file` with a JSON file containing a JSON array `["invalid"]`, number `42`, or string `"scalar"`, asserting it returns `None` and does not raise `AttributeError`.
     2. Test `SecretStoreKeySource._read_spec_file` with a non-dict JSON file asserting it returns `None`.
   - Before fix in Step 4, the `env.py` test will fail with `AttributeError`.

2. **Step 4 (Development):**
   - Add `if not isinstance(data, dict): return None` (with debug log) in `EnvKeySource._read_registry_file` in `pypost/core/key_sources/env.py`.
   - Run `make test` to verify all tests pass.

3. **Step 5-8:**
   - Step 5: Code cleanup (`ai-tasks/PYPOST-1112/40-code-cleanup.md`).
   - Step 6: Observability (`ai-tasks/PYPOST-1112/50-observability.md`).
   - Step 7: Technical debt analysis (`ai-tasks/PYPOST-1112/60-tech-debt.md`).
   - Step 8: Dev docs updates (`doc/dev/`).

## Architecture

```
+-------------------------------------------------------------+
|                      Key Source Loaders                     |
+-------------------------------------------------------------+
|                                                             |
|  pypost/core/key_sources/secret_store.py                    |
|  - _read_spec_file(path)                                    |
|      -> json.load()                                         |
|      -> isinstance(data, dict) ? data : None [PASS]         |
|                                                             |
|  pypost/core/key_sources/env.py                             |
|  - _read_registry_file(path)                                |
|      -> json.load()                                         |
|      -> isinstance(data, dict) ? continue : None [NEW GUARD]|
|      -> data.get("active_key_id") ...                       |
|                                                             |
+-------------------------------------------------------------+
```

### Module Responsibilities & Interfaces

- `pypost.core.key_sources.env.EnvKeySource`:
  - `_read_registry_file(path: Path) -> KeyRegistry | None`: Reads, parses, and validates registry JSON files from disk, returning `KeyRegistry` on success or `None` on failure/invalid data.
- `pypost.core.key_sources.secret_store.SecretStoreKeySource`:
  - `_read_spec_file(path: Path) -> dict[str, Any] | None`: Reads and parses specification JSON files from disk, returning a dict on success or `None` on invalid data.

## Q&A

| Question | Answer |
| --- | --- |
| What logging is performed on non-dict payload? | `logger.debug("env_keys_file_invalid path=%s", path)` is emitted before returning `None`. |
