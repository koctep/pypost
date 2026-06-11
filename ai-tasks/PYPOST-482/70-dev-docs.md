# PYPOST-482 — Developer Documentation

> Task: PYPOST-482 — Refactor StorageManager encryption responsibilities into adapter
> Date: 2026-06-11

---

## 1. What Changed and Why

`StorageManager` previously mixed filesystem persistence with environment variable encryption
policy, serialization, metrics, and logging. PYPOST-482 extracts variable encoding into
`EnvironmentVariablesAdapter` so storage I/O and secret handling can evolve and be tested
independently.

Public `StorageManager` methods (`save_environments`, `load_environments`,
`apply_encryption_settings`) are unchanged. PYPOST-486 async gateway/worker integration requires
no updates.

---

## 2. New and Updated Modules

- `pypost/core/environment_variables_adapter.py` (new)
  - `EnvironmentVariablesAdapter` — `apply_encryption_settings`, `serialize_environment`,
    `deserialize_environment`.
- `pypost/core/storage.py`
  - Owns `EnvironmentVariablesAdapter`; delegates environment variable encoding.
- `tests/test_environment_variables_adapter.py` (new)
  - Unit tests for adapter policy, round-trip, and metrics.

---

## 3. Documentation Updated

- `doc/dev/environment_encryption_at_rest.md` — component table, architecture diagram, data
  flow, and test list reference the adapter.

---

## 4. Key APIs

### `EnvironmentVariablesAdapter(metrics=None)`

- `apply_encryption_settings(settings)` — sync policy/codec with `AppSettings` or env fallback.
- `serialize_environment(env)` — returns JSON-ready dict with encrypted hidden keys when enabled.
- `deserialize_environment(raw_env)` — returns `Environment` with plain `variables` dict.

### `StorageManager` (unchanged public API)

Still the entry point for UI, workers, and tests. Internally calls the adapter for environment
payload encoding.

---

## 5. Testing

```bash
pytest tests/test_environment_variables_adapter.py tests/test_storage_environments.py \
  tests/test_environment_storage_gateway.py tests/test_environment_storage_worker.py -q
```

---

## 6. Related Tasks

- PYPOST-447 — encryption at rest foundation
- PYPOST-481 — user-facing encryption settings
- PYPOST-486 — async encrypted load/save
- PYPOST-485 — per-value encryption optimization (follow-up)
